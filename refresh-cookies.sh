#!/bin/bash

# Quick script to refresh YouTube cookies from browser
# This extracts cookies directly from your browser and saves them

set -e

COOKIES_FILE="youtube_cookies.txt"
BACKUP_FILE="youtube_cookies.txt.backup.$(date +%Y%m%d_%H%M%S)"
TEST_VIDEO="https://www.youtube.com/watch?v=dQw4w9WgXcQ"

echo "🍪 YouTube Cookies Refresher"
echo "=============================="
echo ""

# Detect browser
BROWSER=""
if [ -d "$HOME/Library/Application Support/Google/Chrome" ]; then
    BROWSER="chrome"
    echo "📌 Detected browser: Chrome"
elif [ -d "$HOME/Library/Application Support/Firefox" ]; then
    BROWSER="firefox"
    echo "📌 Detected browser: Firefox"
elif [ -d "$HOME/Library/Application Support/Microsoft Edge" ]; then
    BROWSER="edge"
    echo "📌 Detected browser: Edge"
elif [ -d "$HOME/Library/Application Support/BraveSoftware/Brave-Browser" ]; then
    BROWSER="brave"
    echo "📌 Detected browser: Brave"
else
    echo "⚠️  Could not auto-detect browser"
    echo ""
    echo "Available browsers: chrome, firefox, edge, brave, safari"
    read -p "Enter your browser name: " BROWSER
fi

# Backup existing cookies
if [ -f "$COOKIES_FILE" ]; then
    echo "📦 Backing up existing cookies to: $BACKUP_FILE"
    cp "$COOKIES_FILE" "$BACKUP_FILE"
fi

# Extract cookies
echo "🔄 Extracting cookies from $BROWSER..."
echo "   (This may take a moment)"
echo ""

if yt-dlp --cookies-from-browser "$BROWSER" --cookies "$COOKIES_FILE" --skip-download "$TEST_VIDEO" 2>&1 | grep -q "ERROR"; then
    echo "❌ Failed to extract cookies from $BROWSER"
    echo ""
    echo "Possible solutions:"
    echo "1. Make sure $BROWSER is installed and you're signed in to YouTube"
    echo "2. Close $BROWSER and try again (some browsers lock the cookie database)"
    echo "3. Export cookies manually using browser extension (see UPDATE-COOKIES-GUIDE.md)"
    
    if [ -f "$BACKUP_FILE" ]; then
        echo ""
        echo "Restoring backup..."
        cp "$BACKUP_FILE" "$COOKIES_FILE"
    fi
    exit 1
fi

echo "✅ Cookies extracted successfully!"
echo ""

# Validate
echo "🧪 Validating new cookies..."
if ./validate-cookies.sh > /dev/null 2>&1; then
    echo "✅ New cookies are valid!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Test locally if needed"
    echo "2. Deploy to Azure: ./deploy-to-azure.ps1"
    echo "   Or upload just cookies: ./upload-cookies.ps1"
    echo ""
    echo "✨ Done! Your YouTube cookies are fresh."
else
    echo "⚠️  Validation had warnings, but cookies were extracted"
    echo "   Try testing them manually"
fi

echo ""
echo "=============================="
