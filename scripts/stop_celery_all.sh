#!/bin/bash
# Stop all Celery services

echo "🛑 Stopping Celery services..."

# Stop Celery Worker
if [ -f celery-worker.pid ]; then
    kill $(cat celery-worker.pid) 2>/dev/null || true
    rm celery-worker.pid
    echo "✅ Celery Worker stopped"
else
    pkill -f "celery worker" 2>/dev/null || true
    echo "⚠️  No Worker PID file found, killed by process name"
fi

# Stop Celery Beat
if [ -f celery-beat.pid ]; then
    kill $(cat celery-beat.pid) 2>/dev/null || true
    rm celery-beat.pid
    echo "✅ Celery Beat stopped"
else
    pkill -f "celery beat" 2>/dev/null || true
    echo "⚠️  No Beat PID file found, killed by process name"
fi

# Clean up schedule file
rm -f celerybeat-schedule.db

echo "✅ All Celery services stopped"
