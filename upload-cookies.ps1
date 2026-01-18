# Quick YouTube Cookies Deployment Script
# This uploads cookies as a base64-encoded environment variable

$cookiesFile = "youtube_cookies.txt"

if (-not (Test-Path $cookiesFile)) {
    Write-Host "❌ $cookiesFile not found!" -ForegroundColor Red
    Write-Host "   Run: ./extract_youtube_cookies.sh chrome" -ForegroundColor Yellow
    exit 1
}

Write-Host "📦 Encoding cookies..." -ForegroundColor Cyan
$cookiesContent = Get-Content $cookiesFile -Raw
$cookiesBase64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($cookiesContent))

Write-Host "✅ Cookies encoded ($(($cookiesBase64.Length)) characters)" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Add this to your .env file:" -ForegroundColor Yellow
Write-Host "YOUTUBE_COOKIES_BASE64=$cookiesBase64" -ForegroundColor White
Write-Host ""
Write-Host "Then redeploy with: ./deploy-to-azure.ps1 -Recreate" -ForegroundColor Cyan
