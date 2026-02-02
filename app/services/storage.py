"""
Storage service for audio files
Supports both local storage and S3
"""

import os
import uuid
import aiofiles
from typing import Tuple, Optional
from fastapi import UploadFile

from app.config import settings


class StorageService:
    """Handle audio file storage"""
    
    def __init__(self):
        self.use_s3 = settings.USE_S3
        self.local_path = settings.LOCAL_STORAGE_PATH
        
        # Create local storage directory if needed
        if not self.use_s3:
            os.makedirs(self.local_path, exist_ok=True)
    
    async def save_audio_file(
        self,
        file: UploadFile,
        meeting_id: str,
    ) -> Tuple[str, Optional[str]]:
        """
        Save audio file and return (file_path, file_url)
        
        Args:
            file: Uploaded audio file
            meeting_id: Associated meeting ID
            
        Returns:
            Tuple of (file_path, file_url)
        """
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1]
        filename = f"{meeting_id}_{uuid.uuid4()}{file_ext}"
        
        if self.use_s3:
            # Upload to S3
            file_path = await self._save_to_s3(file, filename)
            file_url = self._get_s3_url(filename)
        else:
            # Save locally
            file_path = await self._save_locally(file, filename)
            file_url = None
        
        return file_path, file_url
    
    async def _save_locally(self, file: UploadFile, filename: str) -> str:
        """Save file to local filesystem"""
        file_path = os.path.join(self.local_path, filename)
        
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        return file_path
    
    async def _save_to_s3(self, file: UploadFile, filename: str) -> str:
        """Upload file to S3"""
        try:
            import boto3
            
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
            )
            
            content = await file.read()
            s3_client.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=f"audio/{filename}",
                Body=content,
                ContentType=file.content_type,
            )
            
            return f"s3://{settings.AWS_STORAGE_BUCKET_NAME}/audio/{filename}"
        except Exception as e:
            raise Exception(f"Failed to upload to S3: {str(e)}")
    
    def _get_s3_url(self, filename: str) -> str:
        """Get public S3 URL"""
        return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/audio/{filename}"
    
    def delete_file(self, file_path: str) -> bool:
        """Delete audio file"""
        try:
            if file_path.startswith("s3://"):
                # Delete from S3
                import boto3
                s3_client = boto3.client("s3")
                bucket = file_path.split("/")[2]
                key = "/".join(file_path.split("/")[3:])
                s3_client.delete_object(Bucket=bucket, Key=key)
            else:
                # Delete from local filesystem
                if os.path.exists(file_path):
                    os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return False
    
    def get_file_path(self, file_path: str) -> str:
        """Get local file path (download from S3 if needed)"""
        if file_path.startswith("s3://"):
            # Download from S3 to temp location
            import boto3
            import tempfile
            
            s3_client = boto3.client("s3")
            bucket = file_path.split("/")[2]
            key = "/".join(file_path.split("/")[3:])
            
            # Create temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".audio")
            s3_client.download_file(bucket, key, temp_file.name)
            
            return temp_file.name
        else:
            return file_path
