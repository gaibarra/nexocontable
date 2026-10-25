#!/usr/bin/env bash
# Actualiza una instalación existente, sin reconfigurar Nginx ni certificados.
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
SERVICE_NAME="${SERVICE_NAME:-manual_contable}"
PROCESS_MANAGER="${PROCESS_MANAGER:-systemd}"
INSTALL_DEPS=true

usage() {
    cat <<'HELP'
Uso: sudo bash deploy/deploy.sh --update [opciones]
     sudo bash deploy/actualizar.sh [opciones]

  --manager systemd|supervisor  Gestor de procesos (predeterminado: systemd).
  --skip-install               Omitir pip install si las dependencias ya están instaladas.
  -h, --help                   Mostrar esta ayuda.

Variables opcionales: APP_USER, SERVICE_NAME, PROCESS_MANAGER.
El código actualizado y el archivo .env deben estar presentes antes de ejecutar.
HELP
}

while (($#)); do
    case "$1" in
        --manager)
            [[ $# -ge 2 ]] || { usage >&2; exit 2; }
            PROCESS_MANAGER="$2"
            shift 2
            ;;
        --skip-install) INSTALL_DEPS=false; shift ;;
        -h|--help) usage; exit 0 ;;
        *) printf 'Opción desconocida: %s\n' "$1" >&2; usage >&2; exit 2 ;;
    esac
done

case "$PROCESS_MANAGER" in
    systemd|supervisor) ;;
    *) printf 'Gestor inválido: %s\n' "$PROCESS_MANAGER" >&2; exit 2 ;;
esac

[[ $EUID -eq 0 ]] || {
    printf 'Ejecuta con sudo para reiniciar el servicio: sudo bash deploy/actualizar.sh\n' >&2
    exit 1
}

PYTHON="${PROJECT_DIR}/venv/bin/python"
APP_USER="${APP_USER:-$(stat -c '%U' "${PROJECT_DIR}/manage.py")}"
[[ "$APP_USER" != root ]] || {
    printf 'Define APP_USER con el usuario que ejecuta la aplicación.\n' >&2
    exit 1
}
id "$APP_USER" >/dev/null
[[ -x "$PYTHON" && -f "${PROJECT_DIR}/.env" ]] || {
    printf 'Falta venv/bin/python o .env. Usa el despliegue inicial para preparar el servidor.\n' >&2
    exit 1
}
command -v runuser >/dev/null
command -v flock >/dev/null
if [[ "$PROCESS_MANAGER" == systemd ]]; then
    command -v systemctl >/dev/null
    systemctl cat "$SERVICE_NAME" >/dev/null
else
    command -v supervisorctl >/dev/null
    supervisorctl status "$SERVICE_NAME" >/dev/null
fi

# Evita actualizaciones simultáneas desde este script.
exec 9>"${PROJECT_DIR}/.deploy.lock"
flock -n 9 || { printf 'Ya hay un despliegue en curso.\n' >&2; exit 1; }
cd -- "$PROJECT_DIR"

STAGE='preparación'
RESTART_ATTEMPTED=false
report_failure() {
    local result=$?
    printf '\nDespliegue interrumpido en: %s (código %s).\n' "$STAGE" "$result" >&2
    if [[ "$RESTART_ATTEMPTED" == false ]]; then
        printf 'No se ha intentado reiniciar el servicio.\n' >&2
    fi
    printf 'Las migraciones ya aplicadas permanecen; no se hace reversión automática.\n' >&2
    if [[ "$PROCESS_MANAGER" == systemd ]]; then
        printf 'Consulta: journalctl -u %s -n 80 --no-pager\n' "$SERVICE_NAME" >&2
    else
        printf 'Consulta: supervisorctl tail %s stderr\n' "$SERVICE_NAME" >&2
    fi
    exit "$result"
}
trap report_failure ERR

# Django lee .env; no se evalúa como código de shell ni se imprimen credenciales.
app_python() {
    runuser -u "$APP_USER" -- "$PYTHON" "$@"
}
django() {
    app_python manage.py "$@"
}

if [[ "$INSTALL_DEPS" == true ]]; then
    STAGE='instalación de dependencias'
    printf '[1/7] Instalando dependencias como %s...\n' "$APP_USER"
    app_python -m pip install -r requirements.txt
fi

STAGE='validación de Django'
printf '[2/7] Validando configuración y migraciones...\n'
django check
django makemigrations --check --dry-run

STAGE='migraciones'
printf '[3/7] Aplicando migraciones...\n'
django migrate --noinput
django migrate --check

STAGE='catálogo SAT'
printf '[4/7] Preparando referencia oficial SAT...\n'
django shell -c 'from catalogo.sat import asegurar_catalogo_sat; asegurar_catalogo_sat()'

STAGE='archivos estáticos'
printf '[5/7] Recopilando archivos estáticos...\n'
django collectstatic --noinput

STAGE='reinicio'
printf '[6/7] Reiniciando %s con %s...\n' "$SERVICE_NAME" "$PROCESS_MANAGER"
RESTART_ATTEMPTED=true
if [[ "$PROCESS_MANAGER" == systemd ]]; then
    systemctl restart "$SERVICE_NAME"
    sleep 3
    systemctl is-active --quiet "$SERVICE_NAME"
else
    supervisorctl restart "$SERVICE_NAME"
    sleep 3
    supervisorctl status "$SERVICE_NAME" | awk '$2 == "RUNNING" {ok=1} END {exit !ok}'
fi

STAGE='verificación final'
printf '[7/7] Despliegue completado; servicio activo.\n'
