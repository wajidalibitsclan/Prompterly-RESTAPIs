"""
Lounge Resource service for managing lounge documents/resources
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import logging
import os

from app.db.models.lounge_resource import LoungeResource
from app.db.models.file import File
from app.db.models.lounge import Lounge
from app.services.file_service import file_service
from fastapi import UploadFile

logger = logging.getLogger(__name__)


class LoungeResourceService:
    """Service for managing lounge resources/documents"""

    def __init__(self):
        """Initialize lounge resource service"""
        self.file_service = file_service

    async def create_resource(
        self,
        lounge_id: int,
        title: str,
        file: UploadFile,
        uploaded_by_user_id: int,
        db: Session,
        description: Optional[str] = None
    ) -> LoungeResource:
        """
        Create new lounge resource with file upload

        Args:
            lounge_id: Lounge ID
            title: Resource title
            file: Uploaded file
            uploaded_by_user_id: User ID who uploaded
            db: Database session
            description: Optional description

        Returns:
            LoungeResource instance

        Raises:
            ValueError: If lounge not found
        """
        # Verify lounge exists
        lounge = db.query(Lounge).filter(Lounge.id == lounge_id).first()
        if not lounge:
            raise ValueError("Lounge not found")

        # Upload file
        file_record = await self.file_service.upload_file(
            file=file,
            user_id=uploaded_by_user_id,
            db=db,
            folder=f"lounge_resources/{lounge_id}"
        )

        # Create resource record
        resource = LoungeResource(
            lounge_id=lounge_id,
            file_id=file_record.id,
            title=title,
            description=description,
            uploaded_by_user_id=uploaded_by_user_id
        )

        db.add(resource)
        db.commit()
        db.refresh(resource)

        logger.info(f"Created lounge resource {resource.id} for lounge {lounge_id}")

        return resource

    async def get_resource(
        self,
        resource_id: int,
        db: Session
    ) -> Optional[LoungeResource]:
        """
        Get resource by ID

        Args:
            resource_id: Resource ID
            db: Database session

        Returns:
            LoungeResource instance or None
        """
        return db.query(LoungeResource).filter(
            LoungeResource.id == resource_id
        ).first()

    async def get_lounge_resources(
        self,
        lounge_id: int,
        db: Session,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[LoungeResource], int]:
        """
        Get all resources for a lounge with pagination

        Args:
            lounge_id: Lounge ID
            db: Database session
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (list of resources, total count)
        """
        # Get total count
        total = db.query(func.count(LoungeResource.id)).filter(
            LoungeResource.lounge_id == lounge_id
        ).scalar()

        # Get paginated results
        offset = (page - 1) * page_size
        resources = db.query(LoungeResource).filter(
            LoungeResource.lounge_id == lounge_id
        ).order_by(
            LoungeResource.created_at.desc()
        ).offset(offset).limit(page_size).all()

        return resources, total

    async def update_resource(
        self,
        resource_id: int,
        db: Session,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> LoungeResource:
        """
        Update resource metadata

        Args:
            resource_id: Resource ID
            db: Database session
            title: New title
            description: New description

        Returns:
            Updated LoungeResource instance

        Raises:
            ValueError: If resource not found
        """
        resource = db.query(LoungeResource).filter(
            LoungeResource.id == resource_id
        ).first()

        if not resource:
            raise ValueError("Resource not found")

        if title is not None:
            resource.title = title

        if description is not None:
            resource.description = description

        resource.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(resource)

        logger.info(f"Updated lounge resource {resource_id}")

        return resource

    async def delete_resource(
        self,
        resource_id: int,
        db: Session
    ) -> bool:
        """
        Delete resource and associated file

        Args:
            resource_id: Resource ID
            db: Database session

        Returns:
            True if successful

        Raises:
            ValueError: If resource not found
        """
        resource = db.query(LoungeResource).filter(
            LoungeResource.id == resource_id
        ).first()

        if not resource:
            raise ValueError("Resource not found")

        # Get file info before deleting resource
        file_id = resource.file_id
        file_record = db.query(File).filter(File.id == file_id).first()

        # Delete resource record
        db.delete(resource)

        # Delete file from storage and database
        if file_record:
            try:
                await self.file_service.delete_file_by_path(file_record.storage_path)
                db.delete(file_record)
            except Exception as e:
                logger.error(f"Error deleting file for resource {resource_id}: {str(e)}")

        db.commit()

        logger.info(f"Deleted lounge resource {resource_id}")

        return True

    async def get_resource_file_url(
        self,
        resource_id: int,
        db: Session
    ) -> Optional[str]:
        """
        Get download URL for resource file

        Args:
            resource_id: Resource ID
            db: Database session

        Returns:
            URL string or None
        """
        resource = db.query(LoungeResource).filter(
            LoungeResource.id == resource_id
        ).first()

        if not resource:
            return None

        return await self.file_service.get_file_url(resource.file_id, db)

    async def get_all_lounges_resources(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        lounge_id: Optional[int] = None
    ) -> Tuple[List[LoungeResource], int]:
        """
        Get all resources (admin use) with optional lounge filter

        Args:
            db: Database session
            page: Page number
            page_size: Items per page
            lounge_id: Optional lounge filter

        Returns:
            Tuple of (list of resources, total count)
        """
        query = db.query(LoungeResource)

        if lounge_id:
            query = query.filter(LoungeResource.lounge_id == lounge_id)

        # Get total count
        total = query.count()

        # Get paginated results
        offset = (page - 1) * page_size
        resources = query.order_by(
            LoungeResource.created_at.desc()
        ).offset(offset).limit(page_size).all()

        return resources, total


# Singleton instance
lounge_resource_service = LoungeResourceService()
