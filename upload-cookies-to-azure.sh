#!/bin/bash

# Upload YouTube Cookies to Azure Blob Storage
# This script uploads the cookies file to Azure so it's available to the containerized app

set -e

COOKIES_FILE="youtube_cookies.txt"
STORAGE_ACCOUNT="zukestorage3833"
CONTAINER="config"
BLOB_NAME="youtube_cookies.txt"

echo "🚀 YouTube Cookies Upload to Azure"
echo "==================================="
echo ""

# Check if cookies file exists
if [ ! -f "$COOKIES_FILE" ]; then
    echo "❌ Cookies file not found: $COOKIES_FILE"
    echo ""
    echo "Run one of these first:"
    echo "  ./refresh-cookies.sh        # Extract from browser"
    echo "  ./validate-cookies.sh       # Check existing cookies"
    exit 1
fi

# Validate cookies first
echo "🔍 Validating cookies before upload..."
if ! ./validate-cookies.sh > /dev/null 2>&1; then
    echo "⚠️  Cookies validation had issues"
    read -p "Continue with upload anyway? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "Upload cancelled"
        exit 1
    fi
fi

echo "✅ Cookies validated"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found"
    echo "   Install from: https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure"
    echo "   Run: az login"
    exit 1
fi

echo "📤 Uploading cookies to Azure Blob Storage..."
echo "   Storage Account: $STORAGE_ACCOUNT"
echo "   Container: $CONTAINER"
echo "   Blob: $BLOB_NAME"
echo ""

# Upload the cookies file
if az storage blob upload \
    --account-name "$STORAGE_ACCOUNT" \
    --container-name "$CONTAINER" \
    --name "$BLOB_NAME" \
    --file "$COOKIES_FILE" \
    --overwrite \
    --output none 2>&1; then
    
    echo "✅ Upload successful!"
    echo ""
    
    # Get blob properties
    SIZE=$(az storage blob show \
        --account-name "$STORAGE_ACCOUNT" \
        --container-name "$CONTAINER" \
        --name "$BLOB_NAME" \
        --query properties.contentLength \
        --output tsv 2>/dev/null || echo "unknown")
    
    echo "📊 Blob Details:"
    echo "   Size: $SIZE bytes"
    echo "   URL: https://${STORAGE_ACCOUNT}.blob.core.windows.net/${CONTAINER}/${BLOB_NAME}"
    echo ""
    
    # Generate SAS token (valid for 1 year)
    EXPIRY=$(date -u -v+1y +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d "+1 year" +"%Y-%m-%dT%H:%M:%SZ")
    
    echo "🔑 Generating SAS token (expires: $EXPIRY)..."
    SAS=$(az storage blob generate-sas \
        --account-name "$STORAGE_ACCOUNT" \
        --container-name "$CONTAINER" \
        --name "$BLOB_NAME" \
        --permissions r \
        --expiry "$EXPIRY" \
        --output tsv 2>/dev/null || echo "")
    
    if [ -n "$SAS" ]; then
        FULL_URL="https://${STORAGE_ACCOUNT}.blob.core.windows.net/${CONTAINER}/${BLOB_NAME}?${SAS}"
        echo "   SAS URL: $FULL_URL"
        echo ""
        echo "📋 Update Dockerfile.azure with this URL if needed"
    fi
    
    echo ""
    echo "✨ Done! Your containers will now use the updated cookies."
    echo ""
    echo "📋 Next steps:"
    echo "1. Redeploy your app: ./deploy-to-azure.ps1"
    echo "2. Or restart if already deployed: az containerapp revision restart"
    
else
    echo "❌ Upload failed!"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check Azure login: az login"
    echo "2. Verify storage account exists: az storage account show -n $STORAGE_ACCOUNT"
    echo "3. Check container exists: az storage container exists -n $CONTAINER --account-name $STORAGE_ACCOUNT"
    exit 1
fi

echo ""
echo "==================================="
