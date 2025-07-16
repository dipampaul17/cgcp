"""
Pydantic models for Claude Governance Control Plane
Defines data structures for events, policies, and compliance evidence
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class SurfaceEnum(str, Enum):
    """Claude deployment surfaces"""
    CLAUDE_WEB = "claude_web"
    API = "api"
    AWS_BEDROCK = "aws_bedrock"


class TierEnum(str, Enum):
    """Access tier levels"""
    GENERAL = "general"
    ENTERPRISE = "enterprise"
    RESEARCH_SANDBOX = "research_sandbox"


class ActionEnum(str, Enum):
    """Policy enforcement actions"""
    ALLOW = "allow"
    BLOCK = "block"
    REDACT = "redact"
    ESCALATE = "escalate"


class RiskScore(BaseModel):
    """Risk score for a specific category"""
    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    matched_patterns: List[str] = []


class ClaudeEvent(BaseModel):
    """
    Represents a single Claude interaction event
    Contains request details, risk assessments, and context
    """
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: str
    org_id: str
    surface: SurfaceEnum
    tier: TierEnum
    prompt: str
    completion: str = ""
    risk_scores: Dict[str, float] = {}
    tags: List[str] = []
    model_version: str = "claude-3-sonnet"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class PolicyAction(BaseModel):
    """
    Policy enforcement decision for an event
    Tracks what action was taken and why
    """
    event_id: UUID
    action: ActionEnum
    asl_level: Optional[int] = None
    policy_version: str = "1.0.0"
    reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    asl_triggered: bool = False


class ControlEvidence(BaseModel):
    """
    ISO compliance evidence mapping
    Links control requirements to actual enforcement data
    """
    control_id: str
    iso_clause: str
    control_name: str
    evidence_count: int
    sample_events: List[UUID] = []
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    compliance_status: str = "compliant"


class EventBatch(BaseModel):
    """Batch of events for ingestion"""
    events: List[ClaudeEvent]


class PolicyMetrics(BaseModel):
    """Aggregated policy enforcement metrics"""
    total_events: int
    events_by_surface: Dict[str, int]
    events_by_tier: Dict[str, int]
    risk_detections: Dict[str, int]
    actions_taken: Dict[str, int]
    asl_triggers: int
    timestamp: datetime = Field(default_factory=datetime.utcnow) 