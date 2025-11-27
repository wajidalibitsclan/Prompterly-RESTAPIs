"""
File service for managing file uploads and storage
Supports AWS S3 and DigitalOcean Spaces
"""
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile
from typing import Optional
import logging
from datetime import datetime, timedelta
import mimetypes
import uuid

from app.core.config import settings
from app.db.models.file import File
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class FileService:
    """File service for S3 operations"""
    
    def __init__(self):
        """Initialize S3 client"""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.S3_ENDPOINT_URL,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
    
    async def upload_file(
        self,
        file: UploadFile,
        user_id: int,
        db: Session,
        folder: str = "uploads"
    ) -> File:
        """
        Upload file to S3 and save metadata to database
        
        Args:
            file: Uploaded file
            user_id: Owner user ID
            db: Database session
            folder: S3 folder path
            
        Returns:
            File model instance
            
        Raises:
            Exception: If upload fails
        """
        try:
            # Validate file size
            content = await file.read()
            file_size = len(content)
            
            if file_size > settings.max_file_size_bytes:
                raise ValueError(
                    f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds "
                    f"maximum allowed ({settings.MAX_FILE_SIZE_MB}MB)"
                )
            
            # Validate file type
            file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
            if file_ext not in settings.allowed_file_extensions:
                raise ValueError(
                    f"File type '.{file_ext}' not allowed. "
                    f"Allowed types: {', '.join(settings.allowed_file_extensions)}"
                )
            
            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}_{file.filename}"
            storage_path = f"{folder}/{datetime.utcnow().strftime('%Y/%m/%d')}/{unique_filename}"
            
            # Determine content type
            content_type = file.content_type
            if not content_type:
                content_type, _ = mimetypes.guess_type(file.filename)
            if not content_type:
                content_type = 'application/octet-stream'
            
            # Upload to S3
            await file.seek(0)  # Reset file pointer
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=storage_path,
                Body=content,
                ContentType=content_type,
                Metadata={
                    'user_id': str(user_id),
                    'original_filename': file.filename
                }
            )
            
            # Create database record
            file_record = File(
                owner_user_id=user_id,
                storage_path=storage_path,
                mime_type=content_type,
                size_bytes=file_size
            )
            
            db.add(file_record)
            db.commit()
            db.refresh(file_record)
            
            logger.info(f"File uploaded: {storage_path} by user {user_id}")
            
            return file_record
        
        except ClientError as e:
            logger.error(f"S3 upload error: {str(e)}")
            raise Exception(f"Failed to upload file to storage: {str(e)}")
        except Exception as e:
            logger.error(f"File upload error: {str(e)}")
            raise
    
    async def get_file_url(
        self,
        file_id: int,
        db: Session,
        expiration: int = 3600
    ) -> str:
        """
        Generate presigned URL for file download
        
        Args:
            file_id: File ID
            db: Database session
            expiration: URL expiration time in seconds
            
        Returns:
            Presigned URL string
            
        Raises:
            ValueError: If file not found
        """
        file = db.query(File).filter(File.id == file_id).first()
        
        if not file:
            raise ValueError("File not found")
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file.storage_path
                },
                ExpiresIn=expiration
            )
            
            return url
        
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise Exception("Failed to generate download URL")
    
    async def delete_file(
        self,
        file_id: int,
        user_id: int,
        db: Session
    ) -> bool:
        """
        Delete file from S3 and database
        
        Args:
            file_id: File ID
            user_id: User ID (for authorization)
            db: Database session
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If file not found or unauthorized
        """
        file = db.query(File).filter(File.id == file_id).first()
        
        if not file:
            raise ValueError("File not found")
        
        if file.owner_user_id != user_id:
            raise ValueError("Unauthorized to delete this file")
        
        try:
            # Delete from S3
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file.storage_path
            )
            
            # Delete from database
            db.delete(file)
            db.commit()
            
            logger.info(f"File deleted: {file.storage_path} by user {user_id}")
            
            return True
        
        except ClientError as e:
            logger.error(f"S3 delete error: {str(e)}")
            raise Exception(f"Failed to delete file from storage: {str(e)}")
    
    async def get_file_info(
        self,
        file_id: int,
        db: Session
    ) -> Optional[File]:
        """
        Get file metadata
        
        Args:
            file_id: File ID
            db: Database session
            
        Returns:
            File model instance or None
        """
        return db.query(File).filter(File.id == file_id).first()
    
    def validate_file_type(self, filename: str) -> bool:
        """
        Validate if file type is allowed
        
        Args:
            filename: File name
            
        Returns:
            True if allowed
        """
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
        return file_ext in settings.allowed_file_extensions
    
    def get_file_category(self, mime_type: str) -> str:
        """
        Categorize file by mime type
        
        Args:
            mime_type: MIME type string
            
        Returns:
            Category string (image/video/audio/document/other)
        """
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type in [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ]:
            return 'document'
        else:
            return 'other'


# Singleton instance
file_service = FileService()
