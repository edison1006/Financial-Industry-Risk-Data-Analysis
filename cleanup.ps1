# cleanup.ps1
# Cleanup script to remove generated files and temporary data

Write-Host "🧹 Cleaning up generated files..." -ForegroundColor Yellow

# Remove generated CSV data files
if (Test-Path "core\data\raw") {
    Write-Host "Removing core\data\raw\*.csv files..." -ForegroundColor Cyan
    Remove-Item "core\data\raw\*.csv" -Force -ErrorAction SilentlyContinue
}

# Remove visualization outputs
if (Test-Path "visualizations") {
    Write-Host "Removing visualizations folder..." -ForegroundColor Cyan
    Remove-Item "visualizations" -Recurse -Force -ErrorAction SilentlyContinue
}

# Remove Python cache
Write-Host "Removing Python cache files..." -ForegroundColor Cyan
Get-ChildItem -Path . -Include __pycache__,*.pyc -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Remove virtual environment (if exists)
if (Test-Path ".venv") {
    Write-Host "Removing .venv folder..." -ForegroundColor Cyan
    Remove-Item ".venv" -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "✅ Cleanup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Note: Sample data in fake_loan_data\ is kept for reference." -ForegroundColor Gray
