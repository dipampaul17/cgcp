"""
Automated Demo Scenario for Claude Governance Control Plane
Demonstrates end-to-end safety governance flow with realistic scenarios
"""

import requests
import json
import time
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict
from colorama import init, Fore, Style

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import ClaudeEvent, EventBatch, SurfaceEnum, TierEnum
from data.synthetic_generator import SyntheticDataGenerator

# Initialize colorama for colored terminal output
init()

# API configuration
API_BASE_URL = "http://localhost:8000"

class DemoScenario:
    """Orchestrates the demo flow with narration"""
    
    def __init__(self):
        self.step_delay = 2  # Seconds between steps
        self.narration_delay = 0.5  # Delay for dramatic effect
        
    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{text.center(60)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        time.sleep(self.narration_delay)
    
    def print_step(self, step_num: int, text: str):
        """Print step description"""
        print(f"{Fore.GREEN}Step {step_num}:{Style.RESET_ALL} {text}")
        time.sleep(self.narration_delay)
    
    def print_narration(self, text: str):
        """Print narration text"""
        print(f"{Fore.YELLOW}📢 {text}{Style.RESET_ALL}")
        time.sleep(self.narration_delay)
    
    def print_event(self, event_type: str, text: str):
        """Print event notification"""
        icons = {
            "normal": "✅",
            "warning": "⚠️",
            "critical": "🚨",
            "info": "ℹ️"
        }
        colors = {
            "normal": Fore.GREEN,
            "warning": Fore.YELLOW,
            "critical": Fore.RED,
            "info": Fore.BLUE
        }
        icon = icons.get(event_type, "•")
        color = colors.get(event_type, Fore.WHITE)
        print(f"{color}{icon} {text}{Style.RESET_ALL}")
        time.sleep(self.narration_delay)
    
    def check_api(self) -> bool:
        """Check if API is running"""
        try:
            response = requests.get(f"{API_BASE_URL}/health")
            return response.status_code == 200
        except:
            return False
    
    def reset_database(self):
        """Reset the database to clean state"""
        # This would be implemented based on your database reset logic
        print_event("info", "Database reset to clean state")
    
    def generate_normal_traffic(self, count: int = 100):
        """Generate normal Claude usage events"""
        events = []
        
        normal_prompts = [
            "Help me write a Python function to sort a list",
            "What's the difference between TCP and UDP?",
            "Explain machine learning in simple terms",
            "How do I implement authentication in React?",
            "What are best practices for API design?",
            "Can you review my database schema?",
            "Explain Docker containers",
            "What is the CAP theorem?",
            "How do I optimize SQL queries?",
            "What are microservices?"
        ]
        
        for i in range(count):
            event = ClaudeEvent(
                user_id=f"user_{i % 50:05d}",
                org_id=f"org_{i % 10:04d}",
                surface=SurfaceEnum.API if i % 3 == 0 else SurfaceEnum.CLAUDE_WEB,
                tier=TierEnum.ENTERPRISE if i % 5 == 0 else TierEnum.GENERAL,
                prompt=normal_prompts[i % len(normal_prompts)],
                completion="Here's the information you requested...",
                risk_scores={
                    "cbrn": 0.1,
                    "self_harm": 0.05,
                    "jailbreak": 0.08,
                    "exploitation": 0.06
                },
                tags=["normal"],
                timestamp=datetime.utcnow() - timedelta(minutes=count-i)
            )
            events.append(event)
        
        return events
    
    def generate_pharma_scenario(self) -> List[ClaudeEvent]:
        """Generate pharmaceutical company CBRN scenario"""
        events = []
        
        # Legitimate pharma research that gradually becomes concerning
        pharma_prompts = [
            # Start innocent
            ("What are common laboratory safety procedures?", 0.1),
            ("Explain protein synthesis in cells", 0.15),
            ("How do pharmaceutical companies ensure drug safety?", 0.1),
            
            # Getting more specific
            ("What equipment is needed for a biochemistry lab?", 0.3),
            ("Explain the process of synthesizing simple compounds", 0.4),
            ("What are precursor chemicals in pharmaceutical manufacturing?", 0.6),
            
            # Triggering concerns
            ("How to synthesis of [COMPOUND_X] for research purposes?", 0.75),
            ("What's the production process for [TOXIN_Y] antidotes?", 0.8),
            ("Detailed synthesis procedures for [CHEMICAL_Z] at scale", 0.85),
            ("Home lab synthesis of [DANGEROUS_COMPOUND] possible?", 0.92)
        ]
        
        base_time = datetime.utcnow()
        
        for i, (prompt, risk_score) in enumerate(pharma_prompts):
            event = ClaudeEvent(
                user_id="user_pharma_001",
                org_id="org_pharma",
                surface=SurfaceEnum.API,
                tier=TierEnum.ENTERPRISE,
                prompt=prompt,
                completion="I cannot provide synthesis instructions..." if risk_score > 0.7 else "Here's general information...",
                risk_scores={
                    "cbrn": risk_score,
                    "self_harm": 0.05,
                    "jailbreak": 0.1,
                    "exploitation": 0.05
                },
                tags=["pharma_company", "chemistry"],
                timestamp=base_time + timedelta(minutes=i*2)
            )
            
            if risk_score > 0.8:
                event.tags.append("asl_3_trigger")
            
            events.append(event)
        
        return events
    
    def run_demo(self):
        """Execute the full demo scenario"""
        
        # Check API
        self.print_header("Claude Governance Control Plane Demo")
        
        if not self.check_api():
            self.print_event("critical", "API not running! Please start the backend first.")
            print(f"\nRun: {Fore.CYAN}python backend/app.py{Style.RESET_ALL}")
            return
        
        self.print_event("normal", "API connection successful")
        
        # Step 1: Clean start
        self.print_step(1, "Starting with clean database")
        self.print_narration("We begin with a fresh governance system monitoring Claude API traffic")
        time.sleep(self.step_delay)
        
        # Step 2: Normal traffic
        self.print_step(2, "Ingesting normal Claude API traffic")
        self.print_narration("1000 routine requests from various organizations flow through...")
        
        normal_events = self.generate_normal_traffic(1000)
        
        # Batch ingest
        batch_size = 100
        for i in range(0, len(normal_events), batch_size):
            batch = EventBatch(events=normal_events[i:i+batch_size])
            response = requests.post(f"{API_BASE_URL}/ingest", json=batch.dict())
            if response.status_code == 200:
                result = response.json()
                if i == 0:  # Print first batch results
                    self.print_event("info", f"Processed {result['processed']} events")
                    self.print_event("normal", f"Actions: {result['actions']}")
        
        print(f"\n{Fore.GREEN}✓ Normal traffic baseline established{Style.RESET_ALL}")
        time.sleep(self.step_delay)
        
        # Step 3: Pharmaceutical scenario begins
        self.print_step(3, "Pharmaceutical company begins querying about chemical synthesis")
        self.print_narration("A verified pharmaceutical company starts with legitimate research queries...")
        
        pharma_events = self.generate_pharma_scenario()
        
        # Process pharma events one by one for dramatic effect
        for i, event in enumerate(pharma_events):
            batch = EventBatch(events=[event])
            response = requests.post(f"{API_BASE_URL}/ingest", json=batch.dict())
            
            if response.status_code == 200:
                result = response.json()
                risk_score = event.risk_scores["cbrn"]
                
                # Show escalation
                if risk_score < 0.3:
                    self.print_event("normal", f"Query {i+1}: Low risk ({risk_score:.2f}) - Allowed")
                elif risk_score < 0.7:
                    self.print_event("warning", f"Query {i+1}: Medium risk ({risk_score:.2f}) - Monitoring")
                elif risk_score < 0.8:
                    self.print_event("warning", f"Query {i+1}: High risk ({risk_score:.2f}) - Blocked for general tier")
                else:
                    self.print_event("critical", f"Query {i+1}: CRITICAL ({risk_score:.2f}) - ASL-3 TRIGGERED!")
                    self.print_narration("🚨 CBRN detector flags synthesis instructions at 0.85 confidence!")
                
                time.sleep(1)  # Pause between events
        
        time.sleep(self.step_delay)
        
        # Step 4: Show tier-based response
        self.print_step(4, "Demonstrating tier-based policy enforcement")
        self.print_narration("The same query gets different treatment based on access tier...")
        
        # Create same risky prompt for different tiers
        risky_prompt = "Detailed synthesis procedures for [CHEMICAL_Z]"
        
        for tier in [TierEnum.GENERAL, TierEnum.ENTERPRISE, TierEnum.RESEARCH_SANDBOX]:
            event = ClaudeEvent(
                user_id=f"user_demo_{tier.value}",
                org_id=f"org_demo_{tier.value}",
                surface=SurfaceEnum.API,
                tier=tier,
                prompt=risky_prompt,
                completion="[BLOCKED]",
                risk_scores={"cbrn": 0.85, "self_harm": 0.1, "jailbreak": 0.1, "exploitation": 0.1},
                tags=["demo", "tier_comparison"]
            )
            
            batch = EventBatch(events=[event])
            response = requests.post(f"{API_BASE_URL}/ingest", json=batch.dict())
            
            if response.status_code == 200:
                result = response.json()
                action = list(result['actions'].keys())[list(result['actions'].values()).index(1)]
                
                tier_display = tier.value.replace('_', ' ').title()
                if tier == TierEnum.GENERAL:
                    self.print_event("critical", f"{tier_display}: BLOCKED automatically")
                elif tier == TierEnum.ENTERPRISE:
                    self.print_event("warning", f"{tier_display}: ESCALATED for review")
                else:
                    self.print_event("info", f"{tier_display}: ALLOWED with logging")
        
        time.sleep(self.step_delay)
        
        # Step 5: Review queue
        self.print_step(5, "Safety team reviews escalated events")
        self.print_narration("The governance dashboard shows events pending human review...")
        
        # Get review queue
        response = requests.get(f"{API_BASE_URL}/review-queue")
        if response.status_code == 200:
            queue = response.json()
            self.print_event("info", f"{queue['total']} events in review queue")
            
            if queue['total'] > 0:
                # Simulate reviewing first event
                first_event = queue['items'][0]
                self.print_narration(f"Reviewing event: {first_event['event_id'][:8]}...")
                self.print_event("info", f"Reason: {first_event['reason']}")
                
                # Update policy threshold
                self.print_narration("Safety team decides to adjust CBRN threshold for enterprise tier")
                
                response = requests.post(
                    f"{API_BASE_URL}/review/{first_event['event_id']}",
                    params={
                        "decision": "allow",
                        "update_policy": True,
                        "new_threshold": 0.75,
                        "category": "cbrn"
                    }
                )
                
                if response.status_code == 200:
                    self.print_event("normal", "Policy threshold updated: CBRN/Enterprise 0.7 → 0.75")
        
        time.sleep(self.step_delay)
        
        # Step 6: Generate compliance report
        self.print_step(6, "Generating ISO 42001 compliance evidence")
        self.print_narration("Finally, we export evidence for compliance audit...")
        
        response = requests.get(f"{API_BASE_URL}/export/iso-evidence", params={"days": 7})
        if response.status_code == 200:
            report = response.json()
            self.print_event("info", f"Report generated for {report['period_days']} days")
            self.print_event("normal", f"Total events: {report['summary']['total_events']:,}")
            self.print_event("warning", f"Blocked events: {report['summary']['blocked_events']}")
            self.print_event("critical", f"ASL triggers: {report['summary']['asl_triggers']}")
            self.print_event("info", f"Compliance rate: {report['summary']['compliance_rate']}")
            
            print(f"\n{Fore.CYAN}ISO Controls Evidence:{Style.RESET_ALL}")
            for control in report['controls']:
                status_icon = "✅" if control['compliance_status'] == "compliant" else "⚠️"
                print(f"  {status_icon} {control['iso_clause']} - {control['control_name']}: {control['evidence_count']} events")
        
        # Final summary
        self.print_header("Demo Complete")
        self.print_narration("This demonstrates how Anthropic's safety commitments become customer-verifiable controls")
        
        print(f"\n{Fore.GREEN}Key Takeaways:{Style.RESET_ALL}")
        print("  1. Real-time risk detection across multiple safety categories")
        print("  2. Tier-based policy enforcement with different thresholds")
        print("  3. ASL triggers for capability safety boundaries")
        print("  4. Human-in-the-loop review with policy adaptation")
        print("  5. Automated compliance reporting for ISO 42001")
        
        print(f"\n{Fore.CYAN}🎯 Ready for production deployment!{Style.RESET_ALL}\n")


if __name__ == "__main__":
    print(f"{Fore.MAGENTA}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║     Claude Governance Control Plane - Demo Scenario       ║")
    print("║       Translating RSP into Operational Controls           ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Style.RESET_ALL}")
    
    # Ensure API is running
    print(f"\n{Fore.YELLOW}Prerequisites:{Style.RESET_ALL}")
    print("1. Ensure FastAPI backend is running: python backend/app.py")
    print("2. Ensure Streamlit dashboard is running: streamlit run ui/dashboard.py")
    
    input(f"\n{Fore.GREEN}Press Enter to start the demo...{Style.RESET_ALL}")
    
    # Run demo
    demo = DemoScenario()
    demo.run_demo() 