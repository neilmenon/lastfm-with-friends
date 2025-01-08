import multiprocessing

# WSGI application path (module:app)
wsgi_app = "wsgi:app"

# Worker settings
workers = 6  # Number of worker processes
threads = 1  # Enable threads (Gunicorn uses 1 thread per worker by default)

# Maximum worker lifetime settings
max_requests = 1_000  # Gunicorn equivalent of max-worker-lifetime
max_requests_jitter = 30  # Gunicorn equivalent of max-worker-lifetime-delta

# Socket settings
bind = "unix:lastfm-with-friends.sock"  # UNIX socket path
umask = 0o117  # Socket file permissions (chmod-socket = 660)

# Logging settings
errorlog = "/var/log/lfmwf.log"  # Path to the error log

# Security (User and Group)
user = "nginx"  # UID to switch to
group = "nginx"  # GID to switch to

# Other settings
reload = False  # Enable code reloading in development if needed
preload_app = True  # Preload application for performance
keepalive = 120
timeout = 120
