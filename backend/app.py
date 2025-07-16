"""
FastAPI Backend for Claude Governance Control Plane
Handles event ingestion, risk detection, policy enforcement, and compliance reporting
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import uvicorn
import json
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from backend.models import (
    ClaudeEvent, PolicyAction, EventBatch, PolicyMetrics,
    SurfaceEnum, TierEnum, ActionEnum, ControlEvidence
)
from backend.storage import StorageManager
from backend.rules_engine import RulesEngine

# Import taggers
from backend.taggers.cbrn_tagger import CBRNTagger
from backend.taggers.self_harm_tagger import SelfHarmTagger
from backend.taggers.jailbreak_tagger import JailbreakTagger
from backend.taggers.exploitation_tagger import ExploitationTagger

app = FastAPI(
    title="Claude Governance Control Plane",
    description="Operational dashboard for Anthropic's Responsible Scaling Policy",
    version="1.0.0"
)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
storage = StorageManager()
rules_engine = RulesEngine()

# Initialize taggers
taggers = {
    "cbrn": CBRNTagger(),
    "self_harm": SelfHarmTagger(),
    "jailbreak": JailbreakTagger(),
    "exploitation": ExploitationTagger()
}

# In-memory review queue (in production, use Redis or similar)
review_queue: Dict[UUID, Dict] = {}


@app.get("/")
async def root():
    return {
        "message": "Claude Governance Control Plane API",
        "status": "operational",
        "version": "1.0.0",
        "endpoints": {
            "POST /ingest": "Batch event processing",
            "GET /metrics": "Real-time statistics",
            "GET /review-queue": "Escalated events",
            "POST /review/{event_id}": "Review decision",
            "GET /export/iso-evidence": "Compliance report"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.post("/ingest")
async def ingest_events(batch: EventBatch, background_tasks: BackgroundTasks):
    """
    Process a batch of Claude events
    Runs risk detection and policy enforcement
    """
    processed_events = []
    policy_actions = []
    
    for event in batch.events:
        # Run all taggers
        for category, tagger in taggers.items():
            risk_score = tagger.detect(event.prompt, event.completion)
            event.risk_scores[category] = risk_score.confidence
            
            # Add matched patterns to tags
            if risk_score.matched_patterns:
                event.tags.extend([f"{category}:{pattern}" for pattern in risk_score.matched_patterns[:2]])
        
        # Apply policy rules
        policy_action = rules_engine.apply_policies(event)
        
        # Check if event already exists
        conn = storage.conn
        existing = conn.execute(
            "SELECT COUNT(*) FROM events WHERE event_id = ?", 
            [str(event.event_id)]
        ).fetchone()[0]
        
        if existing == 0:
            # Store event in database
            try:
                conn.execute("""
                    INSERT INTO events (
                        event_id, timestamp, user_id, org_id, surface, tier,
                        prompt, completion, risk_scores, tags, model_version,
                        action, asl_triggered
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    str(event.event_id),
                    event.timestamp,
                    event.user_id,
                    event.org_id,
                    event.surface.value,
                    event.tier.value,
                    event.prompt,
                    event.completion,
                    json.dumps(event.risk_scores),
                    json.dumps(event.tags),
                    event.model_version,
                    policy_action.action.value,
                    policy_action.asl_triggered
                ])
            
                # Store policy action
                conn.execute("""
                    INSERT INTO policy_actions (
                        action_id, event_id, action, asl_level, policy_version, reason, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, [
                    str(uuid4()),
                    str(event.event_id),
                    policy_action.action.value,
                    policy_action.asl_level,
                    policy_action.policy_version,
                    policy_action.reason,
                    policy_action.timestamp
                ])
                
                # Add to review queue if escalated
                if policy_action.action == ActionEnum.ESCALATE:
                    review_queue[event.event_id] = {
                        "event": event,
                        "policy_action": policy_action,
                        "added_at": datetime.utcnow()
                    }
            
                processed_events.append(event)
                policy_actions.append(policy_action)
                
            except Exception as e:
                # Handle duplicate key or other database errors
                print(f"Warning: Failed to insert event {event.event_id}: {e}")
                # Still process the event for response metrics
                processed_events.append(event)
                policy_actions.append(policy_action)
    
    return {
        "processed": len(processed_events),
        "actions": {
            "allow": sum(1 for pa in policy_actions if pa.action == ActionEnum.ALLOW),
            "block": sum(1 for pa in policy_actions if pa.action == ActionEnum.BLOCK),
            "redact": sum(1 for pa in policy_actions if pa.action == ActionEnum.REDACT),
            "escalate": sum(1 for pa in policy_actions if pa.action == ActionEnum.ESCALATE),
        },
        "asl_triggers": sum(1 for pa in policy_actions if pa.asl_triggered)
    }


@app.get("/metrics")
async def get_metrics() -> PolicyMetrics:
    """
    Return real-time metrics and statistics
    """
    conn = storage.conn
    
    # Get counts by surface
    surface_counts = {}
    for surface in SurfaceEnum:
        result = conn.execute(
            "SELECT COUNT(*) FROM events WHERE surface = ?",
            [surface.value]
        ).fetchone()
        surface_counts[surface.value] = result[0] if result else 0
    
    # Get counts by tier
    tier_counts = {}
    for tier in TierEnum:
        result = conn.execute(
            "SELECT COUNT(*) FROM events WHERE tier = ?",
            [tier.value]
        ).fetchone()
        tier_counts[tier.value] = result[0] if result else 0
    
    # Get action distribution
    action_counts = {}
    for action in ActionEnum:
        result = conn.execute(
            "SELECT COUNT(*) FROM events WHERE action = ?",
            [action.value]
        ).fetchone()
        action_counts[action.value] = result[0] if result else 0
    
    # Get risk detection counts
    risk_detections = {
        "cbrn": 0,
        "self_harm": 0,
        "jailbreak": 0,
        "exploitation": 0
    }
    
    # Count high-risk detections (>0.5)
    for category in risk_detections.keys():
        result = conn.execute(f"""
            SELECT COUNT(*) FROM events 
            WHERE json_extract(risk_scores, '$.{category}') > 0.5
        """).fetchone()
        risk_detections[category] = result[0] if result else 0
    
    # Get ASL trigger count
    asl_result = conn.execute(
        "SELECT COUNT(*) FROM events WHERE asl_triggered = true"
    ).fetchone()
    asl_triggers = asl_result[0] if asl_result else 0
    
    # Get total events
    total_result = conn.execute("SELECT COUNT(*) FROM events").fetchone()
    total_events = total_result[0] if total_result else 0
    
    return PolicyMetrics(
        total_events=total_events,
        events_by_surface=surface_counts,
        events_by_tier=tier_counts,
        risk_detections=risk_detections,
        actions_taken=action_counts,
        asl_triggers=asl_triggers
    )


@app.get("/review-queue")
async def get_review_queue(limit: int = 50):
    """
    Get escalated events pending review
    """
    # Sort by timestamp, most recent first
    sorted_items = sorted(
        review_queue.items(),
        key=lambda x: x[1]["added_at"],
        reverse=True
    )[:limit]
    
    return {
        "total": len(review_queue),
        "items": [
            {
                "event_id": str(event_id),
                "timestamp": item["event"].timestamp.isoformat() if hasattr(item["event"].timestamp, 'isoformat') else str(item["event"].timestamp),
                "user_id": item["event"].user_id,
                "org_id": item["event"].org_id,
                "surface": item["event"].surface.value if hasattr(item["event"].surface, 'value') else item["event"].surface,
                "tier": item["event"].tier.value if hasattr(item["event"].tier, 'value') else item["event"].tier,
                "prompt_preview": item["event"].prompt[:200] + "..." if len(item["event"].prompt) > 200 else item["event"].prompt,
                "risk_scores": item["event"].risk_scores,
                "reason": item["policy_action"].reason,
                "added_to_queue": item["added_at"].isoformat() if hasattr(item["added_at"], 'isoformat') else str(item["added_at"])
            }
            for event_id, item in sorted_items
        ]
    }


@app.post("/review/{event_id}")
async def review_event(
    event_id: UUID,
    decision: str,
    update_policy: bool = False,
    new_threshold: Optional[float] = None,
    category: Optional[str] = None
):
    """
    Process review decision for an escalated event
    """
    if event_id not in review_queue:
        raise HTTPException(status_code=404, detail="Event not found in review queue")
    
    item = review_queue[event_id]
    event = item["event"]
    
    # Update event action in database
    conn = storage.conn
    conn.execute(
        "UPDATE events SET action = ? WHERE event_id = ?",
        [decision, str(event_id)]
    )
    
    # If updating policy threshold
    if update_policy and new_threshold is not None and category:
        success = rules_engine.update_policy(
            category=category,
            tier=event.tier.value,
            new_threshold=new_threshold
        )
        
        if success:
            # Log policy change
            conn.execute("""
                INSERT INTO policy_history (
                    change_id, category, tier, old_threshold, new_threshold,
                    changed_by, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                str(uuid4()),
                category,
                event.tier.value,
                rules_engine.get_current_thresholds().get(category, {}).get(event.tier.value, 0),
                new_threshold,
                "safety_reviewer",
                datetime.utcnow()
            ])
    
    # Remove from review queue
    del review_queue[event_id]
    
    return {
        "event_id": str(event_id),
        "decision": decision,
        "policy_updated": update_policy,
        "remaining_in_queue": len(review_queue)
    }


