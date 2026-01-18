#!/bin/bash

# YouTube Cookies Validator and Refresher
# This script helps validate your cookies file and optionally refresh it

set -e

COOKIES_FILE="youtube_cookies.txt"
TEST_VIDEO="https://www.youtube.com/watch?v=dQw4w9WgXcQ"

echo "🍪 YouTube Cookies Validator"
echo "=============================="
echo ""

# Check if cookies file exists
if [ ! -f "$COOKIES_FILE" ]; then
    echo "❌ Cookies file not found: $COOKIES_FILE"
    echo ""
    echo "Options:"
    echo "1. Export cookies from your browser (see UPDATE-COOKIES-GUIDE.md)"
    echo "2. Use yt-dlp to extract cookies:"
    echo "   yt-dlp --cookies-from-browser chrome --cookies $COOKIES_FILE $TEST_VIDEO"
    exit 1
fi

echo "✅ Cookies file found: $COOKIES_FILE"

# Check file format
FIRST_LINE=$(head -n 1 "$COOKIES_FILE")
if [[ "$FIRST_LINE" == "# Netscape HTTP Cookie File"* ]] || [[ "$FIRST_LINE" == "# HTTP Cookie File"* ]]; then
    echo "✅ Cookies file format is valid"
else
    echo "❌ Invalid cookies file format"
    echo "   First line should be: # Netscape HTTP Cookie File"
    echo "   Found: $FIRST_LINE"
    exit 1
fi

# Check for YouTube cookies
if grep -q ".youtube.com" "$COOKIES_FILE"; then
    echo "✅ YouTube cookies found"
    YOUTUBE_COOKIES=$(grep -c ".youtube.com" "$COOKIES_FILE")
    echo "   Found $YOUTUBE_COOKIES YouTube cookie entries"
else
    echo "❌ No YouTube cookies found in file"
    echo "   Make sure you exported cookies from youtube.com"
    exit 1
fi

# Check line endings
if file "$COOKIES_FILE" | grep -q "CRLF"; then
    echo "⚠️  File has Windows line endings (CRLF)"
    echo "   Converting to Unix line endings (LF)..."
    sed -i.bak 's/\r$//' "$COOKIES_FILE"
    echo "   ✅ Converted (backup saved as ${COOKIES_FILE}.bak)"
else
    echo "✅ Line endings are correct (LF)"
fi

# Test cookies with yt-dlp
echo ""
echo "🧪 Testing cookies with yt-dlp..."
echo "   Video: $TEST_VIDEO"
echo ""

if command -v yt-dlp &> /dev/null; then
    if yt-dlp --cookies "$COOKIES_FILE" --skip-download --print title "$TEST_VIDEO" 2>&1 | grep -q "Sign in to confirm"; then
        echo "❌ Cookies test FAILED - YouTube bot detection"
        echo ""
        echo "Your cookies are expired or invalid. Please refresh them:"
        echo "1. Sign in to YouTube in your browser"
        echo "2. Export fresh cookies using browser extension"
        echo "3. Replace $COOKIES_FILE"
        echo ""
        echo "Or extract directly from browser:"
        echo "   yt-dlp --cookies-from-browser chrome --cookies $COOKIES_FILE $TEST_VIDEO"
        exit 1
    else
        TITLE=$(yt-dlp --cookies "$COOKIES_FILE" --skip-download --print title "$TEST_VIDEO" 2>/dev/null || echo "Unknown")
        echo "✅ Cookies test PASSED!"
        echo "   Successfully accessed: $TITLE"
        echo ""
        echo "Your cookies are working! ✨"
    fi
else
    echo "⚠️  yt-dlp not found, skipping test"
    echo "   Install with: pip install yt-dlp"
fi

echo ""
echo "=============================="
echo "Validation complete!"
