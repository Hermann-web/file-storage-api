# 🚀 Deployment Guide

This guide covers multiple deployment options for the Simple File Storage API, from development to production.

## 📋 Table of Contents

1. [Development Deployment](#development-deployment)
2. [Production Deployment](#production-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Monitoring & Maintenance](#monitoring--maintenance)

---

## 🛠️ Development Deployment

### Option 1: Using uv (Recommended)

**Install uv** (if not installed):
```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

**Run the application**:
```bash
# Install dependencies and run
uv pip install -r requirements.txt
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or one-liner for development
uv run --with fastapi --with uvicorn uvicorn main:app --reload
```

### Option 2: Direct uvicorn

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# With auto-reload and debug logging
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### Option 3: With micromamba

```bash
# Using your existing setup
micromamba run uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or create a dedicated environment
micromamba create -n fileapi python=3.11
micromamba activate fileapi
uv pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🏭 Production Deployment

### Option 1: Gunicorn with Uvicorn Workers (Recommended)

**Install Gunicorn**:
```bash
pip install gunicorn
# or
uv pip install gunicorn
```

**Basic Production Setup**:
```bash
# Single worker (for small loads)
gunicorn main:app -w 1 -k uvicorn.workers.UnicornWorker --bind 0.0.0.0:8000

# Multiple workers (recommended)
gunicorn main:app -w 4 -k uvicorn.workers.UnicornWorker --bind 0.0.0.0:8000

# With configuration file
gunicorn main:app -c gunicorn.conf.py
```

**Create `gunicorn.conf.py`**:
```python
# gunicorn.conf.py
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UnicornWorker"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, with up to 50% jitter
max_requests = 1000
max_requests_jitter = 50

# Logging
errorlog = "-"
loglevel = "info"
accesslog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "simple-file-storage-api"

# Server mechanics
preload_app = True
```

### Option 2: Direct Uvicorn (Simple Production)

```bash
# Basic production
uvicorn main:app --host 0.0.0.0 --port 8000

# With multiple workers (uvicorn 0.11.0+)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# With SSL (if you have certificates)
uvicorn main:app --host 0.0.0.0 --port 443 --ssl-keyfile key.pem --ssl-certfile cert.pem
```

### Option 3: Hypercorn (Alternative ASGI server)

```bash
pip install hypercorn
hypercorn main:app --bind 0.0.0.0:8000 --workers 4
```

---

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY main.py .

# Create upload directory
RUN mkdir -p files

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UnicornWorker", "--bind", "0.0.0.0:8000"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  file-api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./files:/app/files
      - ./files.db:/app/files.db
    environment:
      - PYTHONPATH=/app
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: Add nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - file-api
    restart: unless-stopped
```

**Build and run**:
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## ☁️ Cloud Deployment

### Option 1: Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

Add `railway.toml`:
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "gunicorn main:app -w 4 -k uvicorn.workers.UnicornWorker --bind 0.0.0.0:$PORT"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### Option 2: Render

Create `render.yaml`:
```yaml
services:
  - type: web
    name: file-storage-api
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "gunicorn main:app -w 4 -k uvicorn.workers.UnicornWorker --bind 0.0.0.0:$PORT"
    healthCheckPath: "/health"
    envVars:
      - key: PYTHON_VERSION
        value: "3.11"
```

### Option 3: Heroku

Create `Procfile`:
```
web: gunicorn main:app -w 4 -k uvicorn.workers.UnicornWorker --bind 0.0.0.0:$PORT
```

Create `runtime.txt`:
```
python-3.11.0
```

Deploy:
```bash
heroku create your-app-name
git push heroku main
```

### Option 4: DigitalOcean App Platform

Create `.do/app.yaml`:
```yaml
name: file-storage-api
services:
- name: api
  source_dir: /
  github:
    repo: your-username/your-repo
    branch: main
  run_command: gunicorn main:app -w 4 -k uvicorn.workers.UnicornWorker --bind 0.0.0.0:$PORT
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  health_check:
    http_path: /health
  routes:
  - path: /
```

---

## ⚙️ Environment Configuration

### Environment Variables

Create `.env` file:
```bash
# Database
DATABASE_URL=sqlite:///./files.db

# File Storage
UPLOAD_DIR=files
MAX_FILE_SIZE=10485760  # 10MB in bytes

# CORS
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]

# Security
SECRET_KEY=your-secret-key-here
```

### Production Settings

Create `config.py`:
```python
import os
from pathlib import Path

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./files.db")

# File storage
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "files"))
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else ["*"]

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
WORKERS = int(os.getenv("WORKERS", 4))
```

### Systemd Service (Linux)

Create `/etc/systemd/system/file-api.service`:
```ini
[Unit]
Description=File Storage API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/file-api
Environment=PATH=/opt/file-api/venv/bin
ExecStart=/opt/file-api/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UnicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable file-api
sudo systemctl start file-api
sudo systemctl status file-api
```

---

## 📊 Monitoring & Maintenance

### Nginx Reverse Proxy

Create `nginx.conf`:
```nginx
events {
    worker_connections 1024;
}

http {
    upstream app {
        server file-api:8000;
    }

    server {
        listen 80;
        client_max_body_size 10M;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /health {
            proxy_pass http://app/health;
        }
    }
}
```

### Health Monitoring

```bash
# Simple health check script
#!/bin/bash
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy"
    exit 1
fi
```

### Log Rotation

```bash
# Add to /etc/logrotate.d/file-api
/var/log/file-api/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    copytruncate
}
```

### Backup Script

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf "backup_${DATE}.tar.gz" files/ files.db
```

---

## 🔧 Troubleshooting

### Common Issues

**Port already in use**:
```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

**Permission denied on files/ directory**:
```bash
sudo chown -R $(whoami):$(whoami) files/
chmod 755 files/
```

**Database locked**:
```bash
# Check for other processes
lsof files.db
# Or backup and recreate
cp files.db files.db.backup
rm files.db
```

**High memory usage**:
- Reduce number of workers
- Add worker recycling in gunicorn config
- Monitor with `htop` or `ps aux`

### Performance Tuning

```python
# Add to main.py for production
import uvicorn.config
uvicorn.config.LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"
