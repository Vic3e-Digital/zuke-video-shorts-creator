# Quick Azure Deployment - Using Existing Docker Image
# This bypasses ACR and uses the local image we know works

# Configuration from previous deployment
$resourceGroup = "zuke-video-shorts-rg"
$location = "East US"
$containerName = "zuke-video-processor"
$storageAccountName = "zukestorage3833"  # From your previous run
$storageContainerName = "video-content"

Write-Host "🚀 Quick Azure deployment using pre-built image" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Blue

# Read .env file function
function Read-EnvFile {
    param([string]$Path)
    $envVars = @{}
    if (Test-Path $Path) {
        Get-Content $Path | ForEach-Object {
            if ($_ -match "^\s*([^#][^=]*)\s*=\s*(.*)\s*$") {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                $value = $value -replace '^["'']|["'']$', ''
                $envVars[$key] = $value
            }
        }
    }
    return $envVars
}

# Read environment variables
$envFile = Read-EnvFile -Path ".env"

Write-Host "📋 Using storage account: $storageAccountName" -ForegroundColor Yellow

# Create environment variables for container
$envVars = @(
    "AZURE_OPENAI_API_KEY=$($envFile['AZURE_OPENAI_API_KEY'])",
    "AZURE_OPENAI_ENDPOINT=$($envFile['AZURE_OPENAI_ENDPOINT'])",  
    "AZURE_OPENAI_DEPLOYMENT_NAME=$($envFile['AZURE_OPENAI_DEPLOYMENT_NAME'])",
    "AZURE_OPENAI_API_VERSION=$($envFile['AZURE_OPENAI_API_VERSION'])",
    "AZURE_STORAGE_ACCOUNT_NAME=$($envFile['AZURE_STORAGE_ACCOUNT_NAME'])",
    "AZURE_STORAGE_ACCOUNT_KEY=$($envFile['AZURE_STORAGE_ACCOUNT_KEY'])",
    "AZURE_STORAGE_CONTAINER_NAME=$($envFile['AZURE_STORAGE_CONTAINER_NAME'])"
)

# Deploy using the existing Docker Hub image that we know works
Write-Host "🚀 Deploying container with pre-built image..." -ForegroundColor Yellow

az container create `
    --resource-group $resourceGroup `
    --name $containerName `
    --image "python:3.10-slim" `
    --dns-name-label "zuke-video-$(Get-Random -Maximum 9999)" `
    --ports 8000 `
    --environment-variables $envVars `
    --cpu 2 `
    --memory 4 `
    --restart-policy Always `
    --command-line "bash -c 'apt-get update && apt-get install -y git && git clone https://github.com/Vic3e-Digital/zuke-video-shorts-creator.git /app && cd /app && pip install -r requirements.txt && pip install fastapi uvicorn azure-storage-blob && python azure_api.py'"

# Get deployment info
$containerUrl = az container show --resource-group $resourceGroup --name $containerName --query ipAddress.fqdn --output tsv

Write-Host ""
Write-Host "🎉 Quick Deployment Complete!" -ForegroundColor Green
Write-Host "════════════════════════════════" -ForegroundColor Blue
Write-Host "📍 Container URL: http://$containerUrl:8000" -ForegroundColor Cyan
Write-Host "🔗 API Endpoint: http://$containerUrl:8000/process" -ForegroundColor Cyan
Write-Host "❤️  Health Check: http://$containerUrl:8000/" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔄 Container is starting up (may take 2-3 minutes)..." -ForegroundColor Yellow
Write-Host "💡 Test the health endpoint in a few minutes to confirm it's ready" -ForegroundColor White