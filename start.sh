#!/bin/bash
# =============================================================================
# STARTUP SCRIPT - Starts Both Web App and Scheduler
# =============================================================================
# This script runs when your container starts on Fly.io

echo "🚀 Starting VoxMail - AI Email Assistant..."
echo "================================================"

# Start scheduler in background
# The & at the end means "run in background"
echo "📅 Starting scheduler process..."
python scheduler.py &
SCHEDULER_PID=$!
echo "✅ Scheduler started (PID: $SCHEDULER_PID)"

# Give scheduler a moment to initialize
sleep 2

# Start Flask web app in foreground
# This keeps the container running
echo "🌐 Starting Flask web app on port 8080..."
python web_app.py

# If web app crashes, this line runs
echo "❌ Web app stopped unexpectedly"
