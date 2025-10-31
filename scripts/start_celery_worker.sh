#!/bin/bash
# Start Celery Worker for processing tasks

echo "🔄 Starting Celery Worker..."

# Kill existing Celery Worker processes if any
pkill -f "celery worker"

# Start Celery Worker
celery -A app.tasks.celery_tasks worker \
  --loglevel=info \
  --logfile=logs/celery-worker.log \
  --concurrency=4 \
  --max-tasks-per-child=1000

echo "✅ Celery Worker started"
