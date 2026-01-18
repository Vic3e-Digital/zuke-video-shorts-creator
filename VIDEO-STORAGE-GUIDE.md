# 🗄️ Video Storage Configuration

## 📁 **Current Status: Azure Blob Storage Ready**

Your system now supports **Azure Blob Storage** for video file hosting. Here's how it works:

### 🔄 **Video Storage Flow:**

```
Video Processing → Local /output/ folder → Upload to Azure Blob Storage → Return Public URLs
```

### ⚙️ **Configuration Options:**

#### Option 1: ✅ **Azure Blob Storage** (Recommended)
Add these to your `.env` file for automatic cloud storage:

```bash
# Azure Blob Storage Configuration
AZURE_STORAGE_ACCOUNT_NAME=yourstorageaccount
AZURE_STORAGE_ACCOUNT_KEY=your-access-key-here
AZURE_STORAGE_CONTAINER_NAME=video-content
```

**Benefits:**
- ✅ Public URLs accessible from anywhere
- ✅ Persistent storage (videos don't get lost)
- ✅ Integrated with Azure ecosystem
- ✅ Automatic upload after processing

#### Option 2: ⚠️ **Local Storage Only**
If you don't add Azure Storage variables:

**What happens:**
- ❌ Videos stored only inside container
- ❌ Lost when container restarts
- ❌ Not accessible from external systems
- ❌ URLs returned are local paths only

### 🛠️ **Quick Azure Blob Storage Setup:**

1. **Create Storage Account:**
   ```bash
   az storage account create \
     --name yourstorageaccount \
     --resource-group zuke-video-shorts-rg \
     --location "East US" \
     --sku Standard_LRS
   ```

2. **Create Container:**
   ```bash
   az storage container create \
     --name video-content \
     --account-name yourstorageaccount \
     --public-access blob
   ```

3. **Get Access Key:**
   ```bash
   az storage account keys list \
     --account-name yourstorageaccount \
     --query [0].value -o tsv
   ```

4. **Add to .env file:**
   ```bash
   AZURE_STORAGE_ACCOUNT_NAME=yourstorageaccount
   AZURE_STORAGE_ACCOUNT_KEY=your-key-from-step-3
   AZURE_STORAGE_CONTAINER_NAME=video-content
   ```

### 📤 **What Gets Uploaded:**

After video processing, the system will:
1. **Process videos** using your Docker container
2. **Upload all .mp4 files** to Azure Blob Storage
3. **Return public URLs** in the n8n response:

```json
{
  "success": true,
  "output_files": [
    {
      "filename": "video_clip1_subtitled.mp4",
      "url": "https://yourstorageaccount.blob.core.windows.net/video-content/videos/job123/clip1.mp4",
      "storage": "azure_blob"
    }
  ]
}
```

### 🔍 **How n8n Receives Videos:**

Your n8n workflow will receive:
- **Direct download URLs** for each processed video
- **File metadata** (size, type, creation time)
- **Storage location** info (azure_blob or local)

These URLs can be:
- **Downloaded by n8n** for further processing
- **Sent to other systems** via webhooks
- **Stored in databases** for future access
- **Used directly in web applications**

### 💡 **Recommendation:**

**Set up Azure Blob Storage** before deploying to ensure your processed videos are:
- ✅ Permanently accessible
- ✅ Available to n8n and other systems
- ✅ Backed up in Azure cloud
- ✅ Ready for production use