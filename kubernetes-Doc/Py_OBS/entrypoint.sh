#!/bin/bash
set -e

echo "Creating database tables..."
python -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all(); print('Tables created.')"

echo "Seeding database..."
flask seed

echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 run:app
