# SMEFlow Development Environment Setup Script
# Run this script to set up the development environment

Write-Host "🚀 Setting up SMEFlow development environment..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop" -ForegroundColor Red
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "📚 Installing dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# Copy environment file
if (-not (Test-Path ".env")) {
    Write-Host "⚙️ Creating .env file..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "📝 Please update .env with your actual configuration values" -ForegroundColor Cyan
}

# Start Docker services
Write-Host "🐳 Starting Docker services..." -ForegroundColor Yellow
docker-compose -f docker-compose.dev.yml up -d postgres redis keycloak livekit

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Run database migrations
Write-Host "🗄️ Running database migrations..." -ForegroundColor Yellow
alembic upgrade head

Write-Host "✅ Development environment setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Update .env file with your API keys" -ForegroundColor White
Write-Host "2. Run 'python -m smeflow.main' to start the API server" -ForegroundColor White
Write-Host "3. Visit http://localhost:8000/docs for API documentation" -ForegroundColor White
Write-Host "4. Visit http://localhost:8080 for Keycloak admin (admin/admin)" -ForegroundColor White
