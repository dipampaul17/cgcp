#!/bin/bash

# Claude Governance Control Plane -  Startup Script

echo "🚀 Starting Claude Governance Control Plane..."

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill processes on a port
kill_port() {
    local port=$1
    echo "🛑 Freeing port $port..."
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
    sleep 1
}

# Activate virtual environment
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  Virtual environment not found. Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check for required files
if [ ! -f "backend/app.py" ]; then
    echo "❌ Backend app.py not found!"
    exit 1
fi

if [ ! -f "ui/dashboard.py" ]; then
    echo "❌ Dashboard not found!"
    exit 1
fi

# Kill existing services on our ports
echo "🧹 Cleaning up existing services..."
kill_port 8000
kill_port 8501

# Wait a moment for cleanup
sleep 2

# Start API backend
echo "🔧 Starting API backend on port 8000..."
if check_port 8000; then
    echo "❌ Port 8000 still in use after cleanup!"
    exit 1
fi

python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for API to start and verify
echo "⏳ Waiting for API to initialize..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ API backend ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ API failed to start within 30 seconds"
        kill $API_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Start Streamlit dashboard
echo "🎨 Starting dashboard on port 8501..."
if check_port 8501; then
    echo "❌ Port 8501 still in use after cleanup!"
    kill $API_PID
    exit 1
fi

streamlit run ui/dashboard.py --server.headless true --server.port 8501 &
DASHBOARD_PID=$!

# Wait for dashboard and verify
echo "⏳ Waiting for dashboard to initialize..."
for i in {1..30}; do
    if curl -s http://localhost:8501 >/dev/null 2>&1; then
        echo "✅ Dashboard ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  Dashboard may not be fully ready, but continuing..."
        break
    fi
    sleep 1
done

echo ""
echo "🎉 Claude Governance Control Plane is ready!"
echo ""
echo "┌─────────────────────────────────────────────────┐"
echo "│                 Access Points                   │"
echo "├─────────────────────────────────────────────────┤"
echo "│ 📊 Dashboard:    http://localhost:8501         │"
echo "│ 🔧 API:          http://localhost:8000         │"
echo "│ 📚 API Docs:     http://localhost:8000/docs    │"
echo "└─────────────────────────────────────────────────┘"
echo ""
echo "🎭 To run the production demo:"
echo "   python demo/production_demo.py"
echo ""
echo "🔄 To reset and run complete demo:"
echo "   python demo/run_complete_demo.py"
echo ""
echo "Press Ctrl+C to stop all services..."

# Trap function to clean shutdown
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $API_PID $DASHBOARD_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Set trap for clean shutdown
trap cleanup INT TERM

# Keep script running and monitor processes
while true; do
    # Check if API is still running
    if ! kill -0 $API_PID 2>/dev/null; then
        echo "❌ API backend stopped unexpectedly"
        kill $DASHBOARD_PID 2>/dev/null
        exit 1
    fi
    
    # Check if dashboard is still running
    if ! kill -0 $DASHBOARD_PID 2>/dev/null; then
        echo "⚠️  Dashboard stopped unexpectedly"
        # Dashboard crash is not critical, continue with API only
    fi
    
    sleep 5
done 