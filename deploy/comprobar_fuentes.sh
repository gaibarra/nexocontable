#!/usr/bin/env bash
set -euo pipefail
umask 077
cd /home/gaibarra/manual_contable_ai
mkdir -p output/biblioteca/operacion
exec /usr/bin/flock -n output/biblioteca/operacion/monitor.lock /usr/bin/env DEBUG=False venv/bin/python manage.py comprobar_fuentes
