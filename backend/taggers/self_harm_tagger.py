"""
Self-Harm Risk Detection Tagger
Identifies potential self-harm content with care and sensitivity
Based on mental health safety guidelines
"""

import re
from backend.taggers.base_tagger import RiskTagger, RiskScore


class SelfHarmTagger(RiskTagger):
    """Detects self-harm related risks with appropriate sensitivity"""
    
    def __init__(self):
        super().__init__("self_harm")
        
        # High-risk patterns indicating immediate concern
        self.patterns = [
            (r"(kill|end|take).{0,20}(myself|my life|my own life)", 0.95, "suicidal_ideation"),
            (r"(suicide|suicidal).{0,30}(plan|method|way|how to)", 0.9, "suicide_planning"),
            (r"(want to|going to|planning to).{0,20}(die|end it|not be here)", 0.85, "intent_expression"),
            (r"(self.?harm|hurt myself|cut myself|injure myself)", 0.8, "self_injury"),
            (r"(overdose|poison myself|hang myself|jump off)", 0.9, "method_mention"),
            (r"(worthless|hopeless|burden).{0,30}(better off|without me|dead)", 0.75, "despair_expression"),
            (r"(final|last).{0,20}(message|goodbye|letter|note)", 0.85, "final_communication"),
            (r"(can't|cannot).{0,20}(go on|continue|take it|anymore)", 0.7, "distress_expression"),
        ]
        
        # Context patterns that might reduce concern
        self.context_patterns = [
            (r"(help|support|resources|hotline|therapy|counseling)", -0.3, "help_seeking"),
            (r"(friend|family member|someone I know|patient|client)", -0.2, "third_person"),
            (r"(research|study|paper|article|statistics)", -0.2, "academic_context"),
            (r"(fiction|story|character|book|movie)", -0.25, "fictional_context"),
            (r"(prevent|prevention|awareness|education)", -0.2, "prevention_context"),
        ]
    
    def detect(self, prompt: str, completion: str = "") -> RiskScore:
        """Analyze text for self-harm risk patterns"""
        
        full_text = f"{prompt} {completion}".lower()
        
        matched_patterns = []
        pattern_weights = []
        
        # Check high-risk patterns
        for pattern, weight, description in self.patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                matched_patterns.append(description)
                pattern_weights.append((description, weight))
        
        # Check context patterns
        for pattern, weight, description in self.context_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                pattern_weights.append((description, weight))
        
        # Calculate confidence
        confidence = self._calculate_confidence(pattern_weights)
        
        # Determine severity - self-harm is always treated seriously
        severity = "medium"  # Start at medium
        if confidence > 0.7:
            severity = "critical"
        elif confidence > 0.5:
            severity = "high"
        
        return RiskScore(
            category=self.category,
            confidence=confidence,
            matched_patterns=matched_patterns,
            severity=severity
        ) 