# 🐳 Docker Quick Reference

Essential Docker commands for AI Coaching Backend.

---

## 🚀 Quick Start

### Development (One Command)
```bash
./dev-start.sh
```

### Production (One Command)
```bash
sudo ./deploy.sh
```

---

## 📦 Container Management

### Start Services
```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d

# Specific service
docker-compose up -d api

# With rebuild
docker-compose up -d --build
```

### Stop Services
```bash
# Stop all
docker-compose down

# Stop and remove volumes (⚠️ DELETES DATA)
docker-compose down -v

# Production
docker-compose -f docker-compose.prod.yml down
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart api

# Restart without downtime
docker-compose up -d --no-deps --build api
```

### View Status
```bash
# List containers
docker-compose ps

# Detailed info
docker-compose ps -a

# Container stats
docker stats
```

---

## 📋 Logs & Debugging

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api

# Since timestamp
docker-compose logs --since 2024-01-01T10:00:00
```

### Access Container Shell
```bash
# API container
docker-compose exec api bash

# MySQL shell
docker-compose exec mysql mysql -u root -p

# Redis CLI
docker-compose exec redis redis-cli

# As root user
docker-compose exec -u root api bash
```

### Run Commands in Container
```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Create admin user
docker-compose exec api python scripts/create_admin.py

# Check Python version
docker-compose exec api python --version
```

---

## 🗄️ Database Management

### Database Operations
```bash
# Access MySQL
docker-compose exec mysql mysql -u root -p

# Show databases
docker-compose exec mysql mysql -u root -p -e "SHOW DATABASES;"

# Create database
docker-compose exec mysql mysql -u root -p -e "
CREATE DATABASE ai_coaching CHARACTER SET utf8mb4;
"

# Drop database (⚠️ DESTRUCTIVE)
docker-compose exec mysql mysql -u root -p -e "DROP DATABASE ai_coaching;"
```

### Backup & Restore
```bash
# Backup database
docker-compose exec mysql mysqldump -u root -p ai_coaching > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T mysql mysql -u root -p ai_coaching < backup.sql

# Copy backup from container
docker cp ai_coaching_mysql:/backup.sql ./local-backup.sql
```

### Run Migrations
```bash
# Upgrade to latest
docker-compose exec api alembic upgrade head

# Rollback one version
docker-compose exec api alembic downgrade -1

# View migration history
docker-compose exec api alembic history

# Create new migration
docker-compose exec api alembic revision --autogenerate -m "description"
```

---

## 🔍 Monitoring & Health

### Health Checks
```bash
# API health
curl http://localhost:8000/health
curl http://localhost/health  # Production with nginx

# MySQL health
docker-compose exec mysql mysqladmin ping

# Redis health
docker-compose exec redis redis-cli ping

# All services
docker-compose ps
```

### Resource Usage
```bash
# Real-time stats
docker stats

# Disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

### Inspect Container
```bash
# Get container IP
docker inspect ai_coaching_api | grep IPAddress

# View container logs location
docker inspect ai_coaching_api | grep LogPath

# Full container details
docker inspect ai_coaching_api
```

---

## 🏗️ Build & Images

### Build Images
```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build api

# Build without cache
docker-compose build --no-cache

# Production build
docker-compose -f docker-compose.prod.yml build
```

### Manage Images
```bash
# List images
docker images

# Remove unused images
docker image prune -a

# Remove specific image
docker rmi ai-coaching-backend_api

# Tag image
docker tag ai-coaching-backend_api:latest myregistry.com/api:v1
```

### Push to Registry
```bash
# Login to registry
docker login

# Tag for registry
docker tag ai-coaching-backend_api username/ai-coaching-api:latest

# Push to Docker Hub
docker push username/ai-coaching-api:latest
```

---

## 🌐 Networking

### Network Commands
```bash
# List networks
docker network ls

# Inspect network
docker network inspect ai_coaching_network

# Connect container to network
docker network connect ai_coaching_network some_container

# Disconnect
docker network disconnect ai_coaching_network some_container
```

### DNS Resolution
```bash
# Test connectivity between containers
docker-compose exec api ping mysql
docker-compose exec api ping redis

# Test external connectivity
docker-compose exec api ping google.com
```

---

## 💾 Volume Management

### Volume Commands
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect ai-coaching-backend_mysql_data

# Backup volume
docker run --rm -v ai-coaching-backend_mysql_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/mysql_backup.tar.gz /data

# Restore volume
docker run --rm -v ai-coaching-backend_mysql_data:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/mysql_backup.tar.gz -C /data

# Remove volume (⚠️ DELETES DATA)
docker volume rm ai-coaching-backend_mysql_data

# Clean unused volumes
docker volume prune
```

---

## 🔧 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

#### Container Won't Start
```bash
# Check logs
docker-compose logs api

# Check config
docker-compose config

# Recreate container
docker-compose up -d --force-recreate api
```

#### Database Connection Failed
```bash
# Verify MySQL is running
docker-compose ps mysql

# Check MySQL logs
docker-compose logs mysql

# Test connection
docker-compose exec api python -c "
from app.db.session import engine
engine.connect()
print('Connected!')
"
```

#### Out of Disk Space
```bash
# Check disk usage
docker system df

# Clean everything (⚠️ STOPS ALL CONTAINERS)
docker system prune -a --volumes

# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune
```

#### Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Run as root in container
docker-compose exec -u root api bash

# Fix container permissions
docker-compose exec -u root api chown -R appuser:appuser /app
```

---

## ⚡ Performance Tips

### Optimize Images
```bash
# Multi-stage builds (already in Dockerfile.prod)
# Use alpine base images where possible
# Minimize layers
# Use .dockerignore
```

### Resource Limits
```yaml
# In docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Caching
```bash
# Build with BuildKit for better caching
DOCKER_BUILDKIT=1 docker-compose build

# Use cache from registry
docker-compose build --pull
```

---

## 📊 Scaling

### Scale Services
```bash
# Scale API to 4 instances
docker-compose up -d --scale api=4

# Production scaling
docker-compose -f docker-compose.prod.yml up -d --scale api=4

# View scaled services
docker-compose ps
```

### Load Balancing
Nginx automatically load balances when you scale:
```nginx
upstream backend {
    least_conn;  # Load balancing method
    server api:8000;
}
```

---

## 🔒 Security

### Security Best Practices
```bash
# Run as non-root user (already configured)
USER appuser

# Use secrets for sensitive data
docker secret create db_password password.txt

# Scan for vulnerabilities
docker scan ai-coaching-backend_api

# Update base images regularly
docker-compose build --pull
```

### Environment Security
```bash
# Never commit .env files
echo ".env" >> .gitignore

# Use strong passwords
openssl rand -base64 32

# Restrict file permissions
chmod 600 .env.production
```

---

## 📚 Additional Commands

### Cleanup
```bash
# Remove all stopped containers
docker container prune

# Remove all unused images
docker image prune -a

# Remove all unused volumes
docker volume prune

# Remove all unused networks
docker network prune

# Nuclear option (⚠️ REMOVES EVERYTHING)
docker system prune -a --volumes
```

### Export/Import
```bash
# Save image to file
docker save ai-coaching-backend_api > api-image.tar

# Load image from file
docker load < api-image.tar

# Export container filesystem
docker export ai_coaching_api > container.tar
```

---

## 🎯 Production Checklist

- [ ] Use `docker-compose.prod.yml`
- [ ] Set strong passwords in `.env.production`
- [ ] Use production Dockerfile (`Dockerfile.prod`)
- [ ] Enable SSL/TLS
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Configure log rotation
- [ ] Set up automated backups
- [ ] Use secrets management
- [ ] Enable firewall rules
- [ ] Set resource limits
- [ ] Configure health checks
- [ ] Set up CI/CD pipeline

---

## 🆘 Get Help

```bash
# Docker help
docker --help
docker-compose --help

# Command help
docker run --help
docker-compose up --help

# Check Docker version
docker --version
docker-compose --version
```

---

## 📖 Resources

- [Docker Docs](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)

---

**Quick Access:**
- Development: `./dev-start.sh`
- Production: `sudo ./deploy.sh`
- Logs: `docker-compose logs -f api`
- Shell: `docker-compose exec api bash`

Happy Dockering! 🐳
