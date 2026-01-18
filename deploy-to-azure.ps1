#Requires -Version 7.0

<#
.SYNOPSIS
    Azure Deployment Script for Zuke Video Shorts Creator

.DESCRIPTION
    Deploys the Zuke Video Shorts application to Azure Container Instances.
    Supports both local Docker builds and cloud-based ACR Build.
    Includes security best practices for handling secrets.

.PARAMETER UseLocalDocker
    Use local Docker to build and push (requires Docker Desktop)
    Default: Uses ACR Build (no local Docker needed)

.PARAMETER Cleanup
    Remove all deployed resources

.PARAMETER DryRun
    Show what would be deployed without making changes

.PARAMETER PrivateStorage
    Use private blob storage with SAS tokens instead of public access

.PARAMETER ResourcePrefix
    Prefix for resource names (default: "zuke")

.PARAMETER Recreate
    Delete and recreate the container (useful for updates)

.EXAMPLE
    ./deploy-to-azure.ps1
    # Deploy using ACR Build (no Docker needed)

.EXAMPLE
    ./deploy-to-azure.ps1 -UseLocalDocker
    # Deploy using local Docker

.EXAMPLE
    ./deploy-to-azure.ps1 -DryRun
    # Preview deployment without making changes

.EXAMPLE
    ./deploy-to-azure.ps1 -PrivateStorage
    # Deploy with private blob storage

.EXAMPLE
    ./deploy-to-azure.ps1 -Cleanup
    # Remove all resources

.EXAMPLE
    ./deploy-to-azure.ps1 -Recreate
    # Update deployment by recreating container
#>

param(
    [switch]$UseLocalDocker,
    [switch]$Cleanup,
    [switch]$DryRun,
    [switch]$PrivateStorage,
    [switch]$Recreate,
    [string]$ResourcePrefix = "zuke"
)

# ============================================================================
# CONFIGURATION
# ============================================================================

$script:Config = @{
    ResourceGroup        = "$ResourcePrefix-video-shorts-rg"
    Location             = "East US"
    AcrName              = ""  # Will be set dynamically or from saved config
    ContainerName        = "$ResourcePrefix-video-processor"
    StorageAccountName   = ""  # Will be set dynamically or from saved config
    StorageContainerName = "video-content"
    ContainerCpu         = 2
    ContainerMemory      = 4
    ContainerPort        = 8000
    Tags                 = @{
        project     = "zuke-video-shorts"
        environment = "prod"
        managedBy   = "deployment-script"
    }
    ConfigFile           = ".azure-deployment-config.json"
    CredentialsFile      = ".azure-storage-credentials.json"
    DeploymentInfoFile   = "azure-deployment-info.json"
    SourceArchive        = ".source-archive.tar.gz"
}

# Environment variable definitions
$script:RequiredEnvVars = @(
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_DEPLOYMENT_NAME"
)

$script:SecretEnvVars = @(
    "AZURE_OPENAI_API_KEY",
    "AZURE_STORAGE_ACCOUNT_KEY"
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function Write-Banner {
    param([string]$Title, [string]$Color = "Green")
    Write-Host ""
    Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Blue
    Write-Host " $Title" -ForegroundColor $Color
    Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Blue
}

function Write-Step {
    param(
        [string]$Message,
        [string]$Emoji = "▶️",
        [string]$Color = "Yellow"
    )
    Write-Host ""
    Write-Host "$Emoji $Message" -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-Host "   ✅ $Message" -ForegroundColor Green
}

function Write-Failure {
    param([string]$Message)
    Write-Host "   ❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "   ℹ️  $Message" -ForegroundColor Cyan
}

function Write-Detail {
    param([string]$Message)
    Write-Host "      $Message" -ForegroundColor White
}

function Write-WarningMsg {
    param([string]$Message)
    Write-Host "   ⚠️  $Message" -ForegroundColor Yellow
}

function Write-DryRun {
    param([string]$Message)
    Write-Host "   [DRY RUN] $Message" -ForegroundColor Magenta
}

function Get-TagsString {
    $tagPairs = $script:Config.Tags.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }
    return $tagPairs -join " "
}

function Test-CommandSuccess {
    param(
        [string]$ErrorMessage,
        [switch]$ExitOnError
    )

    if ($LASTEXITCODE -ne 0) {
        Write-Failure $ErrorMessage
        if ($ExitOnError) {
            Write-Host ""
            Write-Host "Deployment failed. Check the errors above." -ForegroundColor Red
            exit 1
        }
        return $false
    }
    return $true
}

function Read-EnvFile {
    param([string]$Path)

    $envVars = @{}

    if (-not (Test-Path $Path)) {
        return $envVars
    }

    $lineNumber = 0
    Get-Content $Path | ForEach-Object {
        $lineNumber++
        $line = $_.Trim()

        # Skip empty lines and comments
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) {
            return
        }

        # Find first '=' to split key and value (handles values with '=' in them)
        $equalIndex = $line.IndexOf('=')
        if ($equalIndex -gt 0) {
            $key = $line.Substring(0, $equalIndex).Trim()
            $value = ""

            if ($equalIndex -lt $line.Length - 1) {
                $value = $line.Substring($equalIndex + 1).Trim()
            }

            # Remove surrounding quotes (single or double)
            if ($value.Length -ge 2) {
                if (($value.StartsWith('"') -and $value.EndsWith('"')) -or
                    ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                    $value = $value.Substring(1, $value.Length - 2)
                }
            }

            $envVars[$key] = $value
        }
        else {
            Write-WarningMsg "Invalid line $lineNumber in .env file: $line"
        }
    }

    return $envVars
}

function Save-DeploymentConfig {
    param([hashtable]$ConfigData)

    if ($DryRun) { return }

    $ConfigData | ConvertTo-Json -Depth 3 | Out-File -FilePath $script:Config.ConfigFile -Encoding UTF8
    Write-Detail "Configuration saved to $($script:Config.ConfigFile)"
}

function Get-SavedDeploymentConfig {
    if (Test-Path $script:Config.ConfigFile) {
        try {
            $saved = Get-Content $script:Config.ConfigFile | ConvertFrom-Json -AsHashtable
            return $saved
        }
        catch {
            Write-WarningMsg "Could not read saved config, will create new resources"
            return $null
        }
    }
    return $null
}

function Add-ToGitignore {
    param([string]$Pattern)

    if (-not (Test-Path ".gitignore")) {
        return
    }

    $gitignore = Get-Content ".gitignore" -ErrorAction SilentlyContinue
    if ($gitignore -notcontains $Pattern) {
        Add-Content ".gitignore" "`n# Azure deployment (auto-added)`n$Pattern"
        Write-Detail "Added $Pattern to .gitignore"
    }
}

