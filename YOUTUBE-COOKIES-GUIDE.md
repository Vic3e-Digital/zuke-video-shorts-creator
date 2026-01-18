# YouTube Cookies Setup Guide

YouTube requires authentication to prevent bot abuse. Follow these steps to extract cookies from your browser.

## 🍪 Method 1: Using Browser Extension (Easiest)

### Chrome/Edge:
1. Install [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Go to [youtube.com](https://youtube.com) and sign in
3. Click the extension icon
4. Click "Export" → Save as `youtube_cookies.txt`
5. Upload to Azure Storage or include in deployment

### Firefox:
1. Install [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
2. Go to [youtube.com](https://youtube.com) and sign in
3. Click the extension icon
4. Save the file as `youtube_cookies.txt`

## 🔧 Method 2: Using yt-dlp CLI

```bash
# Export cookies from Chrome
yt-dlp --cookies-from-browser chrome --cookies youtube_cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Or from Firefox
yt-dlp --cookies-from-browser firefox --cookies youtube_cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Or from Safari
yt-dlp --cookies-from-browser safari --cookies youtube_cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

## 📦 Deploying Cookies to Azure

### Option 1: Azure Key Vault (Recommended)
```bash
# Store cookies as secret
az keyvault secret set \
  --vault-name zuke-keyvault \
  --name youtube-cookies \
  --file youtube_cookies.txt

# Update deployment to fetch from Key Vault
```

### Option 2: Include in Docker Build
```dockerfile
# Add to Dockerfile.azure
COPY youtube_cookies.txt /app/youtube_cookies.txt
```

### Option 3: Azure Blob Storage
```bash
# Upload cookies file
az storage blob upload \
  --account-name zukevideostorage \
  --container-name config \
  --name youtube_cookies.txt \
  --file youtube_cookies.txt

# Download at runtime in azure_api.py
```

## 🔐 Security Notes

⚠️ **Cookie files contain sensitive authentication tokens!**

- Never commit to Git
- Add to `.gitignore`
- Use Azure Key Vault or secure storage
- Rotate cookies regularly (every 30 days)
- Use a dedicated YouTube account

## 📝 Cookie File Format

The file should look like:
```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	1234567890	CONSENT	YES+1
.youtube.com	TRUE	/	FALSE	1234567890	VISITOR_INFO1_LIVE	abcdef
```

## ✅ Testing Locally

```bash
# Test with your cookies
python3 -c "from Components.YoutubeDownloader import download_youtube_video; download_youtube_video('https://www.youtube.com/watch?v=6mPFWSDysyI')"
```

## 🚀 Next Steps

1. Extract cookies using Method 1 or 2
2. Test locally to confirm it works
3. Deploy to Azure using one of the secure storage options
4. Update your deployment
