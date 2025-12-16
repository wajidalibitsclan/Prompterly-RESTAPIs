"""
File service for managing file uploads and storage
Supports AWS S3, DigitalOcean Spaces, and Local Storage
"""
import os
import shutil
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile
from typing import Optional
import logging
from datetime import datetime
import mimetypes
import uuid
from pathlib import Path

from app.core.config import settings
from app.db.models.file import File
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class FileService:
    """File service for S3 and Local storage operations"""

    def __init__(self):
        """Initialize storage client based on configuration"""
        self.storage_type = settings.STORAGE_TYPE.lower()

        if self.storage_type == "s3":
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=settings.S3_ENDPOINT_URL,
                region_name=settings.AWS_REGION
            )
            self.bucket_name = settings.S3_BUCKET_NAME
        else:
            # Local storage
            self.local_storage_path = Path(settings.LOCAL_STORAGE_PATH)
            self._ensure_storage_directory()

    def _ensure_storage_directory(self):
        """Ensure local storage directory exists"""
        self.local_storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Local storage directory: {self.local_storage_path.absolute()}")

    async def upload_file(
        self,
        file: UploadFile,
        user_id: int,
        db: Session,
        folder: str = "uploads"
    ) -> File:
        """
        Upload file to storage and save metadata to database

        Args:
            file: Uploaded file
            user_id: Owner user ID
            db: Database session
            folder: Storage folder path

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
            date_path = datetime.utcnow().strftime('%Y/%m/%d')
            storage_path = f"{folder}/{date_path}/{unique_filename}"

            # Determine content type
            content_type = file.content_type
            if not content_type:
                content_type, _ = mimetypes.guess_type(file.filename)
            if not content_type:
                content_type = 'application/octet-stream'

            if self.storage_type == "s3":
                # Upload to S3
                await file.seek(0)
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
            else:
                # Upload to local storage
                full_path = self.local_storage_path / storage_path
                full_path.parent.mkdir(parents=True, exist_ok=True)

                with open(full_path, 'wb') as f:
                    f.write(content)

                logger.info(f"File saved locally: {full_path}")

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

            logger.info(f"File uploaded: {storage_path} by user {user_id} (storage: {self.storage_type})")

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
        Generate URL for file download

        Args:
            file_id: File ID
            db: Database session
            expiration: URL expiration time in seconds (S3 only)

        Returns:
            URL string

        Raises:
            ValueError: If file not found
        """
        file = db.query(File).filter(File.id == file_id).first()

        if not file:
            raise ValueError("File not found")

        try:
            if self.storage_type == "s3":
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': file.storage_path
                    },
                    ExpiresIn=expiration
                )
            else:
                # Local storage - return relative URL to be served by FastAPI
                url = f"/files/{file.storage_path}"

            return url

        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise Exception("Failed to generate download URL")

    async def get_file_path(self, file_id: int, db: Session) -> Optional[str]:
        """
        Get the local file path for a file (local storage only)

        Args:
            file_id: File ID
            db: Database session

        Returns:
            Full file path string or None
        """
        file = db.query(File).filter(File.id == file_id).first()

        if not file:
            return None

        if self.storage_type == "local":
            return str(self.local_storage_path / file.storage_path)

        return None

    async def get_file_content(self, file_id: int, db: Session) -> Optional[bytes]:
        """
        Get file content directly

        Args:
            file_id: File ID
            db: Database session

        Returns:
            File content bytes or None
        """
        file = db.query(File).filter(File.id == file_id).first()

        if not file:
            return None

        try:
            if self.storage_type == "s3":
                response = self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=file.storage_path
                )
                return response['Body'].read()
            else:
                full_path = self.local_storage_path / file.storage_path
                if full_path.exists():
                    with open(full_path, 'rb') as f:
                        return f.read()
                return None
        except Exception as e:
            logger.error(f"Error reading file content: {str(e)}")
            return None

    async def delete_file(
        self,
        file_id: int,
        user_id: int,
        db: Session
    ) -> bool:
        """
        Delete file from storage and database

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
            if self.storage_type == "s3":
                # Delete from S3
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=file.storage_path
                )
            else:
                # Delete from local storage
                full_path = self.local_storage_path / file.storage_path
                if full_path.exists():
                    full_path.unlink()
                    logger.info(f"Local file deleted: {full_path}")

            # Delete from database
            db.delete(file)
            db.commit()

            logger.info(f"File deleted: {file.storage_path} by user {user_id}")

            return True

        except ClientError as e:
            logger.error(f"S3 delete error: {str(e)}")
            raise Exception(f"Failed to delete file from storage: {str(e)}")
        except Exception as e:
            logger.error(f"File delete error: {str(e)}")
            raise

    async def delete_file_by_path(self, storage_path: str) -> bool:
        """
        Delete file from storage by path (no database operation)

        Args:
            storage_path: Storage path of the file

        Returns:
            True if successful
        """
        try:
            if self.storage_type == "s3":
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=storage_path
                )
            else:
                full_path = self.local_storage_path / storage_path
                if full_path.exists():
                    full_path.unlink()
                    logger.info(f"Local file deleted: {full_path}")

            return True
        except Exception as e:
            logger.error(f"Error deleting file by path: {str(e)}")
            return False

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
