#!/usr/bin/env bash
set -euo pipefail
# Instala únicamente el servicio privado y la ruta /panel/ del sitio existente.
APP_DIR=/home/gaibarra/manual_contable_ai
NGINX_SITE=/etc/nginx/sites-available/manual_contable
if [[ $EUID -ne 0 ]]; then
    echo 'Ejecuta: sudo bash deploy/instalar_panel.sh' >&2
    exit 1
fi
exec 9>/run/lock/manual-contable-panel.lock
flock -n 9 || { echo 'Ya hay una instalación en curso.' >&2; exit 1; }
cd "$APP_DIR"
sudo -u gaibarra env DEBUG=False "$APP_DIR/venv/bin/python" manage.py check --deploy
sudo -u gaibarra env DEBUG=False "$APP_DIR/venv/bin/python" manage.py migrate --noinput
sudo -u gaibarra env DEBUG=False "$APP_DIR/venv/bin/python" manage.py collectstatic --noinput > /dev/null
install -m 644 deploy/manual_contable_panel.service /etc/systemd/system/manual_contable_panel.service
install -m 644 deploy/nginx_panel.location.conf /etc/nginx/snippets/manual_contable_panel.conf
BACKUP_PATH="${NGINX_SITE}.panel-backup.$(date +%Y%m%d%H%M%S)"
cp -p "$NGINX_SITE" "$BACKUP_PATH"
restaurar_en_error() {
    cp -p "$BACKUP_PATH" "$NGINX_SITE"
    echo 'La instalación se detuvo; se restauró el archivo de Nginx anterior.' >&2
}
trap restaurar_en_error ERR
python3 - "$NGINX_SITE" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text()
include = '    include /etc/nginx/snippets/manual_contable_panel.conf;\n\n'
if include.strip() not in text:
    marker = '    # ── Django/Gunicorn (proxy reverso) ──'
    if text.count(marker) != 1:
        raise SystemExit('No se reconoció el bloque HTTPS. Revisar manualmente; archivo conservado.')
    path.write_text(text.replace(marker, include + marker))
PY
if ! nginx -t; then
    cp -p "$BACKUP_PATH" "$NGINX_SITE"
    echo 'Falló la validación de Nginx. Se restauró el archivo anterior.' >&2
    exit 1
fi
# Detener únicamente el daemon privado previo si lo arrancó la puerta local.
if [[ -f panel.pid ]]; then
    read -r PANEL_PID < panel.pid
    if [[ "$PANEL_PID" =~ ^[0-9]+$ ]] && [[ -r "/proc/$PANEL_PID/cmdline" ]] && tr '\0' ' ' < "/proc/$PANEL_PID/cmdline" | grep -q 'manual_contable_ai.wsgi_panel'; then
        kill -TERM "$PANEL_PID"
        for _ in {1..40}; do
            if ! kill -0 "$PANEL_PID" 2>/dev/null; then break; fi
            sleep 0.5
        done
        if kill -0 "$PANEL_PID" 2>/dev/null; then
            echo 'El daemon privado sigue cerrando. Reintenta cuando termine.' >&2
            exit 1
        fi
    fi
fi
systemctl daemon-reload
systemctl enable --now manual_contable_panel
systemctl is-active --quiet manual_contable_panel
PANEL_LISTO=0
for _ in {1..40}; do
    if curl --fail --silent --max-time 2 --output /dev/null --unix-socket "$APP_DIR/panel.sock" -H 'Host: manualcontable.online' -H 'X-Forwarded-Proto: https' http://localhost/panel/login/; then
        PANEL_LISTO=1
        break
    fi
    sleep 0.5
done
if [[ "$PANEL_LISTO" -ne 1 ]]; then
    restaurar_en_error
    echo 'El panel no respondió. Revisar: journalctl -u manual_contable_panel -n 50' >&2
    exit 1
fi
systemctl reload nginx
trap - ERR
printf 'Panel independiente activo: https://manualcontable.online/panel/\n'
