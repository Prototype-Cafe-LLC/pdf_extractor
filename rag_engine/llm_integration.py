"""LLM integration for generating intelligent responses.

This module provides LLM integration capabilities for generating responses
based on RAG-retrieved context, with support for multiple LLM providers.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Represents an LLM response with metadata."""

    answer: str
    sources: list[dict[str, Any]]
    confidence: float
    model_used: str
    tokens_used: int | None = None
    processing_time: float | None = None


class LLMIntegration:
    """Integrates with various LLM providers for response generation."""

    def __init__(
        self, model_type: str = "openai", model_name: str = "gpt-4", lazy_init: bool = True
    ):
        """Initialize the LLM integration.

        Args:
            model_type: Type of LLM provider (openai, anthropic, ollama)
            model_name: Name of the specific model to use
            lazy_init: If True, delay initialization until first use
        """
        self.model_type = model_type
        self.model_name = model_name
        self.llm = None
        self.lazy_init = lazy_init
        self._initialized = False

        if not lazy_init:
            self._initialize_llm()

    def _initialize_llm(self):
        """Initialize the LLM based on configuration."""
        try:
            if self.model_type == "openai":
                self._initialize_openai()
            elif self.model_type == "anthropic":
                self._initialize_anthropic()
            elif self.model_type == "ollama":
                self._initialize_ollama()
            else:
                raise ValueError(f"Unsupported model type: {self.model_type}")

            logger.info(f"Initialized {self.model_type} LLM: {self.model_name}")

        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise

    def _initialize_openai(self):
        """Initialize OpenAI LLM."""
        try:
            from langchain_openai import ChatOpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")

            self.llm = ChatOpenAI(
                model=self.model_name,
                temperature=0.1,  # Low temperature for technical accuracy
                api_key=api_key,
            )

        except ImportError:
            raise ImportError("langchain-openai not installed. Run: pip install langchain-openai")

    def _initialize_anthropic(self):
        """Initialize Anthropic LLM."""
        try:
            from langchain_anthropic import ChatAnthropic

            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")

            self.llm = ChatAnthropic(model=self.model_name, temperature=0.1, api_key=api_key)

        except ImportError:
            raise ImportError(
                "langchain-anthropic not installed. Run: pip install langchain-anthropic"
            )

    def _initialize_ollama(self):
        """Initialize Ollama LLM."""
        try:
            from langchain_ollama import ChatOllama

            self.llm = ChatOllama(model=self.model_name, temperature=0.1)

        except ImportError:
            raise ImportError("langchain-ollama not installed. Run: pip install langchain-ollama")

    def generate_response(
        self, query: str, context_chunks: list[str], sources: list[dict[str, Any]]
    ) -> LLMResponse:
        """Generate intelligent response using RAG context.

        Args:
            query: User query
            context_chunks: Retrieved context chunks
            sources: Source metadata for chunks

        Returns:
            LLMResponse with answer and metadata
        """
        import time

        start_time = time.time()

        # Initialize LLM if using lazy initialization
        if self.lazy_init and not self._initialized:
            try:
                self._initialize_llm()
                self._initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize LLM on first use: {e}")
                return LLMResponse(
                    answer=f"Error: LLM initialization failed. Please check API keys and configuration.\n{str(e)}",
                    sources=sources,
                    confidence=0.0,
                    model_used=self.model_name,
                    processing_time=time.time() - start_time,
                )

        try:
            # Create context-aware prompt
            context_text = "\n\n".join(context_chunks)
            source_info = self._format_sources(sources)

            # Create prompt template
            from langchain.prompts import ChatPromptTemplate

            prompt_template = ChatPromptTemplate.from_messages(
                [("system", self._get_system_prompt()), ("human", self._get_user_prompt_template())]
            )

            messages = prompt_template.format_messages(
                query=query, context=context_text, sources=source_info
            )

            # Generate response
            response = self.llm.invoke(messages)

            processing_time = time.time() - start_time

            # Calculate confidence
            confidence = self._calculate_confidence(context_chunks, query)

            return LLMResponse(
                answer=response.content,
                sources=sources,
                confidence=confidence,
                model_used=self.model_name,
                processing_time=processing_time,
            )

        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return LLMResponse(
                answer=f"Error generating response: {str(e)}",
                sources=sources,
                confidence=0.0,
                model_used=self.model_name,
                processing_time=time.time() - start_time,
            )

    def _get_system_prompt(self) -> str:
        """Get system prompt for technical documentation queries."""
        return """You are a technical documentation assistant specializing in PDF document analysis and retrieval.

        Your role is to:
        1. Provide accurate answers based ONLY on the provided context
        2. Include specific details and examples when relevant
        3. Cite source documents and page numbers when possible
        4. If information is not in the context, clearly state this
        5. Maintain accuracy and avoid speculation
        6. Format code, commands, or technical content in code blocks when appropriate
        7. Provide complete information when available

        Always be precise and factual in your responses."""

    def _get_user_prompt_template(self) -> str:
        """Get user prompt template."""
        return """Question: {query}

Context from technical documentation:
{context}

Source documents: {sources}

Please provide a comprehensive answer based on the context above. Include specific details,
examples, and technical information where relevant. Cite your sources clearly. If the information is not
available in the provided context, clearly state this."""

    def _format_sources(self, sources: list[dict[str, Any]]) -> str:
        """Format source information for the prompt.

        Args:
            sources: List of source metadata

        Returns:
            Formatted source string
        """
        if not sources:
            return "No specific sources available"

        formatted_sources = []
        for source in sources:
            doc_name = source.get("document", "Unknown")
            page_info = source.get("page", "N/A")
            section = source.get("section", "")

            source_line = f"- {doc_name}"
            if page_info != "N/A":
                source_line += f" (Page: {page_info})"
            if section:
                source_line += f" - {section}"

            formatted_sources.append(source_line)

        return "\n".join(formatted_sources)

    def _calculate_confidence(self, context_chunks: list[str], query: str) -> float:
        """Calculate confidence score based on context relevance.

        Args:
            context_chunks: Retrieved context chunks
            query: Original query

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not context_chunks:
            return 0.0

        # Simple heuristic-based confidence calculation
        # Can be enhanced with semantic similarity scoring

        # Factor 1: Number of relevant chunks
        chunk_factor = min(1.0, len(context_chunks) * 0.2)

        # Factor 2: Context length (more context = higher confidence)
        total_length = sum(len(chunk) for chunk in context_chunks)
        length_factor = min(1.0, total_length / 1000)  # Normalize to 1000 chars

        # Factor 3: Query-specific relevance (basic keyword matching)
        query_lower = query.lower()
        relevance_matches = sum(
            1
            for chunk in context_chunks
            if any(word in chunk.lower() for word in query_lower.split())
        )
        relevance_factor = min(1.0, relevance_matches / len(context_chunks))

        # Combine factors
        confidence = (chunk_factor + length_factor + relevance_factor) / 3
        return min(1.0, max(0.0, confidence))

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the loaded LLM model.

        Returns:
            Dictionary with model information
        """
        if self.llm is None:
            return {"error": "LLM not initialized"}

        try:
            return {
                "model_type": self.model_type,
                "model_name": self.model_name,
                "provider": self.model_type,
                "temperature": getattr(self.llm, "temperature", "unknown"),
            }
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {"error": str(e)}

    def test_connection(self) -> bool:
        """Test LLM connection with a simple query.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            test_response = self.llm.invoke("Hello")
            return test_response is not None and hasattr(test_response, "content")
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}")
            return False
