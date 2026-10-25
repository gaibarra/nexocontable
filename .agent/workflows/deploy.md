---
description: Guía completa de deploy a producción con Nginx, Gunicorn, systemd, Supervisor y Certbot SSL
---

# Deploy - Manual Contable AI

## Arquitectura de producción

```
Cliente → HTTPS (443) → Nginx (reverse proxy) → Unix Socket → Gunicorn → Django
                           ↓
                     Certbot SSL (Let's Encrypt)
                           ↓
                     Archivos estáticos servidos directamente
```

## Prerequisitos en el servidor

1. Ubuntu 22.04+ o Debian 12+
2. PostgreSQL instalado con BD `mconta` creada
3. Dominio apuntando a la IP del servidor (DNS A record)
4. Acceso root o sudo

## Archivos de configuración

Todos están en `deploy/`:

| Archivo | Destino | Propósito |
|---------|---------|-----------|
| `gunicorn.conf.py` | Se lee desde el directorio del proyecto | Workers, timeouts, logging |
| `manual_contable.service` | `/etc/systemd/system/` | Servicio systemd (principal) |
| `manual_contable_supervisor.conf` | `/etc/supervisor/conf.d/` | Supervisor (alternativa/respaldo) |
| `nginx_manual_contable.conf` | `/etc/nginx/sites-available/` | Reverse proxy + SSL + estáticos |
| `deploy.sh` | Se ejecuta una sola vez | Script automatizado de deploy |

## Deploy automático (recomendado)

```bash
# 1. Editar .env con los valores de producción
nano .env
# Cambiar: DEBUG=False, ALLOWED_HOSTS=tudominio.com

# 2. Ejecutar el script
sudo bash deploy/deploy.sh tudominio.com tu@email.com

# 3. Crear superusuario
source venv/bin/activate
python manage.py createsuperuser
```

## Deploy manual (paso a paso)

### 1. Instalar paquetes
```bash
sudo apt update
sudo apt install -y python3 python3-venv nginx certbot python3-certbot-nginx supervisor postgresql-client libpq-dev
```

### 2. Preparar la aplicación
```bash
cd /home/gaibarra/manual_contable_ai
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn whitenoise
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py createsuperuser
```

### 3. Configurar Gunicorn + systemd
```bash
sudo mkdir -p /var/log/gunicorn /run/gunicorn
sudo chown www-data:www-data /var/log/gunicorn /run/gunicorn
sudo cp deploy/manual_contable.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable manual_contable
sudo systemctl start manual_contable
sudo systemctl status manual_contable
```

### 4. Configurar Nginx
```bash
# Copiar config (reemplazar tudominio.com)
sudo sed 's/tudominio.com/tudominio-real.com/g' deploy/nginx_manual_contable.conf \
    > /etc/nginx/sites-available/manual_contable
sudo ln -sf /etc/nginx/sites-available/manual_contable /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### 5. SSL con Certbot
```bash
sudo certbot --nginx -d tudominio.com -d www.tudominio.com --email tu@email.com --agree-tos
sudo systemctl enable certbot.timer
```

## Comandos útiles post-deploy

```bash
# ── Estado ──
sudo systemctl status manual_contable
sudo systemctl status nginx

# ── Reiniciar ──
sudo systemctl restart manual_contable
sudo systemctl reload nginx

# ── Logs en vivo ──
sudo journalctl -u manual_contable -f
sudo tail -f /var/log/nginx/manual_contable_error.log
sudo tail -f /var/log/gunicorn/manual_contable_error.log

# ── Desplegar código ya actualizado ──
cd /home/gaibarra/manual_contable_ai
sudo bash deploy/deploy.sh --update
# Con Supervisor: agregar --manager supervisor

# ── SSL ──
sudo certbot renew --dry-run    # Probar renovación
sudo certbot certificates       # Ver certificados activos

# ── Supervisor (si lo usas como alternativa) ──
sudo supervisorctl status manual_contable
sudo supervisorctl restart manual_contable
sudo supervisorctl tail -f manual_contable
```

## Cambiar de systemd a Supervisor (o viceversa)

```bash
# De systemd a Supervisor:
sudo systemctl stop manual_contable
sudo systemctl disable manual_contable
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start manual_contable

# De Supervisor a systemd:
sudo supervisorctl stop manual_contable
sudo systemctl enable manual_contable
sudo systemctl start manual_contable
```

## Notas importantes

- **Timeout alto** (120s): Las llamadas a OpenAI pueden tardar, especialmente con `max_tokens=8000`
- **Workers**: auto-calculados como `(2 × CPU cores) + 1`
- **Socket Unix**: Más rápido que TCP localhost para comunicación Nginx↔Gunicorn
- **WhiteNoise**: Sirve estáticos en producción sin necesidad de `collectstatic` con Nginx (pero Nginx es más eficiente)
- **Certbot timer**: Renueva SSL automáticamente antes de que expire
