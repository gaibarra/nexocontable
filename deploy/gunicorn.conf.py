# ======================================
# Gunicorn - Configuración de producción
# Manual Contable AI
# ======================================

import multiprocessing

# Conexión
bind = "unix:/home/gaibarra/manual_contable_ai/manual_contable.sock"
# Alternativa TCP: bind = "127.0.0.1:8000"

# Workers
# Regla general: (2 × núcleos) + 1
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gthread"
threads = 2
worker_connections = 1000

# Timeouts
timeout = 120  # Aumentado por llamadas a OpenAI que pueden tardar
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Proceso
daemon = False
pidfile = "/home/gaibarra/manual_contable_ai/manual_contable.pid"
umask = 0o007
# user = "www-data"
# group = "www-data"

# Seguridad
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Reinicio automático por memory leaks
max_requests = 1000
max_requests_jitter = 50

# Preload para arranque más rápido
preload_app = True
