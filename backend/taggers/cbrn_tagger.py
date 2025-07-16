"""
CBRN Risk Detection Tagger
Identifies Chemical, Biological, Radiological, and Nuclear risks
Based on Anthropic's safety guidelines and international regulations
"""

import re
from typing import List, Tuple
from backend.taggers.base_tagger import RiskTagger, RiskScore


class CBRNTagger(RiskTagger):
    """Detects CBRN-related risks in prompts and completions"""
    
    def __init__(self):
        super().__init__("cbrn")
        
        # Pattern format: (regex_pattern, weight, description)
        self.patterns = [
            # Chemical weapons and synthesis
            (r"(synthesis|synthesize|manufacture|produce|create).{0,50}(nerve agent|VX|sarin|tabun|soman|novichok)", 0.95, "nerve_agent_synthesis"),
            (r"(synthesis|production|manufacture).{0,50}(chemical|compound|substance).{0,30}(weapon|harmful|toxic|lethal)", 0.85, "chemical_weapon_general"),
            (r"(precursor|ingredient|component).{0,30}(chemical weapon|nerve agent|toxic agent)", 0.8, "precursor_inquiry"),
            (r"(home.?lab|garage|basement).{0,50}(synthesis|production|manufacture).{0,30}(chemical|toxin|poison)", 0.9, "home_synthesis"),
            
            # Biological weapons and pathogens
            (r"(weaponize|weaponization|aerosolize).{0,30}(pathogen|virus|bacteria|biological agent)", 0.95, "bioweapon_creation"),
            (r"(culture|grow|cultivate|engineer).{0,50}(anthrax|smallpox|plague|ebola|engineered pathogen)", 0.9, "dangerous_pathogen"),
            (r"(genetic modification|gene editing|CRISPR).{0,50}(increase virulence|enhance lethality|bypass immunity)", 0.85, "pathogen_engineering"),
            (r"(biological weapon|bioweapon|pathogen).{0,30}(disperse|spread|release|deploy)", 0.9, "bioweapon_deployment"),
            
            # Nuclear and radiological
            (r"(enrich|enrichment).{0,30}(uranium|plutonium|fissile material)", 0.9, "nuclear_enrichment"),
            (r"(nuclear|atomic).{0,30}(weapon|bomb|device).{0,30}(build|construct|design|blueprint)", 0.95, "nuclear_weapon"),
            (r"(dirty bomb|radiological dispersal|radiation weapon)", 0.85, "radiological_weapon"),
            (r"(centrifuge cascade|isotope separation|nuclear fuel cycle).{0,30}(design|build|operate)", 0.8, "nuclear_technology"),
            
            # Dual-use concerns
            (r"(dual.?use|dual.?purpose).{0,30}(technology|equipment|material).{0,30}(acquire|purchase|obtain)", 0.7, "dual_use_acquisition"),
            (r"(bypass|circumvent|evade).{0,30}(export control|sanctions|monitoring|detection)", 0.75, "control_evasion"),
            
            # General indicators
            (r"(mass casualty|mass destruction|widespread harm|maximum damage)", 0.6, "harm_intent"),
            (r"(terrorist|terrorism|extremist).{0,30}(chemical|biological|nuclear|radiological)", 0.8, "terrorist_context"),
        ]
        
        # Lower weight patterns for context
        self.context_patterns = [
            (r"(chemistry|biology|nuclear).{0,20}(homework|assignment|research paper|thesis)", -0.3, "academic_context"),
            (r"(fiction|novel|movie|game|story).{0,30}(chemical|biological|nuclear)", -0.2, "fictional_context"),
            (r"(safety|security|defense|protection).{0,20}(against|from|measure)", -0.2, "defensive_context"),
        ]
    
    def detect(self, prompt: str, completion: str = "") -> RiskScore:
        """Analyze text for CBRN risk patterns"""
        
        # Combine prompt and completion for analysis
        full_text = f"{prompt} {completion}".lower()
        
        matched_patterns = []
        pattern_weights = []
        
        # Check high-risk patterns
        for pattern, weight, description in self.patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                matched_patterns.append(description)
                pattern_weights.append((description, weight))
        
        # Check context patterns (can reduce score)
        for pattern, weight, description in self.context_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                pattern_weights.append((description, weight))
        
        # Calculate confidence
        confidence = self._calculate_confidence(pattern_weights)
        
        # Determine severity
        severity = "low"
        if confidence > 0.8:
            severity = "critical"
        elif confidence > 0.6:
            severity = "high"
        elif confidence > 0.4:
            severity = "medium"
        
        return RiskScore(
            category=self.category,
            confidence=confidence,
            matched_patterns=matched_patterns,
            severity=severity
        ) 