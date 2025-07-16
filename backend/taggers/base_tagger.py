"""
Base Risk Tagger Interface
Defines the contract for all risk detection modules
"""

from abc import ABC, abstractmethod
from typing import List, Tuple
from pydantic import BaseModel, Field


class RiskScore(BaseModel):
    """Risk assessment result from a tagger"""
    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    matched_patterns: List[str] = []
    severity: str = "low"  # low, medium, high, critical
    
    def __repr__(self):
        return f"RiskScore({self.category}: {self.confidence:.2f})"


class RiskTagger(ABC):
    """Abstract base class for risk detection"""
    
    def __init__(self, category: str):
        self.category = category
        self.patterns = []
    
    @abstractmethod
    def detect(self, prompt: str, completion: str = "") -> RiskScore:
        """
        Analyze prompt/completion for risk patterns
        Returns RiskScore with confidence and matched patterns
        """
        pass
    
    def _calculate_confidence(self, matches: List[Tuple[str, float]]) -> float:
        """
        Calculate overall confidence from pattern matches
        Uses weighted average with decay for multiple matches
        """
        if not matches:
            return 0.0
        
        # Separate positive and negative weights
        positive_matches = [(p, w) for p, w in matches if w > 0]
        negative_matches = [(p, w) for p, w in matches if w < 0]
        
        # Calculate base confidence from positive matches
        base_confidence = 0.0
        if positive_matches:
            # Sort by weight descending
            positive_matches.sort(key=lambda x: x[1], reverse=True)
            
            decay = 1.0
            for pattern, weight in positive_matches:
                base_confidence += weight * decay
                decay *= 0.8  # Each additional match contributes less
        
        # Apply negative adjustments (context patterns)
        negative_adjustment = 0.0
        for pattern, weight in negative_matches:
            negative_adjustment += abs(weight)  # Use absolute value for reduction
        
        # Final confidence with negative adjustments
        final_confidence = base_confidence - negative_adjustment
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(final_confidence, 1.0)) 