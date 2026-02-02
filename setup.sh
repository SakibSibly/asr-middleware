#!/bin/bash

# ASR Middleware - Quick Setup Script
# This script sets up the development environment

echo "🚀 Setting up ASR Middleware..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if PostgreSQL is running
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL client not found. Make sure PostgreSQL is installed and running."
fi

# Check if Redis is running
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️  Redis client not found. Make sure Redis is installed and running."
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration!"
fi

# Create media directory
echo "📁 Creating media directory..."
mkdir -p media

# Initialize database
echo "🗄️  Initializing database..."
uv run python init_db.py create

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys and configuration"
echo "2. Make sure PostgreSQL and Redis are running"
echo "3. Start the FastAPI server:"
echo "   uv run python run.py"
echo "4. In another terminal, start Celery worker:"
echo "   uv run celery -A celery_worker worker --loglevel=info"
echo ""
echo "📚 API documentation will be available at: http://localhost:8000/docs"
