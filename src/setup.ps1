# Get the script's directory (workspace root)
$WorkspaceRoot = $PSScriptRoot

Write-Host "Cleaning workspace..." -ForegroundColor Cyan

# Remove all folders starting with '.'
Write-Host "Removing folders starting with '.'..." -ForegroundColor Yellow
Get-ChildItem -Path $WorkspaceRoot -Directory -Recurse -Force -Filter ".*" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  Removing: $($_.FullName)" -ForegroundColor Gray
    Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
}

# Remove all __pycache__ folders
Write-Host "Removing __pycache__ folders..." -ForegroundColor Yellow
Get-ChildItem -Path $WorkspaceRoot -Directory -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  Removing: $($_.FullName)" -ForegroundColor Gray
    Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
}

# Sync workspace dependencies
Write-Host "Syncing workspace dependencies..." -ForegroundColor Cyan
Set-Location -Path $WorkspaceRoot
poetry sync

Write-Host "Setup complete!" -ForegroundColor Green