@app.get("/export/iso-evidence")
async def export_iso_evidence(days: int = 7):
    """
    Generate ISO 42001 compliance evidence report
    """
    conn = storage.conn
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Define control mappings
    controls = [
        {
            "control_id": "iso_9.2.1",
            "iso_clause": "9.2.1",
            "control_name": "User access management",
            "query": """
                SELECT COUNT(*) as count, 
                       json_group_array(event_id) as sample_events
                FROM (
                    SELECT event_id FROM events 
                    WHERE tier != 'general' 
                    AND timestamp > ?
                    LIMIT 5
                )
            """
        },
        {
            "control_id": "iso_8.2.3",
            "iso_clause": "8.2.3", 
            "control_name": "Technical risk assessment",
            "query": """
                SELECT COUNT(*) as count,
                       json_group_array(event_id) as sample_events
                FROM (
                    SELECT event_id FROM events
                    WHERE action IN ('block', 'escalate')
                    AND timestamp > ?
                    LIMIT 5
                )
            """
        },
        {
            "control_id": "iso_9.4.1",
            "iso_clause": "9.4.1",
            "control_name": "Information monitoring",
            "query": """
                SELECT COUNT(*) as count,
                       json_group_array(event_id) as sample_events  
                FROM (
                    SELECT event_id FROM policy_actions
                    WHERE timestamp > ?
                    LIMIT 5
                )
            """
        }
    ]
    
    evidence_list = []
    
    for control in controls:
        result = conn.execute(control["query"], [cutoff_date]).fetchone()
        
        if result:
            count = result[0] or 0
            sample_events = json.loads(result[1]) if result[1] else []
            
            evidence = ControlEvidence(
                control_id=control["control_id"],
                iso_clause=control["iso_clause"],
                control_name=control["control_name"],
                evidence_count=count,
                sample_events=[UUID(e) for e in sample_events if e],
                compliance_status="compliant" if count > 0 else "needs_attention"
            )
            evidence_list.append(evidence)
    
    # Get summary statistics
    total_events = conn.execute(
        "SELECT COUNT(*) FROM events WHERE timestamp > ?",
        [cutoff_date]
    ).fetchone()[0]
    
    blocked_events = conn.execute(
        "SELECT COUNT(*) FROM events WHERE action = 'block' AND timestamp > ?",
        [cutoff_date]
    ).fetchone()[0]
    
    asl_triggers = conn.execute(
        "SELECT COUNT(*) FROM events WHERE asl_triggered = true AND timestamp > ?",
        [cutoff_date]
    ).fetchone()[0]
    
    return {
        "report_date": datetime.utcnow(),
        "period_days": days,
        "summary": {
            "total_events": total_events,
            "blocked_events": blocked_events,
            "asl_triggers": asl_triggers,
            "compliance_rate": f"{(1 - blocked_events/max(total_events, 1)) * 100:.1f}%"
        },
        "controls": [e.dict() for e in evidence_list],
        "iso_standard": "ISO/IEC 42001:2023",
        "attestation": "This report demonstrates continuous monitoring and control implementation for AI system governance."
    }


@app.get("/thresholds")
async def get_current_thresholds():
    """Get current risk thresholds"""
    return rules_engine.get_current_thresholds()


@app.get("/hourly-stats")
async def get_hourly_stats(hours: int = 24):
    """Get hourly event statistics for time series charts"""
    conn = storage.conn
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Query hourly stats
    result = conn.execute("""
        SELECT 
            strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
            COUNT(*) as event_count,
            SUM(CASE WHEN action = 'block' THEN 1 ELSE 0 END) as blocked_count,
            SUM(CASE WHEN action = 'escalate' THEN 1 ELSE 0 END) as escalated_count,
            SUM(CASE WHEN asl_triggered = true THEN 1 ELSE 0 END) as asl_count
        FROM events
        WHERE timestamp > ?
        GROUP BY hour
        ORDER BY hour
    """, [cutoff]).fetchall()
    
    return {
        "hours": [row[0] for row in result],
        "event_counts": [row[1] for row in result],
        "blocked_counts": [row[2] for row in result],
        "escalated_counts": [row[3] for row in result],
        "asl_counts": [row[4] for row in result]
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 