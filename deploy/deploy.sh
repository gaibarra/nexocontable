#!/bin/bash
# ======================================================
# Script de Deploy - Manual Contable AI
# ======================================================
# Actualización: sudo bash deploy/deploy.sh --update
# Instalación inicial: sudo bash deploy/deploy.sh manualcontable.online tu@email.com
#
# Requisitos previos:
#   - Ubuntu 22.04+ / Debian 12+
#   - PostgreSQL instalado y BD 'mconta' creada
#   - El archivo .env configurado correctamente
#   - DNS apuntando a la IP del servidor
# ======================================================

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${1:-}" == --update ]]; then
    shift
    exec bash "${SCRIPT_DIR}/actualizar.sh" "$@"
fi
if [[ "${1:-}" == --help || "${1:-}" == -h ]]; then
    printf 'Actualizar instalación: sudo bash deploy/deploy.sh --update [--manager systemd|supervisor] [--skip-install]\n'
    printf 'Instalación inicial: sudo bash deploy/deploy.sh DOMINIO EMAIL\n'
    exit 0
fi

# ── Colores ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ── Variables ──
DOMAIN="${1:-}"
EMAIL="${2:-}"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${PROJECT_DIR}/venv"
DEPLOY_DIR="${PROJECT_DIR}/deploy"
USER_APP="gaibarra"

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo -e "${RED}❌ Uso: sudo bash deploy.sh manualcontable.online tu@email.com${NC}"
    exit 1
fi

echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo -e "${BLUE}  Deploy: Manual Contable AI${NC}"
echo -e "${BLUE}  Dominio: ${DOMAIN}${NC}"
echo -e "${BLUE}  Email:   ${EMAIL}${NC}"
echo -e "${BLUE}══════════════════════════════════════════${NC}"

# ── Paso 1: Instalar paquetes del sistema ──
echo -e "\n${YELLOW}[1/9] Instalando paquetes del sistema...${NC}"
apt update -qq
apt install -y -qq python3 python3-venv python3-pip \
    nginx certbot python3-certbot-nginx \
    supervisor \
    postgresql-client \
    libpq-dev > /dev/null 2>&1
echo -e "${GREEN}✅ Paquetes instalados${NC}"

# ── Paso 2: Crear directorios de logs ──
echo -e "\n${YELLOW}[2/9] Creando directorios...${NC}"
mkdir -p /var/log/gunicorn
mkdir -p /var/log/supervisor
mkdir -p /run/gunicorn
mkdir -p /var/www/certbot
mkdir -p "${PROJECT_DIR}/staticfiles"
mkdir -p "${PROJECT_DIR}/media"

chown -R www-data:www-data /var/log/gunicorn
chown -R www-data:www-data /run/gunicorn
chown -R ${USER_APP}:www-data "${PROJECT_DIR}"
chmod -R 750 "${PROJECT_DIR}"
echo -e "${GREEN}✅ Directorios creados${NC}"

# ── Paso 3: Instalar dependencias Python ──
echo -e "\n${YELLOW}[3/9] Instalando dependencias Python...${NC}"
cd "${PROJECT_DIR}"
if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
fi
source "${VENV_DIR}/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet gunicorn whitenoise
echo -e "${GREEN}✅ Dependencias instaladas${NC}"

# ── Paso 4: Colectar archivos estáticos ──
echo -e "\n${YELLOW}[4/9] Colectando archivos estáticos...${NC}"
python manage.py collectstatic --noinput --clear > /dev/null 2>&1
echo -e "${GREEN}✅ Estáticos colectados${NC}"

# ── Paso 5: Ejecutar migraciones ──
echo -e "\n${YELLOW}[5/9] Ejecutando migraciones...${NC}"
python manage.py migrate --noinput
python manage.py migrate --check
python manage.py shell -c 'from catalogo.sat import asegurar_catalogo_sat; asegurar_catalogo_sat()'
echo -e "${GREEN}✅ Migraciones aplicadas${NC}"

