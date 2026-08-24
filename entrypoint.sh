#!/bin/sh
set -e

echo "Creating database tables if they don't exist..."
python -c "from app.db.init_db import create_tables; create_tables()"

echo "Seeding initial data..."
python seed.py

echo "Starting FastAPI server..."
exec "$@"
