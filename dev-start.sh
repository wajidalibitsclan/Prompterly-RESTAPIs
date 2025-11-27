#!/bin/bash
# Quick start script for development

echo "🚀 Starting AI Coaching Backend (Development)"
echo "=============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env from example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your API keys"
fi

# Start services
echo "🐳 Starting Docker containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run migrations
echo "📊 Running database migrations..."
docker-compose exec -T api alembic upgrade head || echo "⚠️  Migrations may need manual intervention"

echo ""
echo "✅ Development environment is ready!"
echo ""
echo "📍 Access Points:"
echo "  API:        http://localhost:8000"
echo "  API Docs:   http://localhost:8000/docs"
echo "  ReDoc:      http://localhost:8000/redoc"
echo "  MySQL:      localhost:3306"
echo "  Redis:      localhost:6379"
echo ""
echo "📝 Useful Commands:"
echo "  View logs:  docker-compose logs -f"
echo "  Stop:       docker-compose down"
echo "  Restart:    docker-compose restart"
echo "  Shell:      docker-compose exec api bash"
echo ""
