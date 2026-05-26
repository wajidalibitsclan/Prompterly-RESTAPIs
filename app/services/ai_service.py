"""
AI Service for LLM integration
Supports OpenAI GPT-4 and Anthropic Claude
Includes RAG (Retrieval Augmented Generation) support

Data-handling posture (Security Standard §14 — AI Data Boundaries):
User conversations are NOT permitted to train public AI models. By default
the OpenAI and Anthropic APIs (non-fine-tuning endpoints) do not retain or
train on submitted prompts, but the binding opt-out lives in each
provider's organisation console — not in this SDK. This module:

  - Refuses to boot in production unless `AI_DATA_OPT_OUT=True`.
  - Logs the configured posture at startup so it appears in audit logs.
  - Passes a *hashed* user identifier on every request (the raw `user_uuid`
    is never shared with a third party) so abuse-monitoring on the provider
    side can be tied to an account without leaking pseudonymous IDs.

Operators must additionally confirm in the provider consoles:
  - OpenAI: data sharing disabled + ZDR enabled if available
  - Anthropic: Zero Data Retention enabled for the workspace
"""
from typing import List, Dict, Optional, Tuple, AsyncGenerator
import hashlib
import hmac
import logging
import json
from openai import AsyncOpenAI
import numpy as np
from anthropic import AsyncAnthropic

from app.core.config import settings

logger = logging.getLogger(__name__)