function Invoke-AzCommand {
    param(
        [string]$Command,
        [string]$Description,
        [switch]$CaptureOutput,
        [switch]$ExitOnError,
        [switch]$SuppressError
    )

    if ($DryRun) {
        Write-DryRun "az $Command"
        if ($CaptureOutput) {
            return "[DRY-RUN-VALUE]"
        }
        return
    }

    $fullCommand = "az $Command"
    if ($SuppressError) {
        $fullCommand += " 2>`$null"
    }

    if ($CaptureOutput) {
        $result = Invoke-Expression $fullCommand
        if (-not (Test-CommandSuccess -ErrorMessage $Description -ExitOnError:$ExitOnError)) {
            return $null
        }
        return $result
    }
    else {
        Invoke-Expression $fullCommand
        Test-CommandSuccess -ErrorMessage $Description -ExitOnError:$ExitOnError | Out-Null
    }
}

function Invoke-DockerCommand {
    param(
        [string]$Command,
        [string]$Description
    )

    if ($DryRun) {
        Write-DryRun "docker $Command"
        return $true
    }

    Invoke-Expression "docker $Command"
    return Test-CommandSuccess -ErrorMessage $Description -ExitOnError
}

function Get-MaskedValue {
    param([string]$Value, [int]$ShowLast = 4)

    if ([string]::IsNullOrEmpty($Value)) {
        return "[empty]"
    }

    if ($Value.Length -le $ShowLast) {
        return "****"
    }

    return "****" + $Value.Substring($Value.Length - $ShowLast)
}

function Test-IsMacOS {
    return $IsMacOS -or ($PSVersionTable.OS -match 'Darwin')
}

# ============================================================================
# CLEANUP FUNCTION
# ============================================================================

function Invoke-Cleanup {
    Write-Banner "🧹 CLEANUP MODE" "Red"

    # Load saved config if available
    $savedConfig = Get-SavedDeploymentConfig
    if ($savedConfig) {
        Write-Step "Found saved deployment configuration:" "📋"
        Write-Detail "Resource Group: $($savedConfig.ResourceGroup)"
        Write-Detail "ACR: $($savedConfig.AcrName)"
        Write-Detail "Storage: $($savedConfig.StorageAccountName)"
        Write-Detail "Container: $($savedConfig.ContainerName)"
    }

    # Check if deployment info exists
    if (Test-Path $script:Config.DeploymentInfoFile) {
        $deployInfo = Get-Content $script:Config.DeploymentInfoFile | ConvertFrom-Json
        Write-Step "Found deployment info:" "📋"
        Write-Detail "Public URL: $($deployInfo.PublicURL)"
    }

    $resourceGroup = if ($savedConfig) { $savedConfig.ResourceGroup } else { $script:Config.ResourceGroup }

    Write-Host ""
    Write-Host "⚠️  WARNING: This will permanently delete:" -ForegroundColor Red
    Write-Host "   • Resource Group: $resourceGroup" -ForegroundColor Yellow
    Write-Host "   • All resources within (ACR, Storage, Container)" -ForegroundColor Yellow
    Write-Host "   • All stored videos and data" -ForegroundColor Yellow
    Write-Host ""

    if ($DryRun) {
        Write-DryRun "Would delete resource group: $resourceGroup"
        Write-DryRun "Would remove local config files"
        return
    }

    $confirm = Read-Host "Type 'DELETE' to confirm (or anything else to cancel)"

    if ($confirm -ne 'DELETE') {
        Write-Host ""
        Write-Host "Cleanup cancelled." -ForegroundColor Yellow
        exit 0
    }

    Write-Step "Deleting resource group..." "🗑️" "Red"

    az group delete --name $resourceGroup --yes --no-wait

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Resource group deletion initiated (running in background)"
        Write-Info "It may take a few minutes to complete"

        # Clean up local files
        $filesToRemove = @(
            $script:Config.ConfigFile,
            $script:Config.CredentialsFile,
            $script:Config.DeploymentInfoFile,
            $script:Config.SourceArchive
        )

        foreach ($file in $filesToRemove) {
            if (Test-Path $file) {
                Remove-Item $file -Force
                Write-Success "Removed $file"
            }
        }
    }
    else {
        Write-Failure "Failed to delete resource group"
        Write-Info "You may need to delete it manually in the Azure Portal"
    }

    Write-Host ""
    Write-Host "Cleanup complete." -ForegroundColor Green
    exit 0
}

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

function Test-Prerequisites {
    Write-Step "Validating prerequisites..." "🔍"

    $allValid = $true

    # Check Azure CLI
    try {
        $azVersionJson = az version 2>$null
        if ($azVersionJson) {
            $azVersion = $azVersionJson | ConvertFrom-Json
            Write-Success "Azure CLI: $($azVersion.'azure-cli')"
        }
        else {
            throw "Azure CLI not responding"
        }
    }
    catch {
        Write-Failure "Azure CLI not found"
        Write-Detail "Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        $allValid = $false
    }

    # Check Docker (only if using local Docker)
    if ($UseLocalDocker) {
        try {
            $dockerVersion = docker version --format '{{.Server.Version}}' 2>$null
            if ($dockerVersion) {
                Write-Success "Docker: $dockerVersion"
            }
            else {
                throw "Docker not responding"
            }
        }
        catch {
            Write-Failure "Docker not found or not running"
            Write-Detail "Either start Docker Desktop or run without -UseLocalDocker flag"
            $allValid = $false
        }
    }
    else {
        Write-Success "Docker: Not required (using ACR Build)"
    }

    # Check Azure login
    try {
        $account = az account show 2>$null | ConvertFrom-Json
        if ($account) {
            Write-Success "Azure Account: $($account.user.name)"
            Write-Detail "Subscription: $($account.name)"
        }
        else {
            throw "Not logged in"
        }
    }
    catch {
        Write-Failure "Not logged in to Azure"
        Write-Detail "Run 'az login' first"
        $allValid = $false
    }

    # Check .env file
    if (Test-Path ".env") {
        Write-Success ".env file found"
    }
    else {
        Write-Failure ".env file not found"
        Write-Detail "Create a .env file with your Azure OpenAI credentials"
        Write-Detail "Copy .env.example as a starting point"
        $allValid = $false
    }

    # Check Dockerfile
    if (Test-Path "Dockerfile.azure") {
        Write-Success "Dockerfile.azure found"
    }
    else {
        Write-Failure "Dockerfile.azure not found"
        $allValid = $false
    }

    # Check for tar (needed for macOS workaround)
    if (-not $UseLocalDocker) {
        $tarExists = Get-Command tar -ErrorAction SilentlyContinue
        if ($tarExists) {
            Write-Success "tar: Available"
        }
        else {
            Write-Failure "tar command not found (required for ACR Build)"
            $allValid = $false
        }
    }

    if (-not $allValid) {
        Write-Host ""
        Write-Failure "Prerequisites check failed. Please fix the issues above."
        exit 1
    }

    Write-Host ""
    Write-Success "All prerequisites validated"
}

function Test-EnvironmentVariables {
    param([hashtable]$EnvFile)

    Write-Step "Validating environment variables..." "📄"

    $missingVars = @()

    foreach ($var in $script:RequiredEnvVars) {
        if (-not $EnvFile.ContainsKey($var) -or [string]::IsNullOrWhiteSpace($EnvFile[$var])) {
            $missingVars += $var
            Write-Failure "Missing: $var"
        }
        else {
            $displayValue = if ($var -in $script:SecretEnvVars) {
                Get-MaskedValue -Value $EnvFile[$var]
            }
            else {
                $EnvFile[$var]
            }
            Write-Success "$var = $displayValue"
        }
    }

    # Check optional variables
    $optionalVars = @("AZURE_OPENAI_API_VERSION")
    foreach ($var in $optionalVars) {
        if ($EnvFile.ContainsKey($var) -and -not [string]::IsNullOrWhiteSpace($EnvFile[$var])) {
            Write-Success "$var = $($EnvFile[$var])"
        }
        else {
            Write-Info "$var = 2024-02-01 (default)"
        }
    }

    if ($missingVars.Count -gt 0) {
        Write-Host ""
        Write-Failure "Missing required environment variables in .env file"
        exit 1
    }

    Write-Host ""
    Write-Success "Environment variables validated"
}

# ============================================================================
# RESOURCE CREATION FUNCTIONS
# ============================================================================

