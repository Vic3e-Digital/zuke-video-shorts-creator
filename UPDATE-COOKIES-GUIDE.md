# 🍪 YouTube Cookies Update Guide

YouTube is blocking your requests with "Sign in to confirm you're not a bot" because your cookies are expired or invalid.

## Quick Fix: Update Your Cookies

### Option 1: Export Fresh Cookies (RECOMMENDED)

1. **Install Browser Extension**
   - Chrome: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
   
   ⚠️ Make sure to use "LOCALLY" version - the old "Get cookies.txt" was malware!

2. **Sign in to YouTube**
   - Open your browser
   - Go to youtube.com
   - Sign in with your Google account
   - Watch a video to confirm it works

3. **Export Cookies**
   - Click the extension icon
   - Make sure you're on youtube.com
   - Click "Export" or "Download"
   - Save as `youtube_cookies.txt`

4. **Replace Old Cookies File**
   ```bash
   # Replace the old file with your new one
   cp ~/Downloads/youtube_cookies.txt ./youtube_cookies.txt
   ```

5. **Redeploy to Azure** (if using Azure)
   ```bash
   ./deploy-to-azure.ps1
   ```

### Option 2: Use Browser Cookies Directly (Development Only)

For local development, you can extract cookies directly from your browser:

```bash
# Set environment variable before running
export YOUTUBE_COOKIES_BROWSER=chrome  # or firefox, edge, safari, brave
```

Then run your application. yt-dlp will extract cookies from your browser automatically.

⚠️ **Note**: This only works on your local machine where the browser is installed.

### Option 3: Manual Cookie Export with yt-dlp

You can also use yt-dlp itself to export cookies:

```bash
# Extract cookies from Chrome and save to file
yt-dlp --cookies-from-browser chrome --cookies youtube_cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# This will save cookies to youtube_cookies.txt
```

## Verify Your Cookies File

Your `youtube_cookies.txt` file should:
- Start with `# Netscape HTTP Cookie File` or `# HTTP Cookie File`
- Have Unix-style line endings (LF, not CRLF)
- Include YouTube-specific cookies (.youtube.com entries)

```bash
# Check first line
head -n 1 youtube_cookies.txt

# Should output: # Netscape HTTP Cookie File
```

## Convert Line Endings (if needed)

If you're on Windows and getting "HTTP Error 400":

```bash
# Convert CRLF to LF
dos2unix youtube_cookies.txt

# Or use sed
sed -i 's/\r$//' youtube_cookies.txt
```

## Troubleshooting

### Still Getting Bot Detection?

1. **Update yt-dlp** (critical!)
   ```bash
   pip install --upgrade yt-dlp
   ```

2. **Wait a few minutes** - YouTube may have temporarily flagged your IP

3. **Try a different video** - some videos have stricter access controls

4. **Check your cookies are fresh** - they expire after ~30 days

### Error: "HTTP Error 400: Bad Request"

Your cookies file has wrong line endings. See "Convert Line Endings" above.

### Error: "Unable to extract video info"

Your cookies may be from the wrong domain. Make sure you:
- Exported cookies while on youtube.com (not google.com)
- Are signed in when exporting

## How Often to Update?

- **YouTube cookies expire** after ~30 days of inactivity
- **Update when you see bot detection errors**
- **Pro tip**: Set a reminder to refresh monthly

## Security Note

⚠️ Your cookies file contains your YouTube session. Keep it secure:
- Don't commit it to public repositories (it's in .gitignore)
- Don't share it with others
- Regenerate if exposed

## Azure Deployment

After updating your cookies locally, upload to Azure:

```bash
# Upload new cookies file
./upload-cookies.ps1

# Or include in deployment
./deploy-to-azure.ps1
```

The file will be mounted at `/app/youtube_cookies.txt` in the container.
