"""
Background Task Service for handling async jobs like embedding generation
"""
import asyncio
import logging
import re
from html.parser import HTMLParser
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models.background_job import BackgroundJob, JobStatus, JobType
from app.db.models.knowledge_base import KBPrompt, KBDocument, KBDocumentChunk, KBFaq
from app.services.ai_service import ai_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class HTMLTextExtractor(HTMLParser):
    """Extract plain text from HTML content"""
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_data = False

    def handle_starttag(self, tag, attrs):
        # Add line breaks for block elements
        if tag in ['p', 'div', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'tr']:
            self.text_parts.append('\n')
        # Skip script and style content
        if tag in ['script', 'style']:
            self.skip_data = True

    def handle_endtag(self, tag):
        if tag in ['script', 'style']:
            self.skip_data = False
        # Add extra line break after headings and paragraphs
        if tag in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.text_parts.append('\n')

    def handle_data(self, data):
        if not self.skip_data:
            self.text_parts.append(data)

    def get_text(self):
        text = ''.join(self.text_parts)
        # Clean up multiple newlines and spaces
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()


def strip_html_tags(html_content: str) -> str:
    """Strip HTML tags and return plain text"""
    if not html_content:
        return ""

    # Quick check if there are any HTML tags
    if '<' not in html_content:
        return html_content

    try:
        parser = HTMLTextExtractor()
        parser.feed(html_content)
        return parser.get_text()
    except Exception as e:
        logger.warning(f"Error parsing HTML, falling back to regex: {e}")
        # Fallback to simple regex stripping
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

# Store for active background tasks
_active_tasks: Dict[int, asyncio.Task] = {}


