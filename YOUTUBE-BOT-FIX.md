# 🔥 URGENT FIX: YouTube Bot Detection Error

## Problem
YouTube is blocking your video downloads with:
```
Sign in to confirm you're not a bot
```

## Root Cause
Your `youtube_cookies.txt` file in Azure Blob Storage is **expired or invalid**. YouTube cookies typically expire after 30 days.

## ✅ Quick Fix (3 Steps)

### Step 1: Export Fresh Cookies from Browser

**Option A: Use Browser Extension (EASIEST)**

1. Install extension:
   - **Chrome**: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - **Firefox**: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. Sign in to YouTube:
   - Open youtube.com in your browser
   - Sign in with your Google account  
   - Watch a video to verify it works

3. Export cookies:
   - Go to youtube.com
   - Click the extension icon
   - Click "Export" or "Download"
   - Save to your project folder as `youtube_cookies.txt`

**Option B: Extract from Browser with yt-dlp**

```bash
# Make sure Chrome/Firefox is CLOSED first!
yt-dlp --cookies-from-browser chrome --cookies youtube_cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Step 2: Validate Cookies Locally

```bash
./validate-cookies.sh
```

You should see:
```
✅ Cookies test PASSED!
Your cookies are working! ✨
```

### Step 3: Upload to Azure

```bash
# Make sure you're logged in to Azure
az login

# Upload the new cookies
./upload-cookies-to-azure.sh
```

Then redeploy:
```bash
./deploy-to-azure.ps1
```

---

## 🧪 Test Your Fix

After redeploying, test with the same video:
```bash
curl -X POST https://your-app-url/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=cSEEQ2ZRIng",
    "clips_to_generate": 1
  }'
```

---

## 🛠️ Scripts Included

| Script | Purpose |
|--------|---------|
| `validate-cookies.sh` | Check if cookies are valid |
| `refresh-cookies.sh` | Extract cookies from browser |
| `upload-cookies-to-azure.sh` | Upload to Azure Blob Storage |

---

## 🔒 Security Reminder

- ⚠️ **Cookies = Your YouTube session**
- Never commit `youtube_cookies.txt` to Git
- It's already in `.gitignore`
- Refresh every 30 days
- Use a dedicated account if possible

---

## 🐛 Troubleshooting

### "Still getting bot detection after update"

1. **Wait 5 minutes** - Azure needs time to pull new cookies
2. **Restart container**:
   ```bash
   az containerapp revision restart --name <your-app> --resource-group <rg>
   ```
3. **Check logs** to confirm new cookies loaded:
   ```bash
   az containerapp logs show --name <your-app> --resource-group <rg>
   ```

### "HTTP Error 400: Bad Request"

Line ending issue. Fix with:
```bash
dos2unix youtube_cookies.txt
# or
sed -i 's/\r$//' youtube_cookies.txt
```

### "Cookies extracted but still failing"

1. Your account might be flagged - try different account
2. Update yt-dlp: `pip install --upgrade yt-dlp`
3. Some videos have stricter protection - try another video

### "Can't extract from browser"

Browser must be **completely closed** when extracting cookies. The browser locks its cookie database while running.

---

## 📚 More Info

- Full guide: [UPDATE-COOKIES-GUIDE.md](UPDATE-COOKIES-GUIDE.md)
- YouTube cookies FAQ: [YOUTUBE-COOKIES-GUIDE.md](YOUTUBE-COOKIES-GUIDE.md)
- yt-dlp FAQ: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp

---

## ⏱️ Maintenance Schedule

Set a reminder to refresh cookies:
- **Every 30 days** (before they expire)
- **When you see bot detection errors**
- **After YouTube updates** (occasionally breaks things)

---

**Need help?** Check the [UPDATE-COOKIES-GUIDE.md](UPDATE-COOKIES-GUIDE.md) for detailed instructions.
