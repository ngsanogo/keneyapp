#!/bin/bash

# KeneyApp Startup Script
echo "🚀 Starting KeneyApp..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Install frontend dependencies
echo "📥 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Check if database is running
echo "🔍 Checking database connection..."
python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://keneyapp:keneyapp123@localhost:5432/keneyapp')
    conn.close()
    print('✅ Database connection successful')
except Exception as e:
    print('❌ Database connection failed:', e)
    print('Please ensure PostgreSQL is running and the database is created')
    exit(1)
"

# Run database initialization
echo "🗄️ Initializing database..."
python scripts/init_db.py

# Start the application
echo "🎉 Starting KeneyApp..."
echo "Backend will be available at: http://localhost:8000"
echo "Frontend will be available at: http://localhost:3000"
echo "API documentation at: http://localhost:8000/api/docs"

# Start backend in background
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend
cd frontend
npm start &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