def _safe_user_id(user_uuid: Optional[str]) -> Optional[str]:
    """
    Hash a user_uuid into a stable, non-reversible identifier safe to send
    to third-party AI providers for abuse monitoring.

    Uses HMAC-SHA256 with the application secret as the key, so the hash
    space changes if our secret rotates — a provider can correlate within
    a deployment but not across deployments / leaks.
    """
    if not user_uuid:
        return None
    secret = (settings.JWT_SECRET_KEY or "ai-pii-pepper").encode("utf-8")
    digest = hmac.new(secret, user_uuid.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"prompterly:{digest[:32]}"


class AIService:
    """AI Service for chat completions and embeddings. Claude is the default provider."""

    def __init__(self):
        """Initialize AI clients — Claude primary, OpenAI for embeddings"""
        self._assert_data_posture()

        # Claude (primary for chat)
        if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY != "sk-ant-your-anthropic-key":
            self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            self.anthropic_client = None

        # OpenAI (for embeddings + fallback). Passing `organization` binds
        # every request to a specific OpenAI org so the dashboard-level
        # data-sharing opt-out applies even if the API key was provisioned
        # with multi-org access.
        self.openai_client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            organization=settings.OPENAI_ORG_ID,
        )

    @staticmethod
    def _assert_data_posture() -> None:
        """Refuse to start in production without the no-training posture set."""
        if settings.AI_DATA_OPT_OUT:
            logger.info(
                "AI data posture: OPT-OUT of training. Operator must also "
                "confirm provider consoles (OpenAI data sharing off, "
                "Anthropic ZDR on). OpenAI org=%s",
                settings.OPENAI_ORG_ID or "<unset>",
            )
            if settings.APP_ENV == "production" and not settings.OPENAI_ORG_ID:
                # In production we want the org binding because the OpenAI
                # opt-out is per-org. Warn loudly so it surfaces in audit
                # review without blocking the boot.
                logger.warning(
                    "AI data posture: production deployment has no "
                    "OPENAI_ORG_ID set. The opt-out cannot be guaranteed "
                    "to bind to the right org — set OPENAI_ORG_ID."
                )
        else:
            if settings.APP_ENV == "production":
                raise RuntimeError(
                    "Refusing to boot: AI_DATA_OPT_OUT must be True in "
                    "production (Security Standard §14). Set AI_DATA_OPT_OUT=True "
                    "in the environment and confirm provider-console opt-out."
                )
            logger.warning(
                "AI data posture: OPT-OUT disabled. User content may be "
                "retained by AI providers. Acceptable only in non-prod."
            )
    
    async def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        context: Optional[str] = None,
        use_anthropic: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        user_uuid: Optional[str] = None,
    ) -> Tuple[str, Dict]:
        """
        Generate AI chat response. Defaults to Claude.

        Args:
            messages: List of message dicts with 'role' and 'content'
            context: Optional RAG context to inject
            use_anthropic: Use Anthropic Claude (default True). Set False for OpenAI.
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            user_uuid: Optional caller user_uuid. Hashed before being sent
                       to the provider — see `_safe_user_id`.

        Returns:
            Tuple of (response_text, metadata)
        """
        try:
            # Inject context if provided
            if context:
                context_message = {
                    "role": "system",
                    "content": f"Use the following context to inform your responses:\n\n{context}"
                }
                messages = [context_message] + messages

            # Default to Claude, fall back to OpenAI
            if use_anthropic and self.anthropic_client:
                return await self._generate_anthropic_response(
                    messages, temperature, max_tokens, user_uuid=user_uuid,
                )
            else:
                return await self._generate_openai_response(
                    messages, temperature, max_tokens, user_uuid=user_uuid,
                )

        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            raise

    async def _generate_openai_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        user_uuid: Optional[str] = None,
    ) -> Tuple[str, Dict]:
        """Generate response using OpenAI GPT-4"""
        kwargs: Dict = {
            "model": settings.OPENAI_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        safe_uid = _safe_user_id(user_uuid)
        if safe_uid:
            # OpenAI `user` field — documented as used only for abuse
            # detection, not training (and training is opted out at the
            # org level — see module docstring).
            kwargs["user"] = safe_uid

        response = await self.openai_client.chat.completions.create(**kwargs)

        content = response.choices[0].message.content

        metadata = {
            "model": settings.OPENAI_MODEL,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "finish_reason": response.choices[0].finish_reason
        }

        return content, metadata

    async def _generate_anthropic_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        user_uuid: Optional[str] = None,
    ) -> Tuple[str, Dict]:
        """Generate response using Anthropic Claude"""
        # Extract system message if present
        system_message = None
        filtered_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                filtered_messages.append(msg)

        kwargs: Dict = {
            "model": settings.ANTHROPIC_MODEL,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_message,
            "messages": filtered_messages,
        }
        safe_uid = _safe_user_id(user_uuid)
        if safe_uid:
            # Anthropic accepts a `metadata.user_id` for abuse monitoring;
            # like OpenAI's `user`, training is opted out at the org level.
            kwargs["metadata"] = {"user_id": safe_uid}

        response = await self.anthropic_client.messages.create(**kwargs)

        content = response.content[0].text

        metadata = {
            "model": settings.ANTHROPIC_MODEL,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            },
            "stop_reason": response.stop_reason
        }

        return content, metadata

    async def generate_chat_response_stream(
        self,
        messages: List[Dict[str, str]],
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        user_uuid: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate AI chat response with streaming. Uses Claude by default.

        Args:
            messages: List of message dicts with 'role' and 'content'
            context: Optional RAG context to inject
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            user_uuid: Optional caller user_uuid; hashed before send.

        Yields:
            Chunks of response text as they arrive
        """
        try:
            # Inject context if provided
            if context:
                context_message = {
                    "role": "system",
                    "content": f"Use the following context to inform your responses:\n\n{context}"
                }
                messages = [context_message] + messages

            safe_uid = _safe_user_id(user_uuid)

            # Use Claude for streaming if available
            if self.anthropic_client:
                # Separate system message for Claude
                system_message = None
                filtered_messages = []
                for msg in messages:
                    if msg["role"] == "system":
                        system_message = msg["content"]
                    else:
                        filtered_messages.append(msg)

                stream_kwargs: Dict = {
                    "model": settings.ANTHROPIC_MODEL,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "system": system_message or "",
                    "messages": filtered_messages,
                }
                if safe_uid:
                    stream_kwargs["metadata"] = {"user_id": safe_uid}

                async with self.anthropic_client.messages.stream(**stream_kwargs) as stream:
                    async for text in stream.text_stream:
                        yield text
            else:
                # Fallback to OpenAI
                openai_kwargs: Dict = {
                    "model": settings.OPENAI_MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                }
                if safe_uid:
                    openai_kwargs["user"] = safe_uid
                response = await self.openai_client.chat.completions.create(**openai_kwargs)

                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Error generating streaming response: {str(e)}")
            raise

    async def create_embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """
        Create text embedding for RAG
        
        Args:
            text: Text to embed
            model: Optional model override
            
        Returns:
            List of embedding values
        """
        try:
            if not model:
                model = settings.OPENAI_EMBEDDING_MODEL
            
            response = await self.openai_client.embeddings.create(
                model=model,
                input=text
            )
            
            return response.data[0].embedding
        
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}")
            raise
    
    async def create_embeddings_batch(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Create embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            model: Optional model override
            
        Returns:
            List of embedding lists
        """
        try:
            if not model:
                model = settings.OPENAI_EMBEDDING_MODEL
            
            response = await self.openai_client.embeddings.create(
                model=model,
                input=texts
            )
            
            return [item.embedding for item in response.data]
        
        except Exception as e:
            logger.error(f"Error creating embeddings batch: {str(e)}")
            raise
    
    def cosine_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score (0-1)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def find_most_similar(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[Tuple[int, List[float]]],
        top_k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Find most similar embeddings to query
        
        Args:
            query_embedding: Query embedding
            candidate_embeddings: List of (id, embedding) tuples
            top_k: Number of top results to return
            
        Returns:
            List of (id, similarity_score) tuples, sorted by similarity
        """
        similarities = []
        
        for item_id, embedding in candidate_embeddings:
            similarity = self.cosine_similarity(query_embedding, embedding)
            similarities.append((item_id, similarity))
        
        # Sort by similarity score (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    async def summarize_text(
        self,
        text: str,
        max_length: int = 200,
        use_anthropic: bool = False
    ) -> str:
        """
        Summarize long text
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length in words
            use_anthropic: Use Anthropic Claude
            
        Returns:
            Summary text
        """
        messages = [
            {
                "role": "user",
                "content": f"Summarize the following text in about {max_length} words:\n\n{text}"
            }
        ]
        
        summary, _ = await self.generate_chat_response(
            messages=messages,
            use_anthropic=use_anthropic,
            max_tokens=max_length * 2  # Account for tokenization
        )
        
        return summary
    
    async def extract_keywords(
        self,
        text: str,
        num_keywords: int = 10
    ) -> List[str]:
        """
        Extract keywords from text
        
        Args:
            text: Text to analyze
            num_keywords: Number of keywords to extract
            
        Returns:
            List of keywords
        """
        messages = [
            {
                "role": "user",
                "content": f"Extract {num_keywords} key topics or keywords from the following text. Return only the keywords, separated by commas:\n\n{text}"
            }
        ]
        
        response, _ = await self.generate_chat_response(
            messages=messages,
            temperature=0.3,
            max_tokens=100
        )
        
        # Parse comma-separated keywords
        keywords = [kw.strip() for kw in response.split(",")]
        return keywords[:num_keywords]


# Singleton instance
ai_service = AIService()
