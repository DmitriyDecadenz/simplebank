#!/usr/bin/env sh
set -e

# Apply database migrations, then serve the ASGI app.
python manage.py migrate --noinput

exec uvicorn infrastructure.django.asgi:application \
    --host 0.0.0.0 \
    --port 8000
