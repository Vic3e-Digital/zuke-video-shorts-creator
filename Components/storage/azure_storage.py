import os
import logging
from typing import Optional, List, BinaryIO
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.identity import DefaultAzureCredential
from datetime import datetime, timedelta
import mimetypes

logger = logging.getLogger(__name__)

class AzureBlobStorageManager:
    """
    Azure Blob Storage manager for handling media files
    """
    
    def __init__(self):
        self.account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "video-content")
        
        if not self.account_name:
            raise ValueError("AZURE_STORAGE_ACCOUNT_NAME environment variable is required")
        
        # Initialize blob service client
        if self.account_key:
            # Use account key authentication
            account_url = f"https://{self.account_name}.blob.core.windows.net"
            self.blob_service_client = BlobServiceClient(
                account_url=account_url,
                credential=self.account_key
            )
        else:
            # Use Azure AD authentication (managed identity or Azure CLI)
            account_url = f"https://{self.account_name}.blob.core.windows.net"
            credential = DefaultAzureCredential()
            self.blob_service_client = BlobServiceClient(
                account_url=account_url,
                credential=credential
            )
        
        # Ensure container exists
        self._ensure_container_exists()
    
    def _ensure_container_exists(self):
        """Create container if it doesn't exist"""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            if not container_client.exists():
                container_client.create_container(public_access='blob')
                logger.info(f"Created container: {self.container_name}")
        except Exception as e:
            logger.error(f"Error ensuring container exists: {str(e)}")
            raise
    
    def upload_file(self, 
                   file_path: str, 
                   blob_name: Optional[str] = None,
                   folder: str = "",
                   overwrite: bool = True) -> str:
        """
        Upload a file to Azure Blob Storage
        
        Args:
            file_path: Local path to the file
            blob_name: Name for the blob (if None, uses filename)
            folder: Folder structure in the container
            overwrite: Whether to overwrite existing blob
            
        Returns:
            Public URL of the uploaded blob
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if blob_name is None:
                blob_name = os.path.basename(file_path)
            
            # Add folder prefix if specified
            if folder:
                blob_name = f"{folder.strip('/')}/{blob_name}"
            
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = "application/octet-stream"
            
            # Upload file
            with open(file_path, 'rb') as data:
                blob_client.upload_blob(
                    data,
                    content_settings={'content_type': content_type},
                    overwrite=overwrite
                )
            
            # Return public URL
            blob_url = blob_client.url
            logger.info(f"Successfully uploaded {file_path} to {blob_url}")
            return blob_url
            
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {str(e)}")
            raise
    
    def upload_stream(self, 
                     data: BinaryIO, 
                     blob_name: str,
                     folder: str = "",
                     content_type: str = "application/octet-stream",
                     overwrite: bool = True) -> str:
        """
        Upload data from a stream to Azure Blob Storage
        
        Args:
            data: Binary data stream
            blob_name: Name for the blob
            folder: Folder structure in the container
            content_type: MIME type of the data
            overwrite: Whether to overwrite existing blob
            
        Returns:
            Public URL of the uploaded blob
        """
        try:
            # Add folder prefix if specified
            if folder:
                blob_name = f"{folder.strip('/')}/{blob_name}"
            
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Upload stream
            blob_client.upload_blob(
                data,
                content_settings={'content_type': content_type},
                overwrite=overwrite
            )
            
            # Return public URL
            blob_url = blob_client.url
            logger.info(f"Successfully uploaded stream to {blob_url}")
            return blob_url
            
        except Exception as e:
            logger.error(f"Error uploading stream to {blob_name}: {str(e)}")
            raise
    
    def download_file(self, blob_name: str, local_path: str) -> str:
        """
        Download a blob to a local file
        
        Args:
            blob_name: Name of the blob to download
            local_path: Local path where the file should be saved
            
        Returns:
            Path to the downloaded file
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Download blob
            with open(local_path, 'wb') as download_file:
                download_file.write(blob_client.download_blob().readall())
            
            logger.info(f"Successfully downloaded {blob_name} to {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"Error downloading blob {blob_name}: {str(e)}")
            raise
    
    def delete_blob(self, blob_name: str) -> bool:
        """
        Delete a blob from storage
        
        Args:
            blob_name: Name of the blob to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            blob_client.delete_blob()
            logger.info(f"Successfully deleted blob: {blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting blob {blob_name}: {str(e)}")
            return False
    
    def list_blobs(self, folder: str = "", name_starts_with: str = "") -> List[dict]:
        """
        List blobs in the container
        
        Args:
            folder: Filter by folder prefix
            name_starts_with: Filter by blob name prefix
            
        Returns:
            List of blob information dictionaries
        """
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # Build prefix for filtering
            prefix = folder.strip('/') + '/' if folder else ""
            prefix += name_starts_with
            
            blobs = []
            for blob in container_client.list_blobs(name_starts_with=prefix or None):
                blobs.append({
                    'name': blob.name,
                    'size': blob.size,
                    'last_modified': blob.last_modified,
                    'content_type': blob.content_settings.content_type if blob.content_settings else None,
                    'url': f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob.name}"
                })
            
            return blobs
            
        except Exception as e:
            logger.error(f"Error listing blobs: {str(e)}")
            raise
    
    def get_blob_url(self, blob_name: str, expiry_hours: int = 24) -> str:
        """
        Get a public URL for a blob (with optional SAS token for private containers)
        
        Args:
            blob_name: Name of the blob
            expiry_hours: Hours until SAS token expires (if needed)
            
        Returns:
            Public URL or SAS URL
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # For public containers, return direct URL
            # For private containers, you'd generate a SAS token here
            return blob_client.url
            
        except Exception as e:
            logger.error(f"Error getting blob URL for {blob_name}: {str(e)}")
            raise
    
    def cleanup_old_files(self, older_than_days: int = 7, folder: str = "temp/") -> int:
        """
        Clean up old temporary files
        
        Args:
            older_than_days: Delete files older than this many days
            folder: Folder to clean up
            
        Returns:
            Number of files deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            deleted_count = 0
            for blob in container_client.list_blobs(name_starts_with=folder):
                if blob.last_modified.replace(tzinfo=None) < cutoff_date:
                    try:
                        blob_client = self.blob_service_client.get_blob_client(
                            container=self.container_name,
                            blob=blob.name
                        )
                        blob_client.delete_blob()
                        deleted_count += 1
                        logger.info(f"Deleted old file: {blob.name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete {blob.name}: {str(e)}")
            
            logger.info(f"Cleanup completed: {deleted_count} files deleted")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return 0

# Singleton instance
_storage_manager = None

def get_storage_manager() -> AzureBlobStorageManager:
    """Get singleton instance of storage manager"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = AzureBlobStorageManager()
    return _storage_manager