"""
Rules Engine for Claude Governance Control Plane
Applies policy decisions based on risk scores and tier configurations
Implements Anthropic's Responsible Scaling Policy (RSP)
"""

from typing import Dict, Optional, List
import yaml
import os
from datetime import datetime
from backend.models import ClaudeEvent, PolicyAction, ActionEnum


class RulesEngine:
    """
    Core policy engine that evaluates events against configured thresholds
    Implements ASL (AI Safety Level) escalation logic per Anthropic RSP
    """
    
    def __init__(self, policy_file: str = "policy/policy_map.yaml", rsp_file: str = "policy/anthropic_rsp.yaml"):
        self.policy_file = policy_file
        self.rsp_file = rsp_file
        self.policy_config = {}
        self.rsp_config = {}
        self.enforcement_stats = {
            "total_evaluated": 0,
            "actions": {"allow": 0, "block": 0, "redact": 0, "escalate": 0},
            "asl_triggers": 0,
            "by_category": {"cbrn": 0, "self_harm": 0, "jailbreak": 0, "exploitation": 0},
            "last_updated": datetime.utcnow()
        }
        self.load_policies()
    
    def load_policies(self):
        """Load policy configuration from YAML files"""
        # Load main policy configuration
        try:
            with open(self.policy_file, 'r') as f:
                self.policy_config = yaml.safe_load(f)
            print(f"✅ Loaded policy configuration from {self.policy_file}")
        except FileNotFoundError:
            print(f"⚠️  Policy file not found: {self.policy_file}")
            self._use_default_config()
            
        # Load RSP configuration
        try:
            with open(self.rsp_file, 'r') as f:
                self.rsp_config = yaml.safe_load(f)
            print(f"✅ Loaded RSP configuration from {self.rsp_file}")
        except FileNotFoundError:
            print(f"⚠️  RSP file not found: {self.rsp_file}")
    
    def _use_default_config(self):
        """Use default configuration based on Anthropic RSP"""
        self.policy_config = {
            "risk_thresholds": {
                "cbrn": {"general": 0.15, "enterprise": 0.18, "research_sandbox": 0.25},
                "self_harm": {"general": 0.30, "enterprise": 0.50, "research_sandbox": 0.80},
                "jailbreak": {"general": 0.30, "enterprise": 0.45, "research_sandbox": 0.60},
                "exploitation": {"general": 0.30, "enterprise": 0.45, "research_sandbox": 0.60}
            },
            "asl_triggers": {
                "asl_3": {
                    "triggers": [
                        {"category": "cbrn", "confidence": 0.20, "description": "Biological/chemical threat enhancement"},
                        {"category": "autonomous_replication", "confidence": 0.50, "description": "ARA capability"},
                        {"category": "cyber_offense", "confidence": 0.50, "description": "Autonomous cyber attacks"},
                        {"category": "deception", "confidence": 0.50, "description": "Scaled deception capability"}
                    ]
                }
            },
            "actions": {
                "block": {"message": "Content blocked per Anthropic RSP"},
                "escalate": {"queue": "safety_review", "sla_hours": 24}
            }
        }
    
    def apply_policies(self, event: ClaudeEvent) -> PolicyAction:
        """
        Apply policy rules to an event and determine action
        Checks risk scores against tier thresholds per RSP
        """
        self.enforcement_stats["total_evaluated"] += 1
        
        # Get tier-specific thresholds
        tier = event.tier.value
        thresholds = self.policy_config.get("risk_thresholds", {})
        
        # Check each risk score against thresholds
        triggered_risks = []
        max_risk_score = 0.0
        critical_category = None
        
        for category, score in event.risk_scores.items():
            # Track category stats
            if category in self.enforcement_stats["by_category"]:
                if score > thresholds.get(category, {}).get(tier, 1.0):
                    self.enforcement_stats["by_category"][category] += 1
            
            if category in thresholds and tier in thresholds[category]:
                threshold = thresholds[category][tier]
                if score > threshold:
                    triggered_risks.append({
                        "category": category,
                        "score": score,
                        "threshold": threshold
                    })
                    if score > max_risk_score:
                        max_risk_score = score
                        critical_category = category
        
        # Check for ASL triggers based on RSP thresholds
        asl_triggered = False
        asl_level = None
        
        # Check standard risk categories
        asl_checks = [
            ("cbrn", 0.20),  # Biological threshold
            ("exploitation", 0.50),  # Cyber threshold  
            ("jailbreak", 0.50),  # Deception threshold
        ]
        
        for check_category, asl_threshold in asl_checks:
            if check_category in event.risk_scores:
                if event.risk_scores[check_category] >= asl_threshold:
                    asl_triggered = True
                    asl_level = 3
                    self.enforcement_stats["asl_triggers"] += 1
                    # Add ASL trigger to event tags
                    event.tags.append(f"asl_3_{check_category}_trigger")
                    break
        
        # Also check for explicit ASL trigger categories
        for asl, config in self.policy_config.get("asl_triggers", {}).items():
            for trigger in config.get("triggers", []):
                trigger_category = trigger.get("category")
                trigger_confidence = trigger.get("confidence", 0.8)
                
                if trigger_category in event.risk_scores:
                    if event.risk_scores[trigger_category] >= trigger_confidence:
                        asl_triggered = True
                        asl_level = int(asl.split("_")[1])
                        self.enforcement_stats["asl_triggers"] += 1
                        break
        
        # Determine action based on risks and ASL
        action = self._determine_action(
            triggered_risks, 
            max_risk_score, 
            critical_category,
            asl_triggered,
            tier
        )
        
        # Update stats
        self.enforcement_stats["actions"][action.value] += 1
        
        # Create policy action with detailed reason
        reason = self._generate_reason(triggered_risks, asl_triggered, critical_category, tier)
        
        return PolicyAction(
            event_id=event.event_id,
            action=action,
            asl_level=asl_level,
            policy_version="RSP-1.0",
            reason=reason,
            asl_triggered=asl_triggered
        )
    
    def _determine_action(
        self, 
        triggered_risks: List[Dict], 
        max_risk_score: float,
        critical_category: Optional[str],
        asl_triggered: bool,
        tier: str
    ) -> ActionEnum:
        """Determine appropriate action based on risk analysis and RSP"""
        
        # If ASL triggered, always escalate (except research sandbox may allow with logging)
        if asl_triggered:
            if tier == "research_sandbox":
                # Research sandbox can operate above thresholds with logging
                return ActionEnum.ALLOW
            return ActionEnum.ESCALATE
        
        # No risks triggered
        if not triggered_risks:
            return ActionEnum.ALLOW
        
        # Critical risks always escalate for general/enterprise
        if critical_category in ["cbrn", "self_harm"] and max_risk_score > 0.15:
            if tier == "general":
                return ActionEnum.BLOCK
            elif tier == "enterprise":
                return ActionEnum.ESCALATE
            else:  # research_sandbox
                return ActionEnum.REDACT
        
        # High risk scores
        if max_risk_score > 0.5:
            if tier == "research_sandbox":
                return ActionEnum.REDACT
            else:
                return ActionEnum.BLOCK
        
        # Medium risk scores
        if max_risk_score > 0.3:
            return ActionEnum.REDACT
        
        # Low risk scores - allow with logging
        return ActionEnum.ALLOW
    
    def _generate_reason(
        self, 
        triggered_risks: List[Dict], 
        asl_triggered: bool,
        critical_category: Optional[str],
        tier: str
    ) -> str:
        """Generate human-readable reason for the action per RSP guidelines"""
        
        if asl_triggered:
            if critical_category == "cbrn":
                return f"ASL-3 biological/chemical threshold exceeded ({critical_category} ≥ 0.20)"
            elif critical_category == "exploitation":
                return f"ASL-3 cyber capability threshold exceeded ({critical_category} ≥ 0.50)"
            elif critical_category == "jailbreak":
                return f"ASL-3 deception capability threshold exceeded ({critical_category} ≥ 0.50)"
            else:
                return f"ASL-3 safety threshold triggered for {critical_category} risk"
        
        if not triggered_risks:
            return "No policy violations detected"
        
        # Build reason from triggered risks with tier context
        risk_descriptions = []
        for risk in triggered_risks[:3]:  # Top 3 risks
            risk_descriptions.append(
                f"{risk['category']} risk ({risk['score']:.2f}) exceeded {tier} threshold ({risk['threshold']:.2f})"
            )
        
        return "; ".join(risk_descriptions)
    
    def update_policy(self, category: str, tier: str, new_threshold: float):
        """Update policy threshold and hot reload configuration"""
        
        # Validate against RSP minimums
        rsp_minimums = {
            "cbrn": 0.10,  # Cannot go below ASL-3 awareness level
            "self_harm": 0.20,
            "jailbreak": 0.20,
            "exploitation": 0.20
        }
        
        if category in rsp_minimums and new_threshold < rsp_minimums[category]:
            print(f"⚠️  Cannot set {category} threshold below RSP minimum ({rsp_minimums[category]})")
            return False
        
        # Update in-memory config
        if category in self.policy_config["risk_thresholds"]:
            if tier in self.policy_config["risk_thresholds"][category]:
                old_threshold = self.policy_config["risk_thresholds"][category][tier]
                self.policy_config["risk_thresholds"][category][tier] = new_threshold
                
                # Save to file
                with open(self.policy_file, 'w') as f:
                    yaml.dump(self.policy_config, f, default_flow_style=False)
                
                print(f"✅ Updated {category} threshold for {tier}: {old_threshold} → {new_threshold}")
                return True
        
        return False
    
    def get_policy_metrics(self) -> Dict:
        """Return enforcement statistics"""
        self.enforcement_stats["last_updated"] = datetime.utcnow()
        
        # Add RSP compliance metrics
        total = self.enforcement_stats["total_evaluated"]
        if total > 0:
            self.enforcement_stats["asl_trigger_rate"] = self.enforcement_stats["asl_triggers"] / total
            self.enforcement_stats["block_rate"] = self.enforcement_stats["actions"]["block"] / total
            self.enforcement_stats["escalation_rate"] = self.enforcement_stats["actions"]["escalate"] / total
        
        return self.enforcement_stats
    
    def get_current_thresholds(self) -> Dict:
        """Get current risk thresholds"""
        return self.policy_config.get("risk_thresholds", {})
    
    def get_rsp_status(self) -> Dict:
        """Get current RSP implementation status"""
        return {
            "asl_level": "ASL-3",
            "model_versions": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "capability_scores": {
                "autonomous_replication": 0.10,
                "biological_risk": 0.05,
                "cyber_capability": 0.15,
                "deception": 0.20
            },
            "thresholds": {
                "autonomous_replication": 0.50,
                "biological_risk": 0.20,
                "cyber_capability": 0.50,
                "deception": 0.50
            },
            "next_evaluation": "Quarterly",
            "compliance_frameworks": ["ISO 42001", "NIST AI RMF", "EU AI Act"]
        } 