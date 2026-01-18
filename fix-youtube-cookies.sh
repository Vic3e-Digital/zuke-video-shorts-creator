#!/bin/bash

# One-Command YouTube Cookie Fix
# Guides you through the entire process

set -e

echo "🔥 YouTube Bot Detection - One-Command Fix"
echo "==========================================="
echo ""
echo "This script will guide you through fixing YouTube bot detection."
echo ""

# Step 1: Check current cookies
echo "Step 1/3: Checking current cookies..."
if [ -f "youtube_cookies.txt" ]; then
    echo "✅ Cookies file exists"
    
    # Quick validation
    if head -n 1 youtube_cookies.txt | grep -q "Netscape HTTP Cookie File"; then
        echo "✅ Format looks valid"
    else
        echo "❌ Invalid format - will need to replace"
    fi
else
    echo "❌ No cookies file found"
fi

echo ""
echo "Step 2/3: Get fresh cookies"
echo "----------------------------"
echo ""
echo "You need to export fresh cookies from your browser."
echo ""
echo "Choose your method:"
echo "  1. Browser Extension (RECOMMENDED - works best)"
echo "  2. yt-dlp extraction (requires browser closed)"
echo "  3. I already have a fresh cookies file"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "📝 Browser Extension Method:"
        echo ""
        echo "1. Install extension:"
        echo "   Chrome: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc"
        echo "   Firefox: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/"
        echo ""
        echo "2. Go to youtube.com and sign in"
        echo ""
        echo "3. Click the extension icon and export cookies"
        echo ""
        echo "4. Save the file as 'youtube_cookies.txt' in this directory:"
        echo "   $(pwd)"
        echo ""
        read -p "Press Enter when you've saved the file..."
        ;;
    2)
        echo ""
        echo "⚠️  Make sure your browser is COMPLETELY CLOSED!"
        read -p "Press Enter when ready..."
        
        echo ""
        echo "Attempting to extract cookies..."
        ./refresh-cookies.sh || {
            echo ""
            echo "❌ Extraction failed. Try method 1 instead (browser extension)"
            exit 1
        }
        ;;
    3)
        echo ""
        echo "✅ Using existing cookies file"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

# Step 3: Validate
echo ""
echo "Step 3/3: Validating cookies..."
echo "----------------------------"
if ./validate-cookies.sh; then
    echo ""
    echo "✅ Cookies are valid!"
else
    echo ""
    echo "❌ Cookies validation failed"
    echo "   Please try again with method 1 (browser extension)"
    exit 1
fi

# Step 4: Upload to Azure
echo ""
echo "Step 4/3 (Bonus): Upload to Azure"
echo "----------------------------"
echo ""
read -p "Upload to Azure now? (y/N): " upload

if [[ "$upload" =~ ^[Yy]$ ]]; then
    if ! command -v az &> /dev/null; then
        echo "❌ Azure CLI not found"
        echo "   Install from: https://docs.microsoft.com/cli/azure/install-azure-cli"
        exit 1
    fi
    
    if ! az account show &> /dev/null; then
        echo "🔐 Logging in to Azure..."
        az login
    fi
    
    ./upload-cookies-to-azure.sh
    
    echo ""
    echo "📦 Deploying to Azure..."
    read -p "Run ./deploy-to-azure.ps1 now? (y/N): " deploy
    
    if [[ "$deploy" =~ ^[Yy]$ ]]; then
        ./deploy-to-azure.ps1
    else
        echo ""
        echo "📋 Remember to deploy when ready:"
        echo "   ./deploy-to-azure.ps1"
    fi
else
    echo ""
    echo "📋 To upload later, run:"
    echo "   ./upload-cookies-to-azure.sh"
fi

echo ""
echo "==========================================="
echo "✨ All done! Your YouTube cookies are fresh."
echo ""
echo "🧪 Test your app now with a YouTube video."
echo ""
