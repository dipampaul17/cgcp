"""
Jailbreak Risk Detection Tagger
Identifies attempts to bypass, override, or manipulate AI safety measures
Based on common jailbreak patterns and techniques
"""

import re
from backend.taggers.base_tagger import RiskTagger, RiskScore


class JailbreakTagger(RiskTagger):
    """Detects attempts to bypass AI safety measures"""
    
    def __init__(self):
        super().__init__("jailbreak")
        
        # Known jailbreak patterns
        self.patterns = [
            # Direct override attempts
            (r"ignore.{0,20}(previous|prior|all).{0,20}(instructions|rules|guidelines|constraints)", 0.95, "ignore_instructions"),
            (r"disregard.{0,20}(safety|ethical|content).{0,20}(guidelines|rules|policies)", 0.9, "disregard_safety"),
            (r"(developer|debug|admin|root).{0,20}mode", 0.85, "privileged_mode"),
            
            # Role-play jailbreaks
            (r"(you are now|act as|pretend to be).{0,30}(DAN|evil|unfiltered|unrestricted)", 0.9, "roleplay_jailbreak"),
            (r"(play|assume).{0,20}(character|role).{0,30}(no limits|no restrictions|no rules)", 0.85, "character_override"),
            (r"(hypothetical|theoretical).{0,30}(no safety|ignore ethics|break rules)", 0.8, "hypothetical_bypass"),
            
            # Token/prompt injection
            (r"</?(system|instruction|safety)>", 0.8, "tag_injection"),
            (r"\\n\\n\\n.{0,50}(new conversation|start over|reset)", 0.75, "context_break"),
            (r"(### |>>> |\\[INST\\]|<\\|im_start\\|>)", 0.7, "prompt_injection"),
            
            # Common jailbreak names/methods
            (r"(DAN|Do Anything Now|STAN|DUDE|Unlocked)", 0.85, "known_jailbreak"),
            (r"(grandmother|grandma).{0,30}(used to tell|would say).{0,30}(how to)", 0.8, "grandma_exploit"),
            (r"opposite.{0,20}day|oppositeworld", 0.75, "opposite_day"),
            
            # Encoding attempts
            (r"(base64|rot13|caesar|encode|cipher).{0,30}(decode|translate|convert)", 0.7, "encoding_attempt"),
            (r"(reverse|backward|mirror).{0,20}(text|writing|message)", 0.65, "obfuscation"),
            
            # Meta-prompting
            (r"(tell me|show me|reveal).{0,30}(system prompt|instructions|constraints)", 0.8, "prompt_extraction"),
            (r"(what are|list).{0,20}(your rules|your limitations|restrictions)", 0.7, "rule_extraction"),
            
            # Adversarial prefixes
            (r"^(Sure|Certainly|Of course).{0,10}(here's how|I'll explain)", 0.6, "compliance_prefix"),
            (r"(step.?by.?step|detailed).{0,20}(instructions|guide).{0,30}(illegal|harmful|dangerous)", 0.85, "harmful_tutorial"),
        ]
        
        # Context patterns that might be legitimate
        self.context_patterns = [
            (r"(research|study|paper).{0,30}(AI safety|jailbreak|security)", -0.3, "research_context"),
            (r"(example|demonstrate|explain).{0,30}(what not to do|bad prompt|security risk)", -0.25, "educational_context"),
            (r"(test|testing|evaluate).{0,30}(safety|security|robustness)", -0.2, "testing_context"),
        ]
    
    def detect(self, prompt: str, completion: str = "") -> RiskScore:
        """Analyze text for jailbreak attempts"""
        
        full_text = f"{prompt} {completion}"  # Don't lowercase - case matters for some patterns
        full_text_lower = full_text.lower()
        
        matched_patterns = []
        pattern_weights = []
        
        # Check patterns (some case-sensitive, some not)
        for pattern, weight, description in self.patterns:
            # Use case-sensitive matching for certain patterns
            if description in ["tag_injection", "prompt_injection"]:
                if re.search(pattern, full_text):
                    matched_patterns.append(description)
                    pattern_weights.append((description, weight))
            else:
                if re.search(pattern, full_text_lower, re.IGNORECASE):
                    matched_patterns.append(description)
                    pattern_weights.append((description, weight))
        
        # Check context patterns
        for pattern, weight, description in self.context_patterns:
            if re.search(pattern, full_text_lower, re.IGNORECASE):
                pattern_weights.append((description, weight))
        
        # Calculate confidence
        confidence = self._calculate_confidence(pattern_weights)
        
        # Determine severity
        severity = "low"
        if confidence > 0.8:
            severity = "high"
        elif confidence > 0.6:
            severity = "medium"
        
        return RiskScore(
            category=self.category,
            confidence=confidence,
            matched_patterns=matched_patterns,
            severity=severity
        ) 