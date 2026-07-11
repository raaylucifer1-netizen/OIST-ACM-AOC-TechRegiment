# Gunicorn configuration file
import multiprocessing

# Workers
workers = 1
worker_class = "uvicorn.workers.UvicornWorker"

# Binding
bind = "0.0.0.0:8000"

# Timeout
timeout = 120
keepalive = 5
