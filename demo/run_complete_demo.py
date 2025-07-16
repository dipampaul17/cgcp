#!/usr/bin/env python3
"""
Complete Demo Runner - Claude Governance Control Plane
Ensures end-to-end execution with real-world scenarios
"""

import subprocess
import time
import sys
import os
import requests
from colorama import init, Fore, Style, Back

# Initialize colorama
init()

def print_banner():
    """Print executive demo banner"""
    print(f"{Back.BLUE}{Fore.WHITE}")
    print("═" * 80)
    print("    CLAUDE GOVERNANCE CONTROL PLANE - COMPLETE DEMONSTRATION".center(80))
    print("    Production-Ready RSP Implementation".center(80))
    print("═" * 80)
    print(f"{Style.RESET_ALL}\n")

def print_status(message: str, status: str = "info"):
    """Print colored status messages"""
    colors = {
        "info": Fore.BLUE,
        "success": Fore.GREEN,
        "warning": Fore.YELLOW,
        "error": Fore.RED
    }
    icons = {
        "info": "ℹ",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    print(f"{colors[status]}{icons[status]} {message}{Style.RESET_ALL}")

def check_service(url: str, service_name: str, timeout: int = 2) -> bool:
    """Check if a service is running"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print_status(f"{service_name} is operational", "success")
            return True
    except:
        pass
    print_status(f"{service_name} is not responding", "error")
    return False

def kill_existing_services():
    """Gracefully terminate existing services"""
    print_status("Terminating existing services...", "info")
    
    # Kill processes on our ports
    for port in [8000, 8501]:
        try:
            result = subprocess.run(
                f"lsof -ti:{port} | xargs kill -9",
                shell=True,
                capture_output=True,
                text=True
            )
        except:
            pass
    
    time.sleep(2)
    print_status("Service cleanup completed", "success")

def wait_for_service(url: str, service_name: str, max_attempts: int = 30) -> bool:
    """Wait for a service to become available"""
    print_status(f"Waiting for {service_name} to start...", "info")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                print_status(f"{service_name} is ready", "success")
                return True
        except:
            pass
        
        # Show progress
        if (attempt + 1) % 5 == 0:
            print(f"   Attempt {attempt + 1}/{max_attempts}...")
        
        time.sleep(1)
    
    print_status(f"{service_name} failed to start within {max_attempts} seconds", "error")
    return False

def check_prerequisites():
    """Verify all prerequisites are met"""
    print_status("Checking prerequisites...", "info")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print_status("Python 3.8+ required", "error")
        return False
    
    # Check virtual environment
    if not os.path.exists("venv"):
        print_status("Virtual environment not found. Please run: python -m venv venv", "error")
        return False
    
    # Check required files
    required_files = [
        "backend/app.py",
        "ui/dashboard.py",
        "requirements.txt",
        "demo/production_demo.py",
        "data/synthetic_generator.py"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print_status(f"Required file missing: {file_path}", "error")
            return False
    
    print_status("All prerequisites satisfied", "success")
    return True

def reset_database():
    """Reset database for clean demo"""
    print_status("Resetting database for clean demo...", "info")
    
    try:
        result = subprocess.run(
            [sys.executable, "demo/reset_database.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print_status("Database reset successful", "success")
            return True
        else:
            print_status(f"Database reset failed: {result.stderr}", "error")
            return False
            
    except subprocess.TimeoutExpired:
        print_status("Database reset timed out", "error")
        return False
    except Exception as e:
        print_status(f"Database reset error: {e}", "error")
        return False

def start_api_backend():
    """Start the API backend service"""
    print_status("Starting API backend...", "info")
    
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for API to be ready
        if wait_for_service("http://localhost:8000/health", "API Backend"):
            return process
        else:
            process.kill()
            return None
            
    except Exception as e:
        print_status(f"Failed to start API: {e}", "error")
        return None

def start_dashboard():
    """Start the Streamlit dashboard"""
    print_status("Starting Streamlit dashboard...", "info")
    
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "ui/dashboard.py", 
             "--server.headless", "true", "--server.port", "8501"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for dashboard (less critical)
        if wait_for_service("http://localhost:8501", "Dashboard", max_attempts=20):
            return process
        else:
            print_status("Dashboard may not be fully ready, continuing...", "warning")
            return process
            
    except Exception as e:
        print_status(f"Failed to start dashboard: {e}", "warning")
        return None

def generate_demo_data():
    """Generate fresh synthetic data for demo"""
    print_status("Generating fresh demonstration data...", "info")
    
    try:
        result = subprocess.run(
            [sys.executable, "data/synthetic_generator.py"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print_status("Demo data generated successfully", "success")
            # Show key statistics from output
            lines = result.stdout.split('\n')
            for line in lines:
                if 'events' in line.lower() and ('generated' in line.lower() or 'total' in line.lower()):
                    print(f"   {line.strip()}")
            return True
        else:
            print_status(f"Data generation failed: {result.stderr}", "error")
            return False
            
    except subprocess.TimeoutExpired:
        print_status("Data generation timed out", "error")
        return False
    except Exception as e:
        print_status(f"Data generation error: {e}", "error")
        return False

def run_production_demo():
    """Execute the main production demonstration"""
    print_status("Launching production demonstration...", "info")
    
    try:
        # Run the enhanced production demo
        result = subprocess.run(
            [sys.executable, "demo/production_demo.py"],
            timeout=300  # 5 minutes max
        )
        
        if result.returncode == 0:
            print_status("Production demo completed successfully", "success")
            return True
        else:
            print_status("Production demo ended with issues", "warning")
            return False
            
    except subprocess.TimeoutExpired:
        print_status("Demo timed out after 5 minutes", "warning")
        return False
    except KeyboardInterrupt:
        print_status("Demo interrupted by user", "info")
        return True
    except Exception as e:
        print_status(f"Demo execution error: {e}", "error")
        return False

def show_access_info():
    """Display access information"""
    print(f"\n{Fore.CYAN}🌐 System Access Points:{Style.RESET_ALL}")
    print("┌─────────────────────────────────────────────────┐")
    print("│                                                 │")
    print("│ 📊 Dashboard:    http://localhost:8501         │")
    print("│ 🔧 API:          http://localhost:8000         │")
    print("│ 📚 Documentation: http://localhost:8000/docs   │")
    print("│                                                 │")
    print("└─────────────────────────────────────────────────┘")

def main():
    """Main execution flow"""
    print_banner()
    
    # Step 1: Prerequisites
    if not check_prerequisites():
        print_status("Prerequisites check failed. Please resolve issues and retry.", "error")
        return 1
    
    # Step 2: Cleanup
    kill_existing_services()
    
    # Step 3: Database reset
    if not reset_database():
        print_status("Database reset failed. Demo may have inconsistent data.", "warning")
    
    # Step 4: Generate demo data
    if not generate_demo_data():
        print_status("Demo data generation failed. Continuing with existing data.", "warning")
    
    # Step 5: Start API backend
    api_process = start_api_backend()
    if not api_process:
        print_status("Failed to start API backend. Cannot continue.", "error")
        return 1
    
    # Step 6: Start dashboard
    dashboard_process = start_dashboard()
    
    # Step 7: Show access information
    show_access_info()
    
    try:
        # Step 8: Run production demo
        print(f"\n{Fore.YELLOW}🎭 Ready to run production demonstration{Style.RESET_ALL}")
        print("   This will showcase real-world RSP implementation")
        print("   with authentic scenarios and executive-level reporting.")
        
        user_input = input(f"\n{Fore.GREEN}Press Enter to start demo (or 'skip' to keep services running): {Style.RESET_ALL}")
        
        if user_input.lower().strip() != 'skip':
            demo_success = run_production_demo()
            
            if demo_success:
                print(f"\n{Back.GREEN}{Fore.BLACK} DEMO COMPLETED SUCCESSFULLY {Style.RESET_ALL}")
            else:
                print(f"\n{Back.YELLOW}{Fore.BLACK} DEMO COMPLETED WITH ISSUES {Style.RESET_ALL}")
        
        # Step 9: Keep services running
        print(f"\n{Fore.CYAN}✨ Services are running and ready for exploration{Style.RESET_ALL}")
        print("   You can now access the dashboard and API endpoints")
        print("   Press Ctrl+C to stop all services...")
        
        # Monitor and keep services running
        while True:
            # Check if processes are still alive
            if api_process and api_process.poll() is not None:
                print_status("API backend stopped unexpectedly", "error")
                break
            
            if dashboard_process and dashboard_process.poll() is not None:
                print_status("Dashboard stopped (non-critical)", "warning")
            
            time.sleep(5)
    
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}🛑 Received shutdown signal{Style.RESET_ALL}")
    
    finally:
        # Cleanup
        print_status("Shutting down services...", "info")
        
        if api_process:
            api_process.terminate()
            try:
                api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                api_process.kill()
        
        if dashboard_process:
            dashboard_process.terminate()
            try:
                dashboard_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                dashboard_process.kill()
        
        print_status("All services stopped", "success")
        
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print_status(f"Unexpected error: {e}", "error")
        sys.exit(1) 