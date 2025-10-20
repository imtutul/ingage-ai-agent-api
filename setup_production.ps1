# Quick Production Setup Script for Windows PowerShell

Write-Host "🚀 Setting up Fabric Data Agent API for Production" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (Test-Path ".venv") {
    Write-Host "✅ Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install production dependencies
Write-Host "Installing production dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host ""
Write-Host "✅ Dependencies installed successfully!" -ForegroundColor Green
Write-Host ""

# Test Redis connection
Write-Host "Testing Redis connection..." -ForegroundColor Yellow
python -c "import redis; print('✅ Redis library installed')" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Redis library ready" -ForegroundColor Green
} else {
    Write-Host "⚠️ Redis library not available" -ForegroundColor Red
}

# Test other imports
Write-Host "Testing other dependencies..." -ForegroundColor Yellow
python -c @"
import fastapi
import uvicorn
import slowapi
from azure.identity import InteractiveBrowserCredential
print('✅ All core dependencies available')
"@ 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ All dependencies verified" -ForegroundColor Green
} else {
    Write-Host "⚠️ Some dependencies missing" -ForegroundColor Red
}

Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Set up Azure Cache for Redis (see AZURE_DEPLOYMENT.md)"
Write-Host "  2. Configure environment variables in Azure App Service"
Write-Host "  3. Replace main.py with main_production.py"
Write-Host "  4. Deploy to Azure"
Write-Host ""
Write-Host "For local testing with Redis:"
Write-Host "  docker run -d -p 6379:6379 redis:latest"
Write-Host "  Set environment variable: `$env:REDIS_URL='redis://localhost:6379/0'"
Write-Host ""
Write-Host "To start local server:"
Write-Host "  python start_server.py runserver"
Write-Host ""