# ── Paso 6: Configurar systemd ──
echo -e "\n${YELLOW}[6/9] Configurando systemd...${NC}"
cp "${DEPLOY_DIR}/manual_contable.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable manual_contable
systemctl restart manual_contable
sleep 2

if systemctl is-active --quiet manual_contable; then
    echo -e "${GREEN}✅ Gunicorn (systemd) activo${NC}"
else
    echo -e "${RED}❌ Error con Gunicorn. Revisa: journalctl -u manual_contable -n 50${NC}"
    exit 1
fi

# ── Paso 7: Configurar Supervisor (como respaldo/alternativa) ──
echo -e "\n${YELLOW}[7/9] Configurando Supervisor...${NC}"
cp "${DEPLOY_DIR}/manual_contable_supervisor.conf" /etc/supervisor/conf.d/manual_contable.conf
# NOTA: Por defecto usamos systemd. Si prefieres Supervisor:
#   1. sudo systemctl stop manual_contable && sudo systemctl disable manual_contable
#   2. sudo supervisorctl reread && sudo supervisorctl update
#   3. sudo supervisorctl start manual_contable
echo -e "${GREEN}✅ Supervisor configurado (en standby — systemd es el principal)${NC}"

# ── Paso 8: Configurar Nginx ──
echo -e "\n${YELLOW}[8/9] Configurando Nginx...${NC}"

# Reemplazar dominio en la config
sed "s/manualcontable.online/${DOMAIN}/g" "${DEPLOY_DIR}/nginx_manual_contable.conf" \
    > /etc/nginx/sites-available/manual_contable

# Activar sitio
ln -sf /etc/nginx/sites-available/manual_contable /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Primero sin SSL para que Certbot funcione
# Crear config temporal solo HTTP
cat > /etc/nginx/sites-available/manual_contable <<NGINX_TEMP
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} www.${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location /static/ {
        alias ${PROJECT_DIR}/staticfiles/;
    }

    location / {
        proxy_pass http://unix:/home/gaibarra/manual_contable_ai/manual_contable.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
    }
}
NGINX_TEMP

nginx -t && systemctl reload nginx
echo -e "${GREEN}✅ Nginx configurado (HTTP)${NC}"

# ── Paso 9: Obtener certificado SSL con Certbot ──
echo -e "\n${YELLOW}[9/9] Obteniendo certificado SSL con Certbot...${NC}"
certbot --nginx \
    -d "${DOMAIN}" \
    -d "www.${DOMAIN}" \
    --email "${EMAIL}" \
    --agree-tos \
    --no-eff-email \
    --redirect

# Restaurar config completa de Nginx con SSL
sed "s/manualcontable.online/${DOMAIN}/g" "${DEPLOY_DIR}/nginx_manual_contable.conf" \
    > /etc/nginx/sites-available/manual_contable

nginx -t && systemctl reload nginx

# Verificar renovación automática
systemctl enable certbot.timer
echo -e "${GREEN}✅ SSL configurado y renovación automática activa${NC}"

# ── Resumen final ──
echo -e "\n${BLUE}══════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ ¡DEPLOY COMPLETADO!${NC}"
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo -e "  🌐 URL:       https://${DOMAIN}"
echo -e "  🔧 Admin:     https://${DOMAIN}/admin/"
echo -e "  📋 Logs app:  journalctl -u manual_contable -f"
echo -e "  📋 Logs nginx: tail -f /var/log/nginx/manual_contable_*.log"
echo -e "  📋 Logs gunicorn: tail -f /var/log/gunicorn/manual_contable_*.log"
echo -e ""
echo -e "  ${YELLOW}⚠️  No olvides:${NC}"
echo -e "  1. Crear superusuario: python manage.py createsuperuser"
echo -e "  2. Verificar .env tiene DEBUG=False"
echo -e "  3. Verificar ALLOWED_HOSTS incluye ${DOMAIN}"
echo -e "${BLUE}══════════════════════════════════════════${NC}"
