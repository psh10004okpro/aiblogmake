#!/bin/bash
# Start Celery Beat scheduler for periodic tasks

echo "🔄 Starting Celery Beat scheduler..."

# Kill existing Celery Beat process if any
pkill -f "celery beat"

# Start Celery Beat
celery -A app.tasks.celery_tasks beat \
  --loglevel=info \
  --logfile=logs/celery-beat.log \
  --pidfile=celerybeat.pid

echo "✅ Celery Beat started"
