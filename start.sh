#!/bin/bash

# Claude Governance Control Plane - Quick Start Script

echo "🚀 Starting Claude Governance Control Plane..."

# Activate virtual environment
source venv/bin/activate

# Kill any existing services
echo "🛑 Stopping any existing services..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8501 | xargs kill -9 2>/dev/null
sleep 2

# Start API backend
echo "🔧 Starting API backend..."
uvicorn backend.app:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for API to start
echo "⏳ Waiting for API to start..."
sleep 5

# Start Streamlit dashboard
echo "🎨 Starting dashboard..."
streamlit run ui/dashboard.py --server.headless true &
DASHBOARD_PID=$!

# Wait for dashboard
sleep 5

echo ""
echo "✅ All services started!"
echo ""
echo "📊 Dashboard: http://localhost:8501"
echo "🔧 API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for Ctrl+C
trap 'echo ""; echo "Stopping services..."; kill $API_PID $DASHBOARD_PID; exit' INT
wait 