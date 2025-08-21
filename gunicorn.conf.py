# Gunicorn configuration file

# Number of worker processes (2 workers = safe for Railway free plan)
workers = 2

# Each worker will handle requests in multiple threads
threads = 4

# Worker type: gthread is better for I/O tasks (like sending emails)
worker_class = "gthread"

# Timeout in seconds (default 30s → increase to 120s)
timeout = 120

# Bind to Railway’s port
bind = "0.0.0.0:8080"

# Optional: log level
loglevel = "info"