class BackgroundTaskService:
    """Service for managing background tasks"""

    def create_job(
        self,
        db: Session,
        job_type: JobType,
        entity_type: str = None,
        entity_id: int = None,
        created_by_id: int = None,
        total_steps: int = 1
    ) -> BackgroundJob:
        """Create a new background job"""
        job = BackgroundJob(
            job_type=job_type,
            entity_type=entity_type,
            entity_id=entity_id,
            created_by_id=created_by_id,
            total_steps=total_steps,
            status=JobStatus.PENDING
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    def get_job(self, db: Session, job_id: int) -> Optional[BackgroundJob]:
        """Get a job by ID"""
        return db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()

    def get_active_jobs(
        self,
        db: Session,
        entity_type: str = None,
        entity_id: int = None
    ) -> list:
        """Get active (pending/processing) jobs"""
        query = db.query(BackgroundJob).filter(
            BackgroundJob.status.in_([JobStatus.PENDING, JobStatus.PROCESSING])
        )
        if entity_type:
            query = query.filter(BackgroundJob.entity_type == entity_type)
        if entity_id:
            query = query.filter(BackgroundJob.entity_id == entity_id)
        return query.order_by(BackgroundJob.created_at.desc()).all()

    def get_recent_jobs(
        self,
        db: Session,
        limit: int = 10,
        job_type: JobType = None
    ) -> list:
        """Get recent jobs"""
        query = db.query(BackgroundJob)
        if job_type:
            query = query.filter(BackgroundJob.job_type == job_type)
        return query.order_by(BackgroundJob.created_at.desc()).limit(limit).all()

    async def process_prompt_embedding(
        self,
        db_session_factory,
        job_id: int,
        prompt_id: int
    ):
        """Process prompt embedding in background"""
        db = db_session_factory()
        try:
            job = self.get_job(db, job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return

            job.mark_processing()
            job.current_step = "Generating embedding..."
            db.commit()

            # Get prompt
            prompt = db.query(KBPrompt).filter(KBPrompt.id == prompt_id).first()
            if not prompt:
                job.mark_failed("Prompt not found")
                db.commit()
                return

            # Step 1: Prepare text (strip HTML tags for embedding)
            job.update_progress(1, 3, "Preparing content...")
            db.commit()
            await asyncio.sleep(0.1)  # Small delay for UI update

            # Strip HTML tags from content for clean embedding text
            clean_content = strip_html_tags(prompt.content)
            text = f"{prompt.title}\n{clean_content}"
            if prompt.description:
                clean_description = strip_html_tags(prompt.description)
                text += f"\n{clean_description}"

            # Step 2: Generate embedding
            job.update_progress(2, 3, "Generating embedding vector...")
            db.commit()

            embedding = await ai_service.create_embedding(text)

            # Step 3: Store embedding
            job.update_progress(3, 3, "Storing embedding...")
            db.commit()

            prompt.embedding = embedding
            prompt.embedding_model = settings.OPENAI_EMBEDDING_MODEL
            db.commit()

            # Mark completed
            job.mark_completed({
                "prompt_id": prompt_id,
                "embedding_dimensions": len(embedding) if embedding else 0
            })
            db.commit()

            logger.info(f"Successfully generated embedding for prompt {prompt_id}")

        except Exception as e:
            logger.error(f"Error processing prompt embedding: {e}")
            try:
                job = self.get_job(db, job_id)
                if job:
                    job.mark_failed(str(e))
                    db.commit()
            except:
                pass
        finally:
            db.close()

    async def process_document_embeddings(
        self,
        db_session_factory,
        job_id: int,
        document_id: int
    ):
        """Process document embeddings in background"""
        db = db_session_factory()
        try:
            job = self.get_job(db, job_id)
            if not job:
                return

            job.mark_processing()
            db.commit()

            document = db.query(KBDocument).filter(KBDocument.id == document_id).first()
            if not document:
                job.mark_failed("Document not found")
                db.commit()
                return

            # Get chunks
            chunks = db.query(KBDocumentChunk).filter(
                KBDocumentChunk.document_id == document_id
            ).all()

            total_steps = len(chunks) + 2  # chunks + document summary + final
            job.total_steps = total_steps

            # Process each chunk
            for i, chunk in enumerate(chunks):
                job.update_progress(i + 1, total_steps, f"Processing chunk {i + 1}/{len(chunks)}...")
                db.commit()

                try:
                    embedding = await ai_service.create_embedding(chunk.content)
                    chunk.embedding = embedding
                    chunk.embedding_model = settings.OPENAI_EMBEDDING_MODEL
                    db.commit()
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk.id}: {e}")

                await asyncio.sleep(0.05)  # Rate limiting

            # Generate document-level embedding
            job.update_progress(len(chunks) + 1, total_steps, "Generating document summary embedding...")
            db.commit()

            text = f"{document.title}\n"
            if document.description:
                text += f"{document.description}\n"
            if document.summary:
                text += document.summary

            try:
                embedding = await ai_service.create_embedding(text)
                document.embedding = embedding
                document.embedding_model = settings.OPENAI_EMBEDDING_MODEL
                document.is_processed = True
                db.commit()
            except Exception as e:
                logger.error(f"Error generating document embedding: {e}")

            # Complete
            job.mark_completed({
                "document_id": document_id,
                "chunks_processed": len(chunks)
            })
            db.commit()

        except Exception as e:
            logger.error(f"Error processing document embeddings: {e}")
            try:
                job = self.get_job(db, job_id)
                if job:
                    job.mark_failed(str(e))
                    db.commit()
            except:
                pass
        finally:
            db.close()

    async def process_faq_embedding(
        self,
        db_session_factory,
        job_id: int,
        faq_id: int
    ):
        """Process FAQ embedding in background"""
        db = db_session_factory()
        try:
            job = self.get_job(db, job_id)
            if not job:
                return

            job.mark_processing()
            job.current_step = "Generating embedding..."
            db.commit()

            faq = db.query(KBFaq).filter(KBFaq.id == faq_id).first()
            if not faq:
                job.mark_failed("FAQ not found")
                db.commit()
                return

            # Step 1: Prepare text (strip HTML tags for embedding)
            job.update_progress(1, 3, "Preparing Q&A content...")
            db.commit()

            # Strip HTML tags from Q&A for clean embedding text
            clean_question = strip_html_tags(faq.question)
            clean_answer = strip_html_tags(faq.answer)
            text = f"Question: {clean_question}\nAnswer: {clean_answer}"

            # Step 2: Generate embedding
            job.update_progress(2, 3, "Generating embedding vector...")
            db.commit()

            embedding = await ai_service.create_embedding(text)

            # Step 3: Store
            job.update_progress(3, 3, "Storing embedding...")
            db.commit()

            faq.embedding = embedding
            faq.embedding_model = settings.OPENAI_EMBEDDING_MODEL
            db.commit()

            job.mark_completed({
                "faq_id": faq_id,
                "embedding_dimensions": len(embedding) if embedding else 0
            })
            db.commit()

        except Exception as e:
            logger.error(f"Error processing FAQ embedding: {e}")
            try:
                job = self.get_job(db, job_id)
                if job:
                    job.mark_failed(str(e))
                    db.commit()
            except:
                pass
        finally:
            db.close()

    def start_background_task(
        self,
        db_session_factory,
        job_id: int,
        job_type: JobType,
        entity_id: int
    ):
        """Start a background task"""
        if job_type == JobType.PROMPT_EMBEDDING:
            coro = self.process_prompt_embedding(db_session_factory, job_id, entity_id)
        elif job_type == JobType.DOCUMENT_PROCESSING:
            coro = self.process_document_embeddings(db_session_factory, job_id, entity_id)
        elif job_type == JobType.FAQ_EMBEDDING:
            coro = self.process_faq_embedding(db_session_factory, job_id, entity_id)
        else:
            logger.error(f"Unknown job type: {job_type}")
            return

        task = asyncio.create_task(coro)
        _active_tasks[job_id] = task

        # Clean up when done
        def cleanup(t):
            _active_tasks.pop(job_id, None)

        task.add_done_callback(cleanup)


# Singleton instance
background_task_service = BackgroundTaskService()
