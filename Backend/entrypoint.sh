#!/bin/bash
set -e

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Run seed script
echo "Checking/seeding database..."
python -m src.db.seed

# Start uvicorn
echo "Starting backend server..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