function New-ResourceGroup {
    Write-Step "Setting up Resource Group..." "📁"

    # Check if resource group exists
    $rgExists = Invoke-AzCommand `
        -Command "group show --name $($script:Config.ResourceGroup) --query name -o tsv" `
        -Description "Check resource group" `
        -CaptureOutput `
        -SuppressError

    if ($rgExists -and $rgExists -ne "[DRY-RUN-VALUE]") {
        Write-Success "Resource group exists: $($script:Config.ResourceGroup)"
        return
    }

    Write-Info "Creating resource group: $($script:Config.ResourceGroup)"

    $tagsString = Get-TagsString
    Invoke-AzCommand `
        -Command "group create --name $($script:Config.ResourceGroup) --location '$($script:Config.Location)' --tags $tagsString" `
        -Description "Create resource group" `
        -ExitOnError

    Write-Success "Resource group created: $($script:Config.ResourceGroup)"
}

function New-ContainerRegistry {
    Write-Step "Setting up Azure Container Registry..." "🏗️"

    # Check if we have a saved ACR name
    $savedConfig = Get-SavedDeploymentConfig
    if ($savedConfig -and $savedConfig.AcrName) {
        $script:Config.AcrName = $savedConfig.AcrName
        Write-Info "Using existing ACR: $($script:Config.AcrName)"
    }
    else {
        # Generate new ACR name
        $script:Config.AcrName = "$($ResourcePrefix)videoacr$(Get-Random -Maximum 9999)"
        Write-Info "Creating new ACR: $($script:Config.AcrName)"
    }

    # Check if ACR exists
    $acrExists = Invoke-AzCommand `
        -Command "acr show --name $($script:Config.AcrName) --query name -o tsv" `
        -Description "Check ACR" `
        -CaptureOutput `
        -SuppressError

    if ($acrExists -and $acrExists -ne "[DRY-RUN-VALUE]") {
        Write-Success "ACR exists: $($script:Config.AcrName)"
    }
    else {
        $tagsString = Get-TagsString
        Invoke-AzCommand `
            -Command "acr create --resource-group $($script:Config.ResourceGroup) --name $($script:Config.AcrName) --sku Basic --admin-enabled true --tags $tagsString" `
            -Description "Create ACR" `
            -ExitOnError

        Write-Success "ACR created: $($script:Config.AcrName)"
    }

    # Get ACR server URL
    $script:AcrServer = Invoke-AzCommand `
        -Command "acr show --name $($script:Config.AcrName) --query loginServer -o tsv" `
        -Description "Get ACR server" `
        -CaptureOutput

    Write-Detail "ACR Server: $($script:AcrServer)"
}

function New-StorageAccount {
    param([hashtable]$EnvFile)

    Write-Step "Setting up Azure Blob Storage..." "🗄️"

    # Check if storage is already configured in .env
    $hasStorageConfig = (
        $EnvFile.ContainsKey('AZURE_STORAGE_ACCOUNT_NAME') -and
        $EnvFile.ContainsKey('AZURE_STORAGE_ACCOUNT_KEY') -and
        -not [string]::IsNullOrWhiteSpace($EnvFile['AZURE_STORAGE_ACCOUNT_NAME']) -and
        -not [string]::IsNullOrWhiteSpace($EnvFile['AZURE_STORAGE_ACCOUNT_KEY'])
    )

    if ($hasStorageConfig) {
        $script:Config.StorageAccountName = $EnvFile['AZURE_STORAGE_ACCOUNT_NAME']
        $script:Config.StorageContainerName = $EnvFile['AZURE_STORAGE_CONTAINER_NAME'] ?? "video-content"

        Write-Success "Using storage configuration from .env"
        Write-Detail "Account: $($script:Config.StorageAccountName)"
        Write-Detail "Container: $($script:Config.StorageContainerName)"
        return $EnvFile
    }

    # Check if we have a saved storage account name
    $savedConfig = Get-SavedDeploymentConfig
    if ($savedConfig -and $savedConfig.StorageAccountName) {
        $script:Config.StorageAccountName = $savedConfig.StorageAccountName
    }
    else {
        # Generate new storage account name (must be lowercase, no hyphens)
        $script:Config.StorageAccountName = "$($ResourcePrefix.ToLower())storage$(Get-Random -Maximum 9999)"
    }

    # Check if storage account exists
    $storageExists = Invoke-AzCommand `
        -Command "storage account show --name $($script:Config.StorageAccountName) --resource-group $($script:Config.ResourceGroup) --query name -o tsv" `
        -Description "Check storage account" `
        -CaptureOutput `
        -SuppressError

    if ($storageExists -and $storageExists -ne "[DRY-RUN-VALUE]") {
        Write-Success "Storage account exists: $($script:Config.StorageAccountName)"
    }
    else {
        Write-Info "Creating storage account: $($script:Config.StorageAccountName)"

        $publicAccessParam = if ($PrivateStorage) { "false" } else { "true" }
        $tagsString = Get-TagsString

        Invoke-AzCommand `
            -Command "storage account create --name $($script:Config.StorageAccountName) --resource-group $($script:Config.ResourceGroup) --location '$($script:Config.Location)' --sku Standard_LRS --allow-blob-public-access $publicAccessParam --tags $tagsString" `
            -Description "Create storage account" `
            -ExitOnError

        Write-Success "Storage account created"
    }

    # Get storage key
    $storageKey = Invoke-AzCommand `
        -Command "storage account keys list --account-name $($script:Config.StorageAccountName) --resource-group $($script:Config.ResourceGroup) --query [0].value -o tsv" `
        -Description "Get storage key" `
        -CaptureOutput

    # Check/create blob container
    $containerAccess = if ($PrivateStorage) { "off" } else { "blob" }

    $containerExists = Invoke-AzCommand `
        -Command "storage container show --name $($script:Config.StorageContainerName) --account-name $($script:Config.StorageAccountName) --account-key '$storageKey' --query name -o tsv" `
        -Description "Check blob container" `
        -CaptureOutput `
        -SuppressError

    if (-not $containerExists -or $containerExists -eq "[DRY-RUN-VALUE]") {
        Invoke-AzCommand `
            -Command "storage container create --name $($script:Config.StorageContainerName) --account-name $($script:Config.StorageAccountName) --account-key '$storageKey' --public-access $containerAccess" `
            -Description "Create blob container" `
            -ExitOnError

        Write-Success "Blob container created: $($script:Config.StorageContainerName)"
    }
    else {
        Write-Success "Blob container exists: $($script:Config.StorageContainerName)"
    }

    # Update environment variables
    $EnvFile['AZURE_STORAGE_ACCOUNT_NAME'] = $script:Config.StorageAccountName
    $EnvFile['AZURE_STORAGE_ACCOUNT_KEY'] = $storageKey
    $EnvFile['AZURE_STORAGE_CONTAINER_NAME'] = $script:Config.StorageContainerName

    # Generate SAS token for private storage
    if ($PrivateStorage) {
        Write-Info "Generating SAS token for private storage..."

        $sasExpiry = (Get-Date).AddYears(1).ToString("yyyy-MM-ddTHH:mm:ssZ")
        $sasToken = Invoke-AzCommand `
            -Command "storage container generate-sas --name $($script:Config.StorageContainerName) --account-name $($script:Config.StorageAccountName) --account-key '$storageKey' --permissions rwdl --expiry $sasExpiry -o tsv" `
            -Description "Generate SAS token" `
            -CaptureOutput

        $EnvFile['AZURE_STORAGE_SAS_TOKEN'] = $sasToken
        Write-Success "SAS token generated (expires: $sasExpiry)"
    }

    # Save credentials to secure file (not .env)
    if (-not $DryRun) {
        $credentials = @{
            StorageAccountName = $script:Config.StorageAccountName
            StorageAccountKey  = $storageKey
            ContainerName      = $script:Config.StorageContainerName
            SasToken           = if ($PrivateStorage) { $EnvFile['AZURE_STORAGE_SAS_TOKEN'] } else { $null }
            PrivateStorage     = $PrivateStorage.IsPresent
            CreatedAt          = (Get-Date).ToString("o")
        }

        $credentials | ConvertTo-Json -Depth 2 | Out-File -FilePath $script:Config.CredentialsFile -Encoding UTF8

        Write-WarningMsg "Storage credentials saved to $($script:Config.CredentialsFile)"
        Write-WarningMsg "DO NOT commit this file to version control!"

        Add-ToGitignore $script:Config.CredentialsFile
    }

    if ($PrivateStorage) {
        Write-Info "Private storage mode: Videos require SAS token for access"
    }
    else {
        Write-WarningMsg "Public storage mode: Videos are publicly accessible"
    }

    return $EnvFile
}

# ============================================================================
# BUILD FUNCTIONS
# ============================================================================

function Get-UploadEstimate {
    Write-Step "Calculating upload size..." "📦"
    
    # Patterns to exclude (matching .dockerignore)
    $excludePatterns = @(
        '[\\/]\.git[\\/]',
        '[\\/]videos[\\/]',
        '[\\/]output[\\/]', 
        '[\\/]demos[\\/]',
        '[\\/]models[\\/]',
        '[\\/]venv[\\/]',
        '[\\/]\.venv[\\/]',
        '[\\/]node_modules[\\/]',
        '[\\/]__pycache__[\\/]',
        '\.mp4$',
        '\.mp3$',
        '\.wav$',
        '\.avi$',
        '\.mov$',
        '\.mkv$',
        '\.webm$',
        '\.bin$',
        '\.pt$',
        '\.pth$',
        '\.tar\.gz$'
    )
    
    $excludeRegex = ($excludePatterns | ForEach-Object { "($_)" }) -join '|'
    
    # Get files that would be uploaded
    $files = Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue | 
        Where-Object { $_.FullName -notmatch $excludeRegex }
    
    $totalSize = ($files | Measure-Object -Property Length -Sum).Sum
    if ($null -eq $totalSize) { $totalSize = 0 }
    $fileCount = $files.Count
    
    # Format size nicely
    $sizeFormatted = if ($totalSize -gt 1GB) {
        "{0:N2} GB" -f ($totalSize / 1GB)
    } elseif ($totalSize -gt 1MB) {
        "{0:N2} MB" -f ($totalSize / 1MB)
    } elseif ($totalSize -gt 1KB) {
        "{0:N2} KB" -f ($totalSize / 1KB)
    } else {
        "$totalSize bytes"
    }
    
    Write-Host ""
    Write-Host "   ┌──────────────────────────────────────────┐" -ForegroundColor Blue
    Write-Host "   │  📊 UPLOAD ESTIMATE                      │" -ForegroundColor Blue
    Write-Host "   ├──────────────────────────────────────────┤" -ForegroundColor Blue
    Write-Host "   │  Files: " -NoNewline -ForegroundColor Blue
    Write-Host ("{0,-30}" -f "$fileCount files") -NoNewline -ForegroundColor White
    Write-Host "│" -ForegroundColor Blue
    Write-Host "   │  Size:  " -NoNewline -ForegroundColor Blue
    Write-Host ("{0,-30}" -f $sizeFormatted) -NoNewline -ForegroundColor Green
    Write-Host "│" -ForegroundColor Blue
    Write-Host "   └──────────────────────────────────────────┘" -ForegroundColor Blue
    
    # Warn if too large
    if ($totalSize -gt 100MB) {
        Write-WarningMsg "Upload is large! Check .dockerignore to exclude unnecessary files."
    } elseif ($totalSize -gt 50MB) {
        Write-WarningMsg "Upload is moderately large. Consider optimizing .dockerignore"
    } else {
        Write-Success "Size looks good! Upload should be quick."
    }
    
    # Show largest files
    Write-Host ""
    Write-Detail "Top 5 largest files:"
    $largestFiles = $files | Sort-Object Length -Descending | Select-Object -First 5
    foreach ($file in $largestFiles) {
        $fileSize = if ($file.Length -gt 1MB) {
            "{0:N2} MB" -f ($file.Length / 1MB)
        } elseif ($file.Length -gt 1KB) {
            "{0:N2} KB" -f ($file.Length / 1KB)
        } else {
            "$($file.Length) B"
        }
        $relativePath = $file.FullName.Replace((Get-Location).Path, "").TrimStart("/\")
        # Truncate long paths
        if ($relativePath.Length -gt 50) {
            $relativePath = "..." + $relativePath.Substring($relativePath.Length - 47)
        }
        Write-Host "      " -NoNewline
        Write-Host ("{0,10}" -f $fileSize) -NoNewline -ForegroundColor Cyan
        Write-Host "  $relativePath" -ForegroundColor DarkGray
    }
    
    # Estimate upload time
    $estimatedSeconds = [math]::Max(5, [math]::Ceiling($totalSize / 2MB))
    $estimatedTime = if ($estimatedSeconds -gt 60) {
        "{0:N0} min" -f ($estimatedSeconds / 60)
    } else {
        "$estimatedSeconds sec"
    }
    Write-Host ""
    Write-Info "Estimated upload time: ~$estimatedTime (varies by connection)"
    
    return @{
        FileCount = $fileCount
        TotalSize = $totalSize
        SizeFormatted = $sizeFormatted
        EstimatedSeconds = $estimatedSeconds
    }
}

function New-SourceArchive {
    Write-Step "Creating source archive..." "📦"
    
    $archiveName = "source-archive.tar.gz"
    $archivePath = Join-Path -Path (Get-Location).Path -ChildPath $archiveName
    
    # Remove old archive if exists
    if (Test-Path $archivePath) {
        Remove-Item $archivePath -Force
    }
    
    Write-Info "Packaging source files..."
    
    if ($DryRun) {
        Write-DryRun "tar -czf $archiveName (with exclusions)"
        return $archivePath
    }
    
    Write-Detail "Running tar with inline exclusions..."
    
    # Create a temporary shell script for reliable tar execution on macOS
    $tarScriptPath = Join-Path -Path (Get-Location).Path -ChildPath ".tar-script.sh"
    
    # Build tar command with all exclusions
    $tarScript = @"
#!/bin/bash
tar -czf "$archiveName" \
  --exclude='.git' \
  --exclude='videos' \
  --exclude='output' \
  --exclude='demos' \
  --exclude='models' \
  --exclude='venv' \
  --exclude='.venv' \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.mp4' \
  --exclude='*.mp3' \
  --exclude='*.wav' \
  --exclude='*.avi' \
  --exclude='*.mov' \
  --exclude='*.mkv' \
  --exclude='*.webm' \
  --exclude='*.bin' \
  --exclude='*.pt' \
  --exclude='*.pth' \
  --exclude='*.tar.gz' \
  --exclude='.azure-*' \
  --exclude='azure-deployment-info.json' \
  --exclude='source-archive.tar.gz' \
  --exclude='.tar-script.sh' \
  .
"@
    
    # Write script file
    Set-Content -Path $tarScriptPath -Value $tarScript -NoNewline
    
    # Make it executable
    chmod +x $tarScriptPath | Out-Null
    
    Write-Detail "Executing: tar via shell script"
    
    # Execute the script
    $result = & bash $tarScriptPath 2>&1
    $exitCode = $LASTEXITCODE
    
    # Clean up script file
    if (Test-Path $tarScriptPath) {
        Remove-Item $tarScriptPath -Force -ErrorAction SilentlyContinue
    }
    
    # Show any output (warnings are OK)
    if ($result) {
        $result | ForEach-Object { 
            if ($_ -notmatch "Can't add archive to itself") {
                Write-Detail $_ 
            }
        }
    }
    
    # Check exit code
    if ($exitCode -ne 0) {
        Write-Failure "tar command failed with exit code: $exitCode"
        if ($result) {
            Write-Detail "Error output:"
            $result | ForEach-Object { Write-Detail "  $_" }
        }
        exit 1
    }
    
    # Small delay to ensure file system catches up
    Start-Sleep -Milliseconds 500
    
    # Verify archive was created
    if (-not (Test-Path $archivePath)) {
        Write-Failure "Failed to create archive at: $archivePath"
        Write-Detail "Current directory: $(Get-Location)"
        Write-Detail "Files in directory:"
        Get-ChildItem -Name "*.tar.gz" | ForEach-Object { Write-Detail "  $_" }
        exit 1
    }
    
    $archiveInfo = Get-Item $archivePath
    
    if ($archiveInfo.Length -eq 0) {
        Write-Failure "Archive is empty"
        exit 1
    }
    
    $archiveSizeFormatted = if ($archiveInfo.Length -gt 1MB) {
        "{0:N2} MB" -f ($archiveInfo.Length / 1MB)
    } elseif ($archiveInfo.Length -gt 1KB) {
        "{0:N2} KB" -f ($archiveInfo.Length / 1KB)
    } else {
        "$($archiveInfo.Length) bytes"
    }
    
    Write-Success "Archive created: $archiveName ($archiveSizeFormatted)"
    
    return $archivePath
}

function Build-WithACR {
    Write-Step "Building Docker image using ACR Build..." "☁️"
    Write-Info "This builds in Azure (no local Docker required)"
    
    # Calculate and show upload estimate
    $uploadInfo = Get-UploadEstimate
    
    # Confirm if large
    if ($uploadInfo.TotalSize -gt 100MB -and -not $DryRun) {
        Write-Host ""
        $continue = Read-Host "   Upload is large ($($uploadInfo.SizeFormatted)). Continue? [Y/n]"
        if ($continue -eq 'n' -or $continue -eq 'N') {
            Write-Failure "Deployment cancelled. Optimize .dockerignore and try again."
            exit 1
        }
    }
    
    # Create source archive (workaround for macOS Azure CLI bug)
    $archivePath = New-SourceArchive
    
    Write-Host ""
    Write-Host "   ┌─────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
    Write-Host "   │  📤 UPLOADING TO AZURE CONTAINER REGISTRY               │" -ForegroundColor Cyan
    Write-Host "   │                                                         │" -ForegroundColor Cyan
    Write-Host ("   │  Files: {0,-10}  Size: {1,-20}│" -f $uploadInfo.FileCount, $uploadInfo.SizeFormatted) -ForegroundColor Cyan
    Write-Host "   │                                                         │" -ForegroundColor Cyan
    Write-Host "   │  Using pre-built archive (macOS compatibility fix)      │" -ForegroundColor Cyan
    Write-Host "   │  Build progress will appear below...                    │" -ForegroundColor Cyan
    Write-Host "   └─────────────────────────────────────────────────────────┘" -ForegroundColor Cyan
    Write-Host ""
    
    # Note about potential pause
    Write-Info "Azure CLI does not show upload progress."
    Write-Info "Upload should complete within 30 seconds for small archives."
    Write-Host ""

    if ($DryRun) {
        Write-DryRun "az acr build --registry $($script:Config.AcrName) --image 'zuke-video-shorts:latest' --file 'Dockerfile.azure' ."
        return
    }
    
    # Run the build using current directory
    $buildStart = Get-Date
    
    Write-Info "Starting ACR build (this may take 5-10 minutes)..."
    Write-Detail "If upload hangs for more than 2 minutes, press Ctrl+C and try again"
    Write-Host ""
    
    # Azure CLI will create its own archive internally and handle the upload
    # Using --no-wait would be faster but we need to wait for the build
    $env:AZURE_CORE_COLLECT_TELEMETRY = "false"
    
    az acr build `
        --registry $script:Config.AcrName `
        --image 'zuke-video-shorts:latest' `
        --file 'Dockerfile.azure' `
        --platform linux/amd64 `
        --timeout 1800 `
        .
    
    $buildEnd = Get-Date
    $buildDuration = $buildEnd - $buildStart
    
    # Clean up the archive (still useful for size estimates)
    if (Test-Path $archivePath) {
        Remove-Item $archivePath -Force
        Write-Detail "Cleaned up temporary archive"
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Failure "ACR Build failed"
        Write-Host ""
        Write-Host "   Troubleshooting:" -ForegroundColor Yellow
        Write-Detail "• Check Dockerfile.azure syntax"
        Write-Detail "• Verify requirements-cpu.txt exists"
        Write-Detail "• Check Azure Portal > ACR > Tasks for logs"
        Write-Detail "• Run: az acr task list-runs --registry $($script:Config.AcrName) --output table"
        exit 1
    }
    
    Write-Host ""
    Write-Host "   ┌─────────────────────────────────────────────────────────┐" -ForegroundColor Green
    Write-Host "   │  ✅ BUILD SUCCESSFUL                                    │" -ForegroundColor Green
    Write-Host "   │                                                         │" -ForegroundColor Green
    Write-Host ("   │  Duration: {0,-43}│" -f ("{0:N1} minutes" -f $buildDuration.TotalMinutes)) -ForegroundColor Green
    Write-Host "   │  Image: zuke-video-shorts:latest                        │" -ForegroundColor Green
    Write-Host "   └─────────────────────────────────────────────────────────┘" -ForegroundColor Green
}

function Build-WithLocalDocker {
    Write-Step "Building Docker image locally..." "🐳"

    # Login to ACR
    Write-Info "Logging into ACR..."

    if (-not $DryRun) {
        az acr login --name $script:Config.AcrName
        if (-not (Test-CommandSuccess -ErrorMessage "ACR login failed" -ExitOnError)) {
            return
        }
    }
    else {
        Write-DryRun "az acr login --name $($script:Config.AcrName)"
    }

    # Build image
    $imageName = "$($script:AcrServer)/zuke-video-shorts:latest"

    Write-Info "Building image: $imageName"
    $buildSuccess = Invoke-DockerCommand `
        -Command "build -f Dockerfile.azure -t '$imageName' ." `
        -Description "Docker build failed"

    if (-not $buildSuccess -and -not $DryRun) {
        exit 1
    }

    # Push image
    Write-Info "Pushing image to ACR..."
    $pushSuccess = Invoke-DockerCommand `
        -Command "push '$imageName'" `
        -Description "Docker push failed"

    if (-not $pushSuccess -and -not $DryRun) {
        exit 1
    }

    Write-Success "Image built and pushed to ACR"
}

# ============================================================================
# DEPLOYMENT FUNCTIONS
# ============================================================================

function Deploy-Container {
    param([hashtable]$EnvFile)

    Write-Step "Deploying to Azure Container Instances..." "🚀"

    # Check if container exists and handle recreation
    $containerExists = Invoke-AzCommand `
        -Command "container show --resource-group $($script:Config.ResourceGroup) --name $($script:Config.ContainerName) --query name -o tsv" `
        -Description "Check container" `
        -CaptureOutput `
        -SuppressError

    if ($containerExists -and $containerExists -ne "[DRY-RUN-VALUE]") {
        if ($Recreate) {
            Write-Info "Deleting existing container for recreation..."

            Invoke-AzCommand `
                -Command "container delete --resource-group $($script:Config.ResourceGroup) --name $($script:Config.ContainerName) --yes" `
                -Description "Delete container" `
                -ExitOnError

            Write-Success "Existing container deleted"

            # Wait a moment for deletion to complete
            if (-not $DryRun) {
                Start-Sleep -Seconds 5
            }
        }
        else {
            Write-WarningMsg "Container already exists. Use -Recreate to update."
            Write-Info "Skipping container creation..."

            # Get existing container info
            $script:ContainerFqdn = Invoke-AzCommand `
                -Command "container show --resource-group $($script:Config.ResourceGroup) --name $($script:Config.ContainerName) --query ipAddress.fqdn -o tsv" `
                -Description "Get container FQDN" `
                -CaptureOutput

            $script:ContainerIp = Invoke-AzCommand `
                -Command "container show --resource-group $($script:Config.ResourceGroup) --name $($script:Config.ContainerName) --query ipAddress.ip -o tsv" `
                -Description "Get container IP" `
                -CaptureOutput

            return
        }
    }

    # Get ACR credentials
    Write-Info "Getting ACR credentials..."

    $acrUser = Invoke-AzCommand `
        -Command "acr credential show --name $($script:Config.AcrName) --query username -o tsv" `
        -Description "Get ACR username" `
        -CaptureOutput

    $acrPassword = Invoke-AzCommand `
        -Command "acr credential show --name $($script:Config.AcrName) --query passwords[0].value -o tsv" `
        -Description "Get ACR password" `
        -CaptureOutput

    # Build environment variables - separate regular and secure
    $regularEnvVars = @(
        "AZURE_OPENAI_ENDPOINT=$($EnvFile['AZURE_OPENAI_ENDPOINT'])",
        "AZURE_OPENAI_DEPLOYMENT_NAME=$($EnvFile['AZURE_OPENAI_DEPLOYMENT_NAME'])",
        "AZURE_OPENAI_API_VERSION=$($EnvFile['AZURE_OPENAI_API_VERSION'] ?? '2024-02-01')",
        "AZURE_STORAGE_ACCOUNT_NAME=$($EnvFile['AZURE_STORAGE_ACCOUNT_NAME'])",
        "AZURE_STORAGE_CONTAINER_NAME=$($EnvFile['AZURE_STORAGE_CONTAINER_NAME'])"
    )

    $secureEnvVars = @(
        "AZURE_OPENAI_API_KEY=$($EnvFile['AZURE_OPENAI_API_KEY'])",
        "AZURE_STORAGE_ACCOUNT_KEY=$($EnvFile['AZURE_STORAGE_ACCOUNT_KEY'])"
    )

    # Add SAS token if using private storage
    if ($PrivateStorage -and $EnvFile.ContainsKey('AZURE_STORAGE_SAS_TOKEN')) {
        $secureEnvVars += "AZURE_STORAGE_SAS_TOKEN=$($EnvFile['AZURE_STORAGE_SAS_TOKEN'])"
    }

    # Generate DNS label
    $dnsLabel = "$ResourcePrefix-video-$(Get-Random -Maximum 9999)"

    # Build image name
    $imageName = "$($script:AcrServer)/zuke-video-shorts:latest"

    Write-Info "Deploying container..."
    Write-Detail "Image: $imageName"
    Write-Detail "DNS Label: $dnsLabel"
    Write-Detail "CPU: $($script:Config.ContainerCpu) cores"
    Write-Detail "Memory: $($script:Config.ContainerMemory) GB"

    # Build the command (PowerShell array for readability)
    $regularEnvVarsString = ($regularEnvVars | ForEach-Object { "`"$_`"" }) -join " "
    $secureEnvVarsString = ($secureEnvVars | ForEach-Object { "`"$_`"" }) -join " "

    $deployCommand = @(
        "container create",
        "--resource-group $($script:Config.ResourceGroup)",
        "--name $($script:Config.ContainerName)",
        "--image '$imageName'",
        "--registry-login-server '$($script:AcrServer)'",
        "--registry-username '$acrUser'",
        "--registry-password '$acrPassword'",
        "--dns-name-label '$dnsLabel'",
        "--ports $($script:Config.ContainerPort)",
        "--cpu $($script:Config.ContainerCpu)",
        "--memory $($script:Config.ContainerMemory)",
        "--restart-policy Always",
        "--environment-variables $regularEnvVarsString",
        "--secure-environment-variables $secureEnvVarsString"
    ) -join " "

    Invoke-AzCommand `
        -Command $deployCommand `
        -Description "Container deployment failed" `
        -ExitOnError

    Write-Success "Container deployed"

    # Get container info
    $script:ContainerFqdn = Invoke-AzCommand `
        -Command "container show --resource-group $($script:Config.ResourceGroup) --name $($script:Config.ContainerName) --query ipAddress.fqdn -o tsv" `
        -Description "Get container FQDN" `
        -CaptureOutput

    $script:ContainerIp = Invoke-AzCommand `
        -Command "container show --resource-group $($script:Config.ResourceGroup) --name $($script:Config.ContainerName) --query ipAddress.ip -o tsv" `
        -Description "Get container IP" `
        -CaptureOutput
}

# ============================================================================
# SUMMARY FUNCTIONS
# ============================================================================

function Save-DeploymentInfo {
    param([hashtable]$EnvFile)

    if ($DryRun) {
        Write-Info "Deployment info would be saved to $($script:Config.DeploymentInfoFile)"
        return
    }

    $baseUrl = "http://$($script:ContainerFqdn):$($script:Config.ContainerPort)"
    $storageUrl = "https://$($EnvFile['AZURE_STORAGE_ACCOUNT_NAME']).blob.core.windows.net/$($EnvFile['AZURE_STORAGE_CONTAINER_NAME'])/"

    $deploymentInfo = @{
        DeployedAt        = (Get-Date).ToString("o")
        ResourceGroup     = $script:Config.ResourceGroup
        Location          = $script:Config.Location
        AcrName           = $script:Config.AcrName
        AcrServer         = $script:AcrServer
        ContainerName     = $script:Config.ContainerName
        StorageAccount    = $EnvFile['AZURE_STORAGE_ACCOUNT_NAME']
        StorageContainer  = $EnvFile['AZURE_STORAGE_CONTAINER_NAME']
        PrivateStorage    = $PrivateStorage.IsPresent
        PublicURL         = $baseUrl
        PublicIP          = $script:ContainerIp
        FQDN              = $script:ContainerFqdn
        APIEndpoint       = "$baseUrl/process"
        HealthCheck       = "$baseUrl/"
        VideoStorageURL   = $storageUrl
    }

    $deploymentInfo | ConvertTo-Json -Depth 3 | Out-File -FilePath $script:Config.DeploymentInfoFile -Encoding UTF8

    # Also save config for future runs
    Save-DeploymentConfig -ConfigData @{
        ResourceGroup      = $script:Config.ResourceGroup
        AcrName            = $script:Config.AcrName
        StorageAccountName = $EnvFile['AZURE_STORAGE_ACCOUNT_NAME']
        ContainerName      = $script:Config.ContainerName
        LastDeployed       = (Get-Date).ToString("o")
    }

    # Add config files to gitignore
    Add-ToGitignore $script:Config.ConfigFile
    Add-ToGitignore $script:Config.DeploymentInfoFile
}

function Show-Summary {
    param([hashtable]$EnvFile)

    $baseUrl = "http://$($script:ContainerFqdn):$($script:Config.ContainerPort)"
    $storageUrl = "https://$($EnvFile['AZURE_STORAGE_ACCOUNT_NAME']).blob.core.windows.net/$($EnvFile['AZURE_STORAGE_CONTAINER_NAME'])/"

    # Get container state
    $containerState = Invoke-AzCommand `
        -Command "container show --resource-group $($script:Config.ResourceGroup) --name $($script:Config.ContainerName) --query instanceView.state -o tsv" `
        -Description "Get container state" `
        -CaptureOutput

    $stateColor = switch ($containerState) {
        "Running" { "Green" }
        "Pending" { "Yellow" }
        "Stopped" { "Red" }
        default { "White" }
    }

    Write-Banner "🎉 DEPLOYMENT COMPLETE!" "Green"

    Write-Host ""
    Write-Host "📊 DEPLOYMENT STATUS" -ForegroundColor Yellow
    Write-Host "   Container State:    " -NoNewline
    Write-Host "$containerState" -ForegroundColor $stateColor
    Write-Host ""

    Write-Host "🌐 ENDPOINTS" -ForegroundColor Yellow
    Write-Host "   Public URL:         " -NoNewline -ForegroundColor White
    Write-Host "$baseUrl" -ForegroundColor Cyan
    Write-Host "   API Endpoint:       " -NoNewline -ForegroundColor White
    Write-Host "$baseUrl/process" -ForegroundColor Cyan
    Write-Host "   Health Check:       " -NoNewline -ForegroundColor White
    Write-Host "$baseUrl/" -ForegroundColor Cyan
    Write-Host "   Video Storage:      " -NoNewline -ForegroundColor White
    Write-Host "$storageUrl" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "🔧 RESOURCES" -ForegroundColor Yellow
    Write-Host "   Resource Group:     $($script:Config.ResourceGroup)" -ForegroundColor White
    Write-Host "   Container Registry: $($script:Config.AcrName)" -ForegroundColor White
    Write-Host "   Storage Account:    $($EnvFile['AZURE_STORAGE_ACCOUNT_NAME'])" -ForegroundColor White
    Write-Host "   Container:          $($script:Config.ContainerName)" -ForegroundColor White
    Write-Host ""

    if ($PrivateStorage) {
        Write-Host "🔒 SECURITY" -ForegroundColor Yellow
        Write-Host "   Storage Mode:       Private (SAS token required)" -ForegroundColor Green
        Write-Host "   Secrets:            Stored as secure environment variables" -ForegroundColor Green
        Write-Host ""
    }
    else {
        Write-Host "⚠️  SECURITY NOTES" -ForegroundColor Yellow
        Write-Host "   Storage Mode:       Public (videos are accessible by URL)" -ForegroundColor Yellow
        Write-Host "   Secrets:            Stored as secure environment variables" -ForegroundColor Green
        Write-Host "   Tip:                Use -PrivateStorage for production" -ForegroundColor Yellow
        Write-Host ""
    }

    Write-Host "📋 NEXT STEPS" -ForegroundColor Yellow
    Write-Host "   1. Wait for container to start (1-2 minutes)" -ForegroundColor White
    Write-Host "   2. Test health: " -NoNewline -ForegroundColor White
    Write-Host "curl $baseUrl/" -ForegroundColor DarkGray
    Write-Host "   3. Update n8n HTTP Request URL to: " -NoNewline -ForegroundColor White
    Write-Host "$baseUrl/process" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "💡 USEFUL COMMANDS" -ForegroundColor Yellow
    Write-Host "   View logs:    " -NoNewline -ForegroundColor White
    Write-Host "az container logs -g $($script:Config.ResourceGroup) -n $($script:Config.ContainerName)" -ForegroundColor DarkGray
    Write-Host "   Stream logs:  " -NoNewline -ForegroundColor White
    Write-Host "az container logs -g $($script:Config.ResourceGroup) -n $($script:Config.ContainerName) --follow" -ForegroundColor DarkGray
    Write-Host "   Restart:      " -NoNewline -ForegroundColor White
    Write-Host "az container restart -g $($script:Config.ResourceGroup) -n $($script:Config.ContainerName)" -ForegroundColor DarkGray
    Write-Host "   Redeploy:     " -NoNewline -ForegroundColor White
    Write-Host "./deploy-to-azure.ps1 -Recreate" -ForegroundColor DarkGray
    Write-Host "   Cleanup:      " -NoNewline -ForegroundColor White
    Write-Host "./deploy-to-azure.ps1 -Cleanup" -ForegroundColor DarkGray
    Write-Host ""

    Write-Host "💾 Files saved:" -ForegroundColor Green
    Write-Host "   • $($script:Config.DeploymentInfoFile) - Deployment details" -ForegroundColor White
    Write-Host "   • $($script:Config.ConfigFile) - Resource names (for updates)" -ForegroundColor White
    if (-not $PrivateStorage) {
        Write-Host "   • $($script:Config.CredentialsFile) - Storage credentials" -ForegroundColor White
    }
    Write-Host ""
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

# Handle cleanup mode first
if ($Cleanup) {
    Invoke-Cleanup
    exit 0
}

# Display header
Write-Banner "🚀 AZURE DEPLOYMENT: Zuke Video Shorts Creator"

# Show mode indicators
$modes = @()
if ($DryRun) { $modes += "DRY RUN" }
if ($UseLocalDocker) { $modes += "LOCAL DOCKER" } else { $modes += "ACR BUILD" }
if ($PrivateStorage) { $modes += "PRIVATE STORAGE" }
if ($Recreate) { $modes += "RECREATE" }

if ($modes.Count -gt 0) {
    Write-Host ""
    Write-Host "   Mode: [$($modes -join '] [')]" -ForegroundColor Magenta
}

# Detect macOS and show note
if (Test-IsMacOS) {
    Write-Host ""
    Write-Host "   Platform: macOS (using archive upload for compatibility)" -ForegroundColor DarkGray
}

# Step 1: Validate prerequisites
Test-Prerequisites

# Step 2: Load and validate environment variables
$envFile = Read-EnvFile -Path ".env"
Test-EnvironmentVariables -EnvFile $envFile

# Set default API version if not specified
if (-not $envFile.ContainsKey('AZURE_OPENAI_API_VERSION') -or
    [string]::IsNullOrWhiteSpace($envFile['AZURE_OPENAI_API_VERSION'])) {
    $envFile['AZURE_OPENAI_API_VERSION'] = '2024-02-01'
}

# Step 3: Create/verify resource group
New-ResourceGroup

# Step 4: Create/verify ACR
New-ContainerRegistry

# Step 5: Create/verify storage account
$envFile = New-StorageAccount -EnvFile $envFile

# Step 6: Build Docker image
if ($UseLocalDocker) {
    Build-WithLocalDocker
}
else {
    Build-WithACR
}

# Step 7: Deploy container
Deploy-Container -EnvFile $envFile

# Step 8: Save deployment info
Save-DeploymentInfo -EnvFile $envFile

# Step 9: Show summary
Show-Summary -EnvFile $envFile

Write-Host ""