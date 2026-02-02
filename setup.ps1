# ASR Middleware - Quick Setup Script (Windows)
# This script sets up the development environment

Write-Host "🚀 Setting up ASR Middleware..." -ForegroundColor Green

# Check if uv is installed
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "❌ uv is not installed. Please install it first:" -ForegroundColor Red
    Write-Host "   powershell -c `"irm https://astral.sh/uv/install.ps1 | iex`"" -ForegroundColor Yellow
    exit 1
}

# Check if PostgreSQL is running
if (-not (Get-Command psql -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️  PostgreSQL client not found. Make sure PostgreSQL is installed and running." -ForegroundColor Yellow
}

# Check if Redis is running
if (-not (Get-Command redis-cli -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️  Redis client not found. Make sure Redis is installed and running." -ForegroundColor Yellow
}

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
uv sync

# Create .env if it doesn't exist
if (-not (Test-Path .env)) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Cyan
    Copy-Item .env.example .env
    Write-Host "⚠️  Please edit .env file with your configuration!" -ForegroundColor Yellow
}

# Create media directory
Write-Host "📁 Creating media directory..." -ForegroundColor Cyan
if (-not (Test-Path media)) {
    New-Item -ItemType Directory -Path media | Out-Null
}

# Initialize database
Write-Host "🗄️  Initializing database..." -ForegroundColor Cyan
uv run python init_db.py create

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env file with your API keys and configuration"
Write-Host "2. Make sure PostgreSQL and Redis are running"
Write-Host "3. Start the FastAPI server:"
Write-Host "   uv run python run.py" -ForegroundColor Yellow
Write-Host "4. In another terminal, start Celery worker:"
Write-Host "   uv run celery -A celery_worker worker --loglevel=info" -ForegroundColor Yellow
Write-Host ""
Write-Host "📚 API documentation will be available at: http://localhost:8000/docs" -ForegroundColor Green
