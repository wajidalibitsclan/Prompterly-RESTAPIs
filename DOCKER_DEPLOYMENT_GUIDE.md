# 🐳 Docker Deployment Guide

Complete guide for deploying the AI Coaching backend with Docker.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Development Setup](#development-setup)
3. [Production Setup](#production-setup)
4. [Container Architecture](#container-architecture)
5. [Configuration](#configuration)
6. [Deployment Options](#deployment-options)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Development (30 seconds)

```bash
# Clone and navigate
cd ai-coaching-backend

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# API available at: http://localhost:8000
# Docs at: http://localhost:8000/docs
```

### Production (2 minutes)

```bash
# Copy production environment
cp .env.production.example .env.production

# Edit with your values
nano .env.production

# Build and start
docker-compose -f docker-compose.prod.yml up -d

# Check health
curl http://localhost/health
```

---

## 💻 Development Setup

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

### Step-by-Step Development Setup

#### 1. Clone Repository

```bash
git clone <your-repo-url>
cd ai-coaching-backend
```

#### 2. Configure Environment

```bash
# Copy example environment
cp .env.example .env

# Edit with your API keys
nano .env
```

Required variables:
```env
DATABASE_URL=mysql+pymysql://root:password@mysql:3306/ai_coaching
OPENAI_API_KEY=sk-your_key
STRIPE_SECRET_KEY=sk_test_your_key
MAIL_SERVER=smtp.gmail.com
```

#### 3. Start Development Services

```bash
# Start all containers
docker-compose up -d

# View logs
docker-compose logs -f

# Stop when done
docker-compose down
```

#### 4. Run Database Migrations

```bash
# Access API container
docker-compose exec api bash

# Run migrations
alembic upgrade head

# Exit container
exit
```

#### 5. Create Test Data (Optional)

```bash
docker-compose exec api python -c "
from app.db.session import get_db
from app.db.models.user import User
from app.core.security import get_password_hash

db = next(get_db())
admin = User(
    email='admin@example.com',
    password_hash=get_password_hash('admin123'),
    name='Admin User',
    role='admin'
)
db.add(admin)
db.commit()
print('Admin created!')
"
```

### Development Services

After `docker-compose up -d`:

- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **MySQL**: localhost:3306
- **Redis**: localhost:6379

### Hot Reload

Code changes auto-reload in development mode:

```yaml
# docker-compose.yml includes:
volumes:
  - ./app:/app/app  # Live code sync
command: uvicorn app.main:app --reload
```

---

## 🏭 Production Setup

### Production Architecture

```
┌─────────────┐
│   Nginx     │ ← Reverse proxy, SSL, rate limiting
│   (Port 80) │
└──────┬──────┘
       │
┌──────▼──────┐
│  FastAPI    │ ← 4 Gunicorn workers
│   (Port     │
│    8000)    │
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
┌──▼──┐ ┌──▼──┐
│MySQL│ │Redis│
└─────┘ └─────┘
```

### Production Deployment Steps

#### 1. Server Requirements

- **VPS/Cloud**: DigitalOcean, AWS EC2, Linode
- **RAM**: 4GB minimum (8GB recommended)
- **CPU**: 2 cores minimum
- **Disk**: 50GB SSD
- **OS**: Ubuntu 22.04 LTS

#### 2. Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

#### 3. Configure Production Environment

```bash
# Copy production template
cp .env.production.example .env.production

# Edit with production values
nano .env.production
```

**Critical production settings:**

```env
# Use strong passwords!
MYSQL_ROOT_PASSWORD=<generate_32_char_random>
MYSQL_PASSWORD=<generate_32_char_random>
REDIS_PASSWORD=<generate_32_char_random>
JWT_SECRET_KEY=<generate_64_char_random>

# Use production keys
STRIPE_SECRET_KEY=sk_live_...
OPENAI_API_KEY=sk-...

# Set production URLs
CORS_ORIGINS=https://yourdomain.com
GOOGLE_REDIRECT_URI=https://yourdomain.com/api/v1/auth/google/callback
```

#### 4. Generate Strong Passwords

```bash
# Generate secure random strings
openssl rand -base64 32  # For passwords
openssl rand -hex 32     # For JWT secret
```

#### 5. Build Production Images

```bash
# Build with production Dockerfile
docker-compose -f docker-compose.prod.yml build

# Or build specific service
docker-compose -f docker-compose.prod.yml build api
```

#### 6. Start Production Services

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check status
docker-compose -f docker-compose.prod.yml ps
```

#### 7. Run Database Migrations

```bash
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

#### 8. Verify Deployment

```bash
# Health check
curl http://localhost/health

# API docs (should work)
curl http://localhost/docs
```

---

## 🏗️ Container Architecture

### Services Overview

#### 1. **nginx** (Reverse Proxy)
- Routes requests to API
- SSL termination
- Rate limiting
- Static file serving
- Load balancing (when scaled)

#### 2. **api** (FastAPI Application)
- Handles all API requests
- 4 Gunicorn workers
- Non-root user for security
- Health checks enabled

#### 3. **mysql** (Database)
- Persistent data storage
- Automated backups (configure)
- Health checks
- Custom configuration

#### 4. **redis** (Cache & Sessions)
- Session storage
- Rate limiting
- Cache layer
- Password protected

#### 5. **worker** (Background Jobs)
- Time capsule unlocking
- Email sending
- Scheduled tasks

### Container Networking

```
ai_coaching_network (bridge)
├── nginx (80, 443)
├── api (8000)
├── mysql (3306)
├── redis (6379)
└── worker
```

All containers communicate via internal network.
Only nginx exposes external ports.

---

## ⚙️ Configuration

### Environment Files

**Development**: `.env`
```env
DEBUG=True
ENVIRONMENT=development
DATABASE_URL=mysql+pymysql://root:password@mysql:3306/ai_coaching
```

**Production**: `.env.production`
```env
DEBUG=False
ENVIRONMENT=production
DATABASE_URL=mysql+pymysql://user:strongpass@mysql:3306/ai_coaching
```

### Docker Compose Files

**Development**: `docker-compose.yml`
- Hot reload enabled
- Development settings
- Exposed ports for debugging

**Production**: `docker-compose.prod.yml`
- Optimized for performance
- Security hardened
- Health checks
- Resource limits
- Multiple replicas

### Nginx Configuration

Located in `nginx/nginx.conf`:

- Rate limiting: 10 req/s
- Max upload: 20MB
- Timeouts: 60s
- Gzip compression
- Security headers

Edit for custom needs:
```bash
nano nginx/nginx.conf
docker-compose -f docker-compose.prod.yml restart nginx
```

### MySQL Configuration

Create `mysql/conf.d/custom.cnf`:

```ini
[mysqld]
max_connections = 200
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M
```

---

## 🚢 Deployment Options

### Option 1: DigitalOcean Droplet

```bash
# Create droplet (4GB RAM, $24/mo)
# SSH into droplet
ssh root@your_droplet_ip

# Clone repo
git clone <your-repo> && cd ai-coaching-backend

# Follow production setup steps above

# Configure firewall
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw enable
```

### Option 2: AWS EC2

```bash
# Launch t3.medium instance (Ubuntu 22.04)
# Security group: Allow 80, 443, 22

# SSH and setup
ssh -i key.pem ubuntu@ec2-ip
git clone <your-repo> && cd ai-coaching-backend

# Follow production setup
# Use RDS for MySQL (recommended)
# Use ElastiCache for Redis (recommended)
```

### Option 3: Docker Swarm (Multi-node)

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml aicoach

# Scale API
docker service scale aicoach_api=4

# View services
docker service ls
```

### Option 4: Kubernetes (Advanced)

See `k8s/` directory for manifests (TODO).

---

## 📊 Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api

# Production
docker-compose -f docker-compose.prod.yml logs -f
```

### Container Stats

```bash
# Real-time stats
docker stats

# Specific container
docker stats ai_coaching_api
```

### Health Checks

```bash
# Check all services
docker-compose ps

# API health
curl http://localhost/health

# MySQL health
docker-compose exec mysql mysqladmin ping

# Redis health
docker-compose exec redis redis-cli ping
```

### Prometheus Metrics (Optional)

API exposes metrics at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

---

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs api

# Common issues:
# 1. Port already in use
sudo lsof -i :8000
sudo kill -9 <PID>

# 2. Database connection failed
docker-compose logs mysql

# 3. Environment variables missing
docker-compose config
```

### Database Connection Issues

```bash
# Test MySQL connection
docker-compose exec mysql mysql -u root -p

# Check if database exists
docker-compose exec mysql mysql -u root -p -e "SHOW DATABASES;"

# Recreate database
docker-compose exec mysql mysql -u root -p -e "
DROP DATABASE IF EXISTS ai_coaching;
CREATE DATABASE ai_coaching CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
"

# Run migrations
docker-compose exec api alembic upgrade head
```

### Rebuild Containers

```bash
# Stop all
docker-compose down

# Remove volumes (⚠️ DELETES DATA)
docker-compose down -v

# Rebuild
docker-compose build --no-cache

# Start fresh
docker-compose up -d
```

### Permission Issues

```bash
# If files owned by root
sudo chown -R $USER:$USER .

# Container permission issues
docker-compose exec -u root api chown -R appuser:appuser /app
```

### Out of Memory

```bash
# Check memory usage
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings > Resources > Memory > 4GB+

# Or add to docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 2G
```

### SSL Certificate Issues

```bash
# Generate self-signed cert (testing)
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem

# For production, use Let's Encrypt:
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy to nginx directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
```

---

## 🔧 Maintenance

### Backup Database

```bash
# Backup
docker-compose exec mysql mysqldump -u root -p ai_coaching > backup.sql

# Restore
docker-compose exec -T mysql mysql -u root -p ai_coaching < backup.sql
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild containers
docker-compose -f docker-compose.prod.yml build

# Restart with zero downtime
docker-compose -f docker-compose.prod.yml up -d --no-deps --build api

# Run new migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### Scaling

```bash
# Scale API to 4 instances
docker-compose -f docker-compose.prod.yml up -d --scale api=4

# Nginx will load balance automatically
```

---

## 📚 Additional Resources

- [Docker Docs](https://docs.docker.com/)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Nginx Docs](https://nginx.org/en/docs/)

---

## 🎉 Success!

Your AI Coaching backend is now Dockerized and ready for deployment!

**Next Steps:**
1. ✅ Configure domain name
2. ✅ Set up SSL certificate
3. ✅ Configure monitoring (Sentry, Prometheus)
4. ✅ Set up automated backups
5. ✅ Configure CI/CD pipeline

Happy deploying! 🚀
