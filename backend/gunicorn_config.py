"""
Gunicorn configuration for production deployment
CRITICAL FIX: Production WSGI server configuration
"""
import os
import multiprocessing

# ==================== SERVER SOCKET ====================
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
backlog = 2048

# ==================== WORKER PROCESSES ====================
# Calculate optimal workers: (2 x CPU cores) + 1
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))

# Worker class
# Options: 'sync', 'eventlet', 'gevent', 'tornado'
# Use 'gevent' for better async performance (requires: pip install gevent)
worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'sync')

# Maximum number of simultaneous clients per worker
worker_connections = 1000

# Workers silent for more than this many seconds are killed and restarted
timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))

# The number of seconds to wait for requests on a Keep-Alive connection
keepalive = 5

# ==================== LOGGING ====================
# Access log - use '-' for stdout
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '-')

# Error log - use '-' for stderr  
errorlog = os.getenv('GUNICORN_ERROR_LOG', '-')

# Log level
loglevel = os.getenv('LOG_LEVEL', 'info').lower()

# Access log format
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s '
    '"%(f)s" "%(a)s" %(D)s %(p)s'
)
# Format explanation:
# %(h)s - remote address
# %(l)s - '-'
# %(u)s - user name
# %(t)s - date of the request
# %(r)s - status line (e.g. GET / HTTP/1.1)
# %(s)s - status code
# %(b)s - response length
# %(f)s - referer
# %(a)s - user agent
# %(D)s - request time in microseconds
# %(p)s - process ID

# ==================== PROCESS NAMING ====================
proc_name = 'knowalledge-api'

# ==================== SERVER MECHANICS ====================
# Daemonize the Gunicorn process
daemon = False

# A filename to use for the PID file
pidfile = None

# Switch worker processes to run as this user
user = None
group = None

# A directory to use for the worker heartbeat temporary file
tmp_upload_dir = None

# ==================== SSL ====================
# SSL key file path
keyfile = os.getenv('SSL_KEYFILE')

# SSL certificate file path
certfile = os.getenv('SSL_CERTFILE')

# SSL version to use
ssl_version = 'TLSv1_2'

# Certificate authority bundle file
ca_certs = os.getenv('SSL_CA_CERTS')

# ==================== SECURITY ====================
# Limit the allowed size of an HTTP request header field
limit_request_field_size = 8190

# Limit the number of HTTP headers fields in a request
limit_request_fields = 100

# Limit the allowed size of an HTTP request line
limit_request_line = 4094

# ==================== PERFORMANCE ====================
# Load application code before the worker processes are forked
# This can save RAM and improve server boot time
preload_app = True

# Restart workers after this many requests (prevent memory leaks)
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', '1000'))

# Randomize max_requests to prevent all workers restarting at once
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', '50'))

# ==================== SERVER HOOKS ====================

def on_starting(server):
    """
    Called just before the master process is initialized
    """
    print("=" * 70)
    print("🚀 Starting KnowAllEdge API Server")
    print("=" * 70)
    print(f"📍 Bind: {bind}")
    print(f"👷 Workers: {workers}")
    print(f"⚙️  Worker Class: {worker_class}")
    print(f"⏱️  Timeout: {timeout}s")
    print(f"📊 Log Level: {loglevel}")
    print(f"🔄 Max Requests: {max_requests} (±{max_requests_jitter})")
    if keyfile and certfile:
        print(f"🔒 SSL: Enabled")
    print("=" * 70)

def on_reload(server):
    """
    Called to recycle workers during a reload via SIGHUP
    """
    print("🔄 Reloading workers...")

def when_ready(server):
    """
    Called just after the server is started
    """
    print("✅ Server is ready. Spawning workers...")

def worker_int(worker):
    """
    Called just after a worker exited on SIGINT or SIGQUIT
    """
    print(f"⚠️  Worker {worker.pid} received SIGINT/SIGQUIT")

def worker_abort(worker):
    """
    Called when a worker received the SIGABRT signal
    """
    print(f"❌ Worker {worker.pid} received SIGABRT - killed")

def pre_fork(server, worker):
    """
    Called just before a worker is forked
    """
    pass

def post_fork(server, worker):
    """
    Called just after a worker has been forked
    """
    print(f"👶 Worker spawned (pid: {worker.pid})")

def post_worker_init(worker):
    """
    Called just after a worker has initialized the application
    """
    print(f"✅ Worker {worker.pid} initialized")

def worker_exit(server, worker):
    """
    Called just after a worker has been exited
    """
    print(f"👋 Worker {worker.pid} exited")

def child_exit(server, worker):
    """
    Called just after a worker has been exited, in the master process
    """
    pass

def nworkers_changed(server, new_value, old_value):
    """
    Called just after num_workers has been changed
    """
    print(f"👷 Workers changed: {old_value} → {new_value}")

def on_exit(server):
    """
    Called just before exiting Gunicorn
    """
    print("=" * 70)
    print("👋 Shutting down KnowAllEdge API Server")
    print("=" * 70)

# ==================== DEVELOPMENT OVERRIDES ====================
# Override settings for development
if os.getenv('FLASK_ENV') == 'development' or os.getenv('ENVIRONMENT') == 'development':
    workers = 2
    loglevel = 'debug'
    reload = True  # Auto-reload on code changes
    print("🔧 Development mode enabled")
