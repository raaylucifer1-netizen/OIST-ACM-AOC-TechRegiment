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

# Expose a default port (Render will override this via the PORT environment variable)
EXPOSE 8000

# Run the application using gunicorn and uvicorn workers with dynamic PORT support
CMD ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker -c gunicorn.conf.py --bind 0.0.0.0:$PORT app.main:app"]
