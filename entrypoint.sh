#!/bin/bash

set -e

 echo "Прогоняются миграции..."
 alembic upgrade head

echo "Запускается приложение..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
