#!/usr/bin/env sh
set -e

# Apply database migrations (bank + Django auth/admin tables).
python manage.py migrate --noinput

# Collect admin (and other) static assets for WhiteNoise under ASGI.
python manage.py collectstatic --noinput

# Bootstrap a Django admin superuser when credentials are provided.
# Uses the standard DJANGO_SUPERUSER_* env vars; skips if the user already exists.
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
username = '${DJANGO_SUPERUSER_USERNAME}'
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username=username,
        email='${DJANGO_SUPERUSER_EMAIL:-admin@example.com}',
        password='${DJANGO_SUPERUSER_PASSWORD}',
    )
    print(f'Created Django admin superuser: {username}')
else:
    print(f'Django admin superuser already exists: {username}')
"
fi

exec uvicorn infrastructure.django.asgi:application \
    --host 0.0.0.0 \
    --port 8000
