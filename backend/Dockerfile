FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if required by any packages (e.g., asyncpg or psycopg2)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Install standard uvicorn and gunicorn for production
RUN pip install --no-cache-dir uvicorn[standard] gunicorn

COPY . .

# Expose a default port (Render overrides this via PORT environment variable)
EXPOSE 8000

# Remove gunicorn.conf.py dependency to prevent bind conflicts
# Use dynamic $PORT provided by Render
CMD gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:${PORT:-8000} --workers 1 --timeout 120
