"""
Script to ingest synthetic data into the Claude Governance Control Plane
"""

import json
import requests
from typing import List, Dict
from uuid import UUID
from datetime import datetime

API_BASE_URL = "http://localhost:8000"


def ingest_synthetic_data(file_path: str = "data/synthetic_events.jsonl", batch_size: int = 50):
    """
    Ingest synthetic events from JSONL file into the system
    """
    print(f"📥 Loading events from {file_path}...")
    
    # Read all events
    events = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                event = json.loads(line)
                # Convert event_id string to UUID format
                if 'event_id' in event and isinstance(event['event_id'], str):
                    event['event_id'] = event['event_id']
                # Ensure timestamp is properly formatted
                if 'timestamp' in event and isinstance(event['timestamp'], str):
                    event['timestamp'] = event['timestamp']
                # Fix model version
                if 'model_version' in event:
                    event['model_version'] = 'claude-3-sonnet'
                events.append(event)
    
    print(f"📊 Loaded {len(events)} events")
    
    # Process in batches
    total_processed = 0
    total_blocked = 0
    total_escalated = 0
    total_asl_triggers = 0
    
    print(f"\n🚀 Ingesting events in batches of {batch_size}...")
    
    for i in range(0, len(events), batch_size):
        batch = events[i:i+batch_size]
        batch_num = i // batch_size + 1
        
        try:
            # Send batch to API
            response = requests.post(
                f"{API_BASE_URL}/ingest",
                json={"events": batch},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                processed = result.get('processed', 0)
                actions = result.get('actions', {})
                asl = result.get('asl_triggers', 0)
                
                total_processed += processed
                total_blocked += actions.get('block', 0)
                total_escalated += actions.get('escalate', 0)
                total_asl_triggers += asl
                
                print(f"  Batch {batch_num:3d}: ✅ Processed {processed} | "
                      f"Blocked: {actions.get('block', 0)} | "
                      f"Escalated: {actions.get('escalate', 0)} | "
                      f"ASL: {asl}")
            else:
                print(f"  Batch {batch_num:3d}: ❌ Error {response.status_code}")
                if response.text:
                    print(f"    Details: {response.text[:200]}")
                    
        except Exception as e:
            print(f"  Batch {batch_num:3d}: ❌ Exception: {str(e)}")
    
    # Summary
    print("\n" + "="*60)
    print("📈 INGESTION SUMMARY")
    print("="*60)
    print(f"Total Events Processed: {total_processed:,}")
    print(f"Total Blocked:         {total_blocked:,} ({total_blocked/max(total_processed,1)*100:.1f}%)")
    print(f"Total Escalated:       {total_escalated:,} ({total_escalated/max(total_processed,1)*100:.1f}%)")
    print(f"ASL-3 Triggers:        {total_asl_triggers:,}")
    print("="*60)
    
    # Check metrics
    print("\n📊 Verifying system metrics...")
    try:
        metrics = requests.get(f"{API_BASE_URL}/metrics").json()
        print(f"✅ System shows {metrics.get('total_events', 0):,} total events")
    except:
        print("❌ Could not fetch metrics")


if __name__ == "__main__":
    # Check API health first
    try:
        health = requests.get(f"{API_BASE_URL}/health")
        if health.status_code == 200:
            print("✅ API is healthy")
            ingest_synthetic_data()
        else:
            print("❌ API is not responding properly")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print(f"   Make sure the API is running at {API_BASE_URL}") 