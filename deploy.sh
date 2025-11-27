#!/bin/bash
# Production deployment script for AI Coaching Backend

set -e  # Exit on error

echo "🚀 AI Coaching Backend - Production Deployment"
echo "=============================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed!${NC}"
    echo "Install with: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed${NC}"

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo -e "${YELLOW}⚠ .env.production not found!${NC}"
    echo "Creating from template..."
    cp .env.production.example .env.production
    echo -e "${RED}Please edit .env.production with your values and run again${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment file found${NC}"

# Create necessary directories
mkdir -p nginx/ssl
mkdir -p mysql/init
mkdir -p logs

echo -e "${GREEN}✓ Directories created${NC}"

# Ask for confirmation
echo ""
echo -e "${YELLOW}This will:${NC}"
echo "1. Build production Docker images"
echo "2. Start all services (nginx, api, mysql, redis, worker)"
echo "3. Run database migrations"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Stop existing containers
echo ""
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down || true

# Build images
echo ""
echo "🏗️ Building Docker images..."
docker-compose -f docker-compose.prod.yml build

# Start services
echo ""
echo "🚀 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for MySQL to be ready
echo ""
echo "⏳ Waiting for MySQL to be ready..."
sleep 10

# Run database migrations
echo ""
echo "📊 Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T api alembic upgrade head

# Check service health
echo ""
echo "🏥 Checking service health..."
sleep 5

# Test API health
if curl -f http://localhost/health &> /dev/null; then
    echo -e "${GREEN}✓ API is healthy${NC}"
else
    echo -e "${RED}✗ API health check failed${NC}"
    echo "Check logs with: docker-compose -f docker-compose.prod.yml logs api"
fi

# Show running containers
echo ""
echo "📦 Running containers:"
docker-compose -f docker-compose.prod.yml ps

# Show useful commands
echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Useful commands:"
echo "  View logs:     docker-compose -f docker-compose.prod.yml logs -f"
echo "  Stop services: docker-compose -f docker-compose.prod.yml down"
echo "  Restart:       docker-compose -f docker-compose.prod.yml restart"
echo ""
echo "Access points:"
echo "  API:           http://localhost/api/v1/"
echo "  API Docs:      http://localhost/docs"
echo "  Health Check:  http://localhost/health"
echo ""
echo -e "${YELLOW}⚠ Don't forget to:${NC}"
echo "  1. Configure your domain DNS to point to this server"
echo "  2. Set up SSL certificates (Let's Encrypt recommended)"
echo "  3. Configure firewall (ufw allow 80,443,22/tcp)"
echo "  4. Set up monitoring and backups"
echo ""
