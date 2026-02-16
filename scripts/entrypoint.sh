#!/bin/bash
set -e

echo "=== Entrypoint: Starting initialization ==="

# Wait for Postgres to be ready
echo "Waiting for PostgreSQL to be ready..."
until python -c "
import psycopg2
import os
import sys
from urllib.parse import urlparse

try:
    db_url = os.environ.get('DATABASE_URL', '')
    # Parse postgresql+psycopg2://user:pass@host:port/db
    parsed = urlparse(db_url.replace('postgresql+psycopg2://', 'postgresql://'))
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=parsed.username,
        password=parsed.password,
        dbname=parsed.path.lstrip('/'),
        connect_timeout=3
    )
    conn.close()
    print('PostgreSQL is ready!')
    sys.exit(0)
except Exception as e:
    print(f'PostgreSQL not ready: {e}')
    sys.exit(1)
" 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is up - continuing with initialization"

# Create tables if they don't exist
echo "Creating database tables..."
python -m scripts.create_tables || echo "Warning: create_tables failed (tables might already exist)"

# Stamp alembic migrations
echo "Stamping Alembic migrations..."
alembic stamp head || echo "Warning: alembic stamp failed"

# Seed initial data (safe - won't duplicate)
echo "Seeding initial data..."
python -m scripts.seed_safe || echo "Warning: seed_safe failed"

echo "=== Entrypoint: Initialization complete ==="
echo "Starting application: $@"

# Execute the main command
exec "$@"
