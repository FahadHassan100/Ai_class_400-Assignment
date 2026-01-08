# FastAPI Deployment

## Table of Contents
- [Production Server](#production-server)
- [Docker](#docker)
- [Docker Compose](#docker-compose)
- [Environment Variables](#environment-variables)
- [HTTPS and Reverse Proxy](#https-and-reverse-proxy)
- [Cloud Deployment](#cloud-deployment)
- [Health Checks](#health-checks)

---

## Production Server

### Uvicorn (single process)
```bash
pip install uvicorn[standard]
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Gunicorn + Uvicorn (multiple workers)
```bash
pip install gunicorn uvicorn[standard]
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

Workers = (2 x CPU cores) + 1

---

## Docker

### Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ./app ./app

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Multi-stage build (smaller image)
```dockerfile
FROM python:3.12-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY ./app ./app

ENV PATH=/root/.local/bin:$PATH

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build and run
```bash
docker build -t myapp .
docker run -d -p 8000:8000 --name myapp myapp
```

---

## Docker Compose

### docker-compose.yml
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d mydb"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  postgres_data:
```

### Commands
```bash
docker-compose up -d           # Start
docker-compose down            # Stop
docker-compose logs -f api     # View logs
docker-compose exec api bash   # Shell into container
```

---

## Environment Variables

### .env file
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
SECRET_KEY=your-super-secret-key
DEBUG=false
ALLOWED_HOSTS=example.com,www.example.com
```

### Config with Pydantic Settings
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = False
    allowed_hosts: list[str] = ["localhost"]

    model_config = {"env_file": ".env"}

@lru_cache
def get_settings():
    return Settings()

# Usage
settings = get_settings()
print(settings.database_url)
```

### In FastAPI
```python
from fastapi import Depends

@app.get("/info")
def info(settings: Settings = Depends(get_settings)):
    return {"debug": settings.debug}
```

---

## HTTPS and Reverse Proxy

### Nginx config
```nginx
server {
    listen 80;
    server_name example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Trust proxy headers in FastAPI
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["example.com", "*.example.com"]
)
```

---

## Cloud Deployment

### Railway / Render / Fly.io
```toml
# fly.toml
app = "myapp"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true

[env]
  PORT = "8000"
```

### AWS Lambda (with Mangum)
```bash
pip install mangum
```

```python
from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello from Lambda"}

handler = Mangum(app)
```

---

## Health Checks

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not ready", "database": str(e)}

@app.get("/health/live")
def liveness_check():
    return {"status": "alive"}
```

### Docker healthcheck
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```
