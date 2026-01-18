# Azure Deployment Script for Zuke Video Shorts Creator (Docker-free)
# Run this in PowerShell after logging in with 'az login'

# Configuration
$resourceGroup = "zuke-video-shorts-rg"
$location = "East US"
$acrName = "zukevideoacr9358"  # Use existing ACR
$containerName = "zuke-video-processor"
$storageAccountName = "zukestorage3833"  # Continue with existing storage

Write-Host "🚀 Continuing Azure deployment (using ACR Build instead of local Docker)" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "Please create a .env file with your Azure OpenAI credentials." -ForegroundColor Red
    Write-Host "You can copy .env.example and update it with your values." -ForegroundColor Yellow
    exit 1
}

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

# Read .env file
Write-Host "📄 Reading environment variables from .env file..." -ForegroundColor Yellow
$envFile = Read-EnvFile -Path ".env"

# Validate required Azure OpenAI variables
$requiredVars = @("AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT_NAME")
$missingVars = @()

foreach ($var in $requiredVars) {
    if (-not $envFile.ContainsKey($var) -or [string]::IsNullOrWhiteSpace($envFile[$var])) {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "❌ Missing required environment variables in .env file:" -ForegroundColor Red
    $missingVars | ForEach-Object { Write-Host "   - $_" -ForegroundColor Red }
    exit 1
}

Write-Host "✅ All required environment variables found" -ForegroundColor Green

# Build image using ACR Build (no local Docker needed)
Write-Host "🔨 Building Docker image using Azure Container Registry Build..." -ForegroundColor Yellow

az acr build `
  --registry $acrName `
  --image "zuke-video-shorts:latest" `
  --file "Dockerfile.azure" `
  .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to build image using ACR Build" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Image built successfully using ACR Build!" -ForegroundColor Green

# Get ACR details
$acrServer = az acr show --name $acrName --query loginServer --output tsv
$acrUser = az acr credential show --name $acrName --query username --output tsv
$acrPassword = az acr credential show --name $acrName --query passwords[0].value --output tsv

# Get storage account details (should exist from previous run)
Write-Host "🗄️ Checking Azure Storage Account..." -ForegroundColor Yellow

$storageExists = az storage account show --name $storageAccountName --resource-group $resourceGroup --query name --output tsv 2>$null

if (-not $storageExists) {
    Write-Host "⚠️ Storage account doesn't exist, creating..." -ForegroundColor Yellow
    
    az storage account create `
        --name $storageAccountName `
        --resource-group $resourceGroup `
        --location $location `
        --sku Standard_LRS `
        --allow-blob-public-access true
    
    $storageKey = az storage account keys list --account-name $storageAccountName --query [0].value --output tsv
    
    az storage container create `
        --name "video-content" `
        --account-name $storageAccountName `
        --account-key $storageKey `
        --public-access blob
    
    # Update .env file
    if (-not ($envFile.ContainsKey('AZURE_STORAGE_ACCOUNT_NAME'))) {
        Add-Content -Path ".env" -Value ""
        Add-Content -Path ".env" -Value "# Azure Storage (auto-generated)"
        Add-Content -Path ".env" -Value "AZURE_STORAGE_ACCOUNT_NAME=$storageAccountName"
        Add-Content -Path ".env" -Value "AZURE_STORAGE_ACCOUNT_KEY=$storageKey"
        Add-Content -Path ".env" -Value "AZURE_STORAGE_CONTAINER_NAME=video-content"
        
        # Re-read .env file
        $envFile = Read-EnvFile -Path ".env"
    }
} else {
    Write-Host "✅ Storage account exists" -ForegroundColor Green
}

# Create environment variables array
$envVars = @(
    "AZURE_OPENAI_API_KEY=$($envFile['AZURE_OPENAI_API_KEY'])",
    "AZURE_OPENAI_ENDPOINT=$($envFile['AZURE_OPENAI_ENDPOINT'])",
    "AZURE_OPENAI_DEPLOYMENT_NAME=$($envFile['AZURE_OPENAI_DEPLOYMENT_NAME'])",
    "AZURE_OPENAI_API_VERSION=$($envFile.ContainsKey('AZURE_OPENAI_API_VERSION') ? $envFile['AZURE_OPENAI_API_VERSION'] : '2024-02-01')",
    "AZURE_STORAGE_ACCOUNT_NAME=$($envFile['AZURE_STORAGE_ACCOUNT_NAME'])",
    "AZURE_STORAGE_ACCOUNT_KEY=$($envFile['AZURE_STORAGE_ACCOUNT_KEY'])",
    "AZURE_STORAGE_CONTAINER_NAME=$($envFile['AZURE_STORAGE_CONTAINER_NAME'])"
)

# Deploy to Azure Container Instances
Write-Host "🚀 Deploying to Azure Container Instances..." -ForegroundColor Yellow

az container create `
  --resource-group $resourceGroup `
  --name $containerName `
  --image "$acrServer/zuke-video-shorts:latest" `
  --registry-login-server $acrServer `
  --registry-username $acrUser `
  --registry-password $acrPassword `
  --dns-name-label "zuke-video-$(Get-Random -Maximum 9999)" `
  --ports 8000 `
  --environment-variables $envVars `
  --cpu 2 `
  --memory 4 `
  --restart-policy Always

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to deploy container" -ForegroundColor Red
    exit 1
}

# Get deployment info
$containerUrl = az container show --resource-group $resourceGroup --name $containerName --query ipAddress.fqdn --output tsv
$publicIP = az container show --resource-group $resourceGroup --name $containerName --query ipAddress.ip --output tsv

Write-Host "" 
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "════════════════════════" -ForegroundColor Blue
Write-Host "📍 Container URL: http://$containerUrl:8000" -ForegroundColor Cyan
Write-Host "🌐 Public IP: $publicIP" -ForegroundColor Cyan
Write-Host "🔗 API Endpoint for n8n: http://$containerUrl:8000/process" -ForegroundColor Cyan
Write-Host "❤️  Health Check: http://$containerUrl:8000/" -ForegroundColor Cyan
Write-Host "🗄️ Storage: https://$($envFile['AZURE_STORAGE_ACCOUNT_NAME']).blob.core.windows.net/$($envFile['AZURE_STORAGE_CONTAINER_NAME'])/" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Test the health endpoint: http://$containerUrl:8000/" -ForegroundColor White
Write-Host "   2. Update n8n HTTP Request URL to: http://$containerUrl:8000/process" -ForegroundColor White
Write-Host "   3. Send a test request from your frontend" -ForegroundColor White
Write-Host ""

# Save details to file
$deploymentInfo = @{
    ResourceGroup = $resourceGroup
    ContainerRegistry = $acrServer
    ContainerName = $containerName
    StorageAccount = $envFile['AZURE_STORAGE_ACCOUNT_NAME']
    StorageContainer = $envFile['AZURE_STORAGE_CONTAINER_NAME']
    PublicURL = "http://$containerUrl:8000"
    APIEndpoint = "http://$containerUrl:8000/process"
    HealthCheck = "http://$containerUrl:8000/"
    VideoStorageURL = "https://$($envFile['AZURE_STORAGE_ACCOUNT_NAME']).blob.core.windows.net/$($envFile['AZURE_STORAGE_CONTAINER_NAME'])/"
} | ConvertTo-Json -Depth 2

$deploymentInfo | Out-File -FilePath "azure-deployment-info.json" -Encoding UTF8
Write-Host "💾 Deployment details saved to: azure-deployment-info.json" -ForegroundColor Green