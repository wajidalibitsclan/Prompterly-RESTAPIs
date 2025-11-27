"""
AI Service for LLM integration
Supports OpenAI GPT-4 and Anthropic Claude
Includes RAG (Retrieval Augmented Generation) support
"""
from typing import List, Dict, Optional, Tuple
import logging
from openai import AsyncOpenAI
import numpy as np
from anthropic import AsyncAnthropic

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """AI Service for chat completions and embeddings"""
    
    def __init__(self):
        """Initialize AI clients"""
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        if settings.ANTHROPIC_API_KEY:
            self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            self.anthropic_client = None
    
    async def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        context: Optional[str] = None,
        use_anthropic: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Tuple[str, Dict]:
        """
        Generate AI chat response
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            context: Optional RAG context to inject
            use_anthropic: Use Anthropic Claude instead of OpenAI
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            
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
            
            if use_anthropic and self.anthropic_client:
                return await self._generate_anthropic_response(
                    messages, temperature, max_tokens
                )
            else:
                return await self._generate_openai_response(
                    messages, temperature, max_tokens
                )
        
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            raise
    
    async def _generate_openai_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> Tuple[str, Dict]:
        """Generate response using OpenAI GPT-4"""
        response = await self.openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
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
        max_tokens: int
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
        
        response = await self.anthropic_client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_message,
            messages=filtered_messages
        )
        
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
