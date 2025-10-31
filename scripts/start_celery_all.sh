#!/bin/bash
# Start both Celery Worker and Beat scheduler

set -e

echo "🚀 Starting Celery services..."

# Create logs directory if not exists
mkdir -p logs

# Start Celery Worker in background
echo "📊 Starting Celery Worker..."
celery -A app.tasks.celery_tasks worker \
  --loglevel=info \
  --logfile=logs/celery-worker.log \
  --concurrency=4 \
  --max-tasks-per-child=1000 \
  --detach \
  --pidfile=celery-worker.pid

sleep 2

# Start Celery Beat in background
echo "⏰ Starting Celery Beat..."
celery -A app.tasks.celery_tasks beat \
  --loglevel=info \
  --logfile=logs/celery-beat.log \
  --detach \
  --pidfile=celery-beat.pid

sleep 2

echo "✅ Celery services started successfully!"
echo ""
echo "📋 Status:"
echo "   Worker PID: $(cat celery-worker.pid 2>/dev/null || echo 'N/A')"
echo "   Beat PID: $(cat celery-beat.pid 2>/dev/null || echo 'N/A')"
echo ""
echo "📝 Logs:"
echo "   Worker: logs/celery-worker.log"
echo "   Beat: logs/celery-beat.log"
echo ""
echo "🛑 To stop: ./scripts/stop_celery_all.sh"
