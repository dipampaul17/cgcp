#!/usr/bin/env python3
"""
Complete Demo Runner
Ensures clean end-to-end execution of the Claude Governance Control Plane demo
"""

import subprocess
import time
import sys
import os
import requests


def check_service(url: str, service_name: str) -> bool:
    """Check if a service is running"""
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            print(f"✅ {service_name} is running")
            return True
    except:
        pass
    print(f"❌ {service_name} is not running")
    return False


def kill_existing_services():
    """Kill any existing services on our ports"""
    print("\n🛑 Stopping existing services...")
    subprocess.run("lsof -ti:8000 | xargs kill -9 2>/dev/null", shell=True)
    subprocess.run("lsof -ti:8501 | xargs kill -9 2>/dev/null", shell=True)
    time.sleep(2)


def main():
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║           CLAUDE GOVERNANCE CONTROL PLANE                     ║
    ║           Complete Demo Runner                                ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Kill existing services
    kill_existing_services()
    
    # Step 2: Reset database
    print("\n📊 Step 1: Resetting database...")
    result = subprocess.run([sys.executable, "demo/reset_database.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to reset database: {result.stderr}")
        return 1
    print(result.stdout)
    
    # Step 3: Generate fresh synthetic data
    print("\n🎲 Step 2: Generating fresh synthetic data...")
    result = subprocess.run([sys.executable, "data/synthetic_generator.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to generate data: {result.stderr}")
        return 1
    print(result.stdout)
    
    # Step 4: Start API backend
    print("\n🚀 Step 3: Starting API backend...")
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for API to start
    print("   Waiting for API to start...")
    for i in range(30):
        if check_service("http://localhost:8000/health", "API Backend"):
            break
        time.sleep(1)
    else:
        print("❌ API failed to start")
        api_process.kill()
        return 1
    
    # Step 5: Start Streamlit dashboard
    print("\n🎨 Step 4: Starting Streamlit dashboard...")
    dashboard_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "ui/dashboard.py", "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for dashboard to start
    print("   Waiting for dashboard to start...")
    for i in range(30):
        if check_service("http://localhost:8501", "Streamlit Dashboard"):
            break
        time.sleep(1)
    else:
        print("❌ Dashboard failed to start")
        api_process.kill()
        dashboard_process.kill()
        return 1
    
    # Step 6: Ingest synthetic data
    print("\n📥 Step 5: Ingesting synthetic data...")
    time.sleep(2)  # Give services a moment to stabilize
    result = subprocess.run([sys.executable, "demo/ingest_data.py"], capture_output=True, text=True)
    print(result.stdout)
    
    # Step 7: Run production demo
    print("\n🎭 Step 6: Running production demo...")
    print("\n" + "="*60)
    print("Services are ready! You can now:")
    print(f"  • View the dashboard at: http://localhost:8501")
    print(f"  • Access the API at: http://localhost:8000")
    print(f"  • API docs at: http://localhost:8000/docs")
    print("="*60)
    
    # Keep services running
    print("\n✨ Press Ctrl+C to stop all services...")
    
    try:
        # Run the production demo
        subprocess.run([sys.executable, "demo/production_demo.py"])
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        api_process.kill()
        dashboard_process.kill()
        print("✅ All services stopped")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 