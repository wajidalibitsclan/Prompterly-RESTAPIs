"""
Note service for managing notes and time capsules
Includes search and RAG integration
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from datetime import datetime, timedelta, timezone
import logging
import asyncio

from app.db.models.note import Note, TimeCapsule, CapsuleStatus
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)


class NoteService:
    """Service for managing notes and time capsules"""
    
    def __init__(self):
        """Initialize note service"""
        self.ai_service = ai_service
    
    async def create_note(
        self,
        user_id: int,
        title: str,
        content: str,
        db: Session,
        lounge_id: Optional[int] = None,
        section: Optional[str] = None,
        is_pinned: bool = False,
        is_included_in_rag: bool = True,
        tags: List[str] = None
    ) -> Note:
        """
        Create new note

        Args:
            user_id: User ID
            title: Note title
            content: Note content
            db: Database session
            lounge_id: Optional lounge association
            section: Section/category for grouping
            is_pinned: Pin note
            is_included_in_rag: Include in RAG
            tags: List of tags

        Returns:
            Note instance
        """
        note = Note(
            user_id=user_id,
            lounge_id=lounge_id,
            section=section,
            title=title,
            content=content,
            is_pinned=is_pinned,
            is_included_in_rag=is_included_in_rag,
            tags=tags or []
        )
        
        db.add(note)
        db.commit()
        db.refresh(note)

        # Generate embedding for RAG in background (non-blocking)
        if is_included_in_rag:
            asyncio.create_task(self._generate_note_embedding(note.id, title, content))

        return note

    async def _generate_note_embedding(self, note_id: int, title: str, content: str):
        """Generate embedding for note in background (fire and forget)"""
        try:
            embedding_text = f"{title}\n\n{content}"
            embedding = await self.ai_service.create_embedding(embedding_text)
            # Store embedding (in production, use vector DB like Pinecone)
            logger.info(f"Generated embedding for note {note_id}")
        except Exception as e:
            logger.error(f"Error generating embedding for note {note_id}: {str(e)}")
    
    async def update_note(
        self,
        note_id: int,
        user_id: int,
        db: Session,
        section: Optional[str] = None,
        title: Optional[str] = None,
        content: Optional[str] = None,
        is_pinned: Optional[bool] = None,
        is_included_in_rag: Optional[bool] = None,
        tags: Optional[List[str]] = None
    ) -> Note:
        """
        Update note

        Args:
            note_id: Note ID
            user_id: User ID
            db: Database session
            section: New section
            title: New title
            content: New content
            is_pinned: Pin status
            is_included_in_rag: RAG status
            tags: New tags

        Returns:
            Updated Note instance

        Raises:
            ValueError: If note not found or unauthorized
        """
        note = db.query(Note).filter(
            Note.id == note_id,
            Note.user_id == user_id
        ).first()

        if not note:
            raise ValueError("Note not found or access denied")

        if section is not None:
            note.section = section

        if title is not None:
            note.title = title

        if content is not None:
            note.content = content

        if is_pinned is not None:
            note.is_pinned = is_pinned

        if is_included_in_rag is not None:
            note.is_included_in_rag = is_included_in_rag

        if tags is not None:
            note.tags = tags
        
        note.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(note)

        # Regenerate embedding in background if RAG enabled and content changed
        if content is not None and note.is_included_in_rag:
            asyncio.create_task(self._generate_note_embedding(note.id, note.title, note.content))

        return note
    
    async def search_notes(
        self,
        user_id: int,
        query: str,
        db: Session,
        tags: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Note]:
        """
        Search notes
        
        Args:
            user_id: User ID
            query: Search query
            db: Database session
            tags: Filter by tags
            limit: Maximum results
            
        Returns:
            List of matching notes
        """
        # Build base query
        base_query = db.query(Note).filter(Note.user_id == user_id)
        
        # Filter by tags if provided
        if tags:
            # In production, use proper JSON querying
            # For now, simple string matching
            for tag in tags:
                base_query = base_query.filter(
                    Note.tags.contains([tag])
                )
        
        # Search in title and content
        search_term = f"%{query}%"
        results = base_query.filter(
            or_(
                Note.title.ilike(search_term),
                Note.content.ilike(search_term)
            )
        ).order_by(
            Note.is_pinned.desc(),
            Note.updated_at.desc()
        ).limit(limit).all()
        
        return results
    
    async def get_pinned_notes(
        self,
        user_id: int,
        db: Session
    ) -> List[Note]:
        """
        Get pinned notes
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            List of pinned notes
        """
        return db.query(Note).filter(
            Note.user_id == user_id,
            Note.is_pinned == True
        ).order_by(Note.updated_at.desc()).all()
    
    async def get_notes_by_tags(
        self,
        user_id: int,
        tags: List[str],
        db: Session
    ) -> List[Note]:
        """
        Get notes by tags
        
        Args:
            user_id: User ID
            tags: List of tags
            db: Database session
            
        Returns:
            List of notes with matching tags
        """
        query = db.query(Note).filter(Note.user_id == user_id)
        
        for tag in tags:
            query = query.filter(Note.tags.contains([tag]))
        
        return query.order_by(Note.updated_at.desc()).all()
    
    async def delete_note(
        self,
        note_id: int,
        user_id: int,
        db: Session
    ) -> bool:
        """
        Delete note
        
        Args:
            note_id: Note ID
            user_id: User ID
            db: Database session
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If note not found or unauthorized
        """
        note = db.query(Note).filter(
            Note.id == note_id,
            Note.user_id == user_id
        ).first()
        
        if not note:
            raise ValueError("Note not found or access denied")
        
        db.delete(note)
        db.commit()
        
        return True
    
    # Time Capsule methods
    async def create_time_capsule(
        self,
        user_id: int,
        title: str,
        content: str,
        unlock_at: datetime,
        db: Session
    ) -> TimeCapsule:
        """
        Create time capsule
        
        Args:
            user_id: User ID
            title: Capsule title
            content: Capsule content
            unlock_at: Unlock date/time
            db: Database session
            
        Returns:
            TimeCapsule instance
        """
        # Make comparison timezone-aware
        now = datetime.now(timezone.utc)
        # If unlock_at is naive, assume UTC
        if unlock_at.tzinfo is None:
            unlock_at = unlock_at.replace(tzinfo=timezone.utc)
        if unlock_at <= now:
            raise ValueError("Unlock date must be in the future")
        
        capsule = TimeCapsule(
            user_id=user_id,
            title=title,
            content=content,
            unlock_at=unlock_at,
            status=CapsuleStatus.LOCKED
        )
        
        db.add(capsule)
        db.commit()
        db.refresh(capsule)
        
        logger.info(f"Created time capsule {capsule.id} for user {user_id}")
        
        return capsule
    
    async def unlock_capsules(
        self,
        db: Session
    ) -> List[TimeCapsule]:
        """
        Unlock capsules that are ready
        
        This should be called by a background worker
        
        Args:
            db: Database session
            
        Returns:
            List of newly unlocked capsules
        """
        now = datetime.now(timezone.utc)

        # Find locked capsules ready to unlock
        capsules = db.query(TimeCapsule).filter(
            TimeCapsule.status == CapsuleStatus.LOCKED,
            TimeCapsule.unlock_at <= now
        ).all()

        unlocked = []
        for capsule in capsules:
            capsule.status = CapsuleStatus.UNLOCKED
            capsule.updated_at = datetime.now(timezone.utc)
            unlocked.append(capsule)
            
            logger.info(f"Unlocked capsule {capsule.id} for user {capsule.user_id}")
        
        if unlocked:
            db.commit()

        return unlocked

    async def unlock_single_capsule(
        self,
        capsule_id: int,
        user_id: int,
        db: Session
    ) -> TimeCapsule:
        """
        Manually unlock a single capsule if its unlock time has passed

        Args:
            capsule_id: Capsule ID
            user_id: User ID
            db: Database session

        Returns:
            Unlocked TimeCapsule instance

        Raises:
            ValueError: If capsule not found, unauthorized, already unlocked, or time not passed
        """
        capsule = db.query(TimeCapsule).filter(
            TimeCapsule.id == capsule_id,
            TimeCapsule.user_id == user_id
        ).first()

        if not capsule:
            raise ValueError("Time capsule not found or access denied")

        if capsule.status == CapsuleStatus.UNLOCKED:
            raise ValueError("Capsule is already unlocked")

        now = datetime.now(timezone.utc)
        unlock_at = capsule.unlock_at
        if unlock_at.tzinfo is None:
            unlock_at = unlock_at.replace(tzinfo=timezone.utc)

        if unlock_at > now:
            raise ValueError("Cannot unlock capsule before its scheduled time")

        capsule.status = CapsuleStatus.UNLOCKED
        capsule.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(capsule)

        logger.info(f"Manually unlocked capsule {capsule.id} for user {user_id}")

        return capsule

    async def get_user_capsules(
        self,
        user_id: int,
        db: Session,
        status: Optional[CapsuleStatus] = None
    ) -> List[TimeCapsule]:
        """
        Get user's time capsules
        
        Args:
            user_id: User ID
            db: Database session
            status: Filter by status
            
        Returns:
            List of time capsules
        """
        query = db.query(TimeCapsule).filter(
            TimeCapsule.user_id == user_id
        )
        
        if status:
            query = query.filter(TimeCapsule.status == status)
        
        return query.order_by(TimeCapsule.unlock_at.asc()).all()
    
    async def update_capsule(
        self,
        capsule_id: int,
        user_id: int,
        db: Session,
        title: Optional[str] = None,
        content: Optional[str] = None,
        unlock_at: Optional[datetime] = None
    ) -> TimeCapsule:
        """
        Update time capsule (only if still locked)
        
        Args:
            capsule_id: Capsule ID
            user_id: User ID
            db: Database session
            title: New title
            content: New content
            unlock_at: New unlock date
            
        Returns:
            Updated TimeCapsule instance
            
        Raises:
            ValueError: If capsule not found, unauthorized, or already unlocked
        """
        capsule = db.query(TimeCapsule).filter(
            TimeCapsule.id == capsule_id,
            TimeCapsule.user_id == user_id
        ).first()
        
        if not capsule:
            raise ValueError("Time capsule not found or access denied")
        
        if capsule.status != CapsuleStatus.LOCKED:
            raise ValueError("Cannot update unlocked capsule")
        
        if title is not None:
            capsule.title = title
        
        if content is not None:
            capsule.content = content
        
        if unlock_at is not None:
            if unlock_at <= datetime.utcnow():
                raise ValueError("Unlock date must be in the future")
            capsule.unlock_at = unlock_at
        
        capsule.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(capsule)
        
        return capsule
    
    async def delete_capsule(
        self,
        capsule_id: int,
        user_id: int,
        db: Session
    ) -> bool:
        """
        Delete time capsule
        
        Args:
            capsule_id: Capsule ID
            user_id: User ID
            db: Database session
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If capsule not found or unauthorized
        """
        capsule = db.query(TimeCapsule).filter(
            TimeCapsule.id == capsule_id,
            TimeCapsule.user_id == user_id
        ).first()
        
        if not capsule:
            raise ValueError("Time capsule not found or access denied")
        
        db.delete(capsule)
        db.commit()
        
        return True
    
    def get_capsule_days_until_unlock(self, capsule: TimeCapsule) -> Optional[int]:
        """
        Calculate days until capsule unlocks
        
        Args:
            capsule: TimeCapsule instance
            
        Returns:
            Number of days or None if already unlocked
        """
        if capsule.status != CapsuleStatus.LOCKED:
            return None
        
        now = datetime.utcnow()
        delta = capsule.unlock_at - now
        
        return max(0, delta.days)


# Singleton instance
note_service = NoteService()
