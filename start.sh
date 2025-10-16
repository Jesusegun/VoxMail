#!/usr/bin/env bash
# =============================================================================
# STARTUP SCRIPT - VPS-Ready Web App and Optional Scheduler
# =============================================================================
# This script runs both processes or just web based on environment variables

set -euo pipefail  # Exit on error, undefined vars, pipe failures

echo "🚀 Starting VoxMail - AI Email Assistant..."
echo "================================================"

# Set defaults for environment variables
: "${AI_MAX_CONCURRENCY:=2}"
: "${RUN_SCHEDULER:=true}"
: "${PORT:=8080}"

export AI_MAX_CONCURRENCY

echo "🔧 Configuration:"
echo "   AI_MAX_CONCURRENCY: $AI_MAX_CONCURRENCY"
echo "   RUN_SCHEDULER: $RUN_SCHEDULER"
echo "   PORT: $PORT"
echo "================================================"

# Start scheduler conditionally
if [ "$RUN_SCHEDULER" = "true" ]; then
    echo "📅 Starting scheduler process..."
    python scheduler.py &
    SCHEDULER_PID=$!
    echo "✅ Scheduler started (PID: $SCHEDULER_PID)"
    
    # Give scheduler a moment to initialize
    sleep 2
else
    echo "⏭️  Scheduler disabled (RUN_SCHEDULER=false)"
fi

# Start web app with gunicorn (production server)
echo "🌐 Starting web server (gunicorn) on port $PORT..."
echo "   Workers: 2, Threads per worker: 4"

# Use gunicorn with:
# -w 2: 2 worker processes (good for CPU-bound tasks)
# -k gthread: threaded workers (handles concurrent requests well)
# --threads 4: 4 threads per worker
# -b 0.0.0.0:$PORT: bind to all interfaces on specified port
# --timeout 120: 2 minute timeout (AI processing can be slow)
# --preload: preload app code (helps with memory sharing)
exec gunicorn \
    -w 2 \
    -k gthread \
    --threads 4 \
    -b "0.0.0.0:$PORT" \
    --timeout 120 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    web_app:app
