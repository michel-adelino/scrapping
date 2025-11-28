#!/bin/bash
# Script to fix corrupted Celery Beat schedule files

echo "Fixing Celery Beat schedule files..."

# Stop any running Beat processes
echo "Stopping any running Celery Beat processes..."
pkill -f "celery.*beat" 2>/dev/null || true
sleep 2

# Delete corrupted schedule files
echo "Removing corrupted schedule files..."
rm -f celerybeat-schedule* 2>/dev/null || true

echo "✓ Schedule files cleaned up"
echo ""
echo "Now restart Celery Beat:"
echo "  source venv/bin/activate"
echo "  python -m celery -A celery_app beat --loglevel=info"

