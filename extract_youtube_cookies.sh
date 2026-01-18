#!/bin/bash
# Extract YouTube cookies for yt-dlp
# Usage: ./extract_youtube_cookies.sh [chrome|firefox|safari|edge]

BROWSER=${1:-chrome}
OUTPUT_FILE="youtube_cookies.txt"

echo "🍪 Extracting YouTube cookies from $BROWSER..."
echo ""
echo "Prerequisites:"
echo "  1. You must be signed into YouTube in $BROWSER"
echo "  2. yt-dlp must be installed (pip install yt-dlp)"
echo ""

# Check if yt-dlp is installed
if ! command -v yt-dlp &> /dev/null; then
    echo "❌ yt-dlp is not installed!"
    echo "   Install it with: pip install yt-dlp"
    exit 1
fi

echo "✓ yt-dlp found"
echo ""
echo "Extracting cookies..."

# Extract cookies using yt-dlp
yt-dlp --cookies-from-browser "$BROWSER" --cookies "$OUTPUT_FILE" "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --skip-download 2>&1 | grep -v "Downloading"

if [ -f "$OUTPUT_FILE" ]; then
    echo ""
    echo "✅ Success! Cookies saved to: $OUTPUT_FILE"
    echo ""
    echo "📋 Cookie file info:"
    wc -l "$OUTPUT_FILE"
    echo ""
    echo "🔐 SECURITY REMINDER:"
    echo "   - Never commit this file to Git"
    echo "   - Store securely (Azure Key Vault recommended)"
    echo "   - Rotate every 30 days"
    echo ""
    echo "📤 Next steps:"
    echo "   1. Test locally: python3 main.py --auto-approve <youtube-url>"
    echo "   2. Deploy to Azure (see YOUTUBE-COOKIES-GUIDE.md)"
else
    echo ""
    echo "❌ Failed to extract cookies"
    echo ""
    echo "Troubleshooting:"
    echo "  - Make sure you're signed into YouTube in $BROWSER"
    echo "  - Try a different browser: chrome, firefox, safari, edge"
    echo "  - On Linux with Flatpak Chrome, use:"
    echo "    yt-dlp --cookies-from-browser 'chrome:~/.var/app/com.google.Chrome' --cookies cookies.txt ..."
    exit 1
fi
