"""Context augmentation system for LLM queries."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from services.rag.retrieval import RetrievedChunk

class ContextConfig(BaseModel):
    """Configuration for context augmentation."""
    
    max_context_length: int = Field(
        default=4000,
        description="Maximum number of tokens in the context"
    )
    context_template: str = Field(
        default="Context:\n{context}\n\nQuestion: {question}\n\nAnswer based on the context above:",
        description="Template for formatting context and question"
    )
    chunk_separator: str = Field(
        default="\n---\n",
        description="Separator between context chunks"
    )
    include_metadata: bool = Field(
        default=True,
        description="Whether to include chunk metadata in context"
    )
    metadata_template: str = Field(
        default="Source: {source}, Relevance: {similarity:.2f}",
        description="Template for formatting chunk metadata"
    )

class ContextAugmenter:
    """Handles context augmentation for LLM queries."""
    
    def __init__(self, config: Optional[ContextConfig] = None):
        """Initialize the context augmenter.
        
        Args:
            config (Optional[ContextConfig]): Configuration for context augmentation.
                If None, uses default configuration.
        """
        self.config = config or ContextConfig()
    
    def format_chunk_metadata(self, chunk: RetrievedChunk) -> str:
        """Format metadata for a chunk.
        
        Args:
            chunk (RetrievedChunk): The retrieved chunk with metadata
            
        Returns:
            str: Formatted metadata string
        """
        if not self.config.include_metadata:
            return ""
            
        metadata = {
            "source": chunk.chunk.metadata.get("source", "Unknown"),
            "similarity": chunk.similarity
        }
        return self.config.metadata_template.format(**metadata)
    
    def format_chunk(self, chunk: RetrievedChunk) -> str:
        """Format a single chunk with its metadata.
        
        Args:
            chunk (RetrievedChunk): The retrieved chunk to format
            
        Returns:
            str: Formatted chunk text with metadata
        """
        text = chunk.chunk.text.strip()
        metadata = self.format_chunk_metadata(chunk)
        
        if metadata:
            return f"{text}\n{metadata}"
        return text
    
    def augment_prompt(self, question: str, chunks: List[RetrievedChunk]) -> str:
        """Augment a question with retrieved context chunks.
        
        Args:
            question (str): The original question
            chunks (List[RetrievedChunk]): Retrieved context chunks
            
        Returns:
            str: Augmented prompt with context
        """
        # Format all chunks with metadata
        formatted_chunks = [self.format_chunk(chunk) for chunk in chunks]
        
        # Join chunks with separator
        context = self.config.chunk_separator.join(formatted_chunks)
        
        # Format final prompt using template
        return self.config.context_template.format(
            context=context,
            question=question
        )
    
    def create_system_prompt(self, task_type: str) -> str:
        """Create a system prompt for a specific task type.
        
        Args:
            task_type (str): Type of task (e.g., 'compliance_check', 'risk_assessment')
            
        Returns:
            str: System prompt for the task
        """
        prompts = {
            'compliance_check': """You are a regulatory compliance assistant. Your task is to:
1. Analyze the provided context from regulatory documents
2. Determine if the given scenario complies with regulations
3. Provide clear explanations with specific references to regulations
4. Highlight any potential compliance issues
5. Suggest corrective actions if needed""",
            
            'risk_assessment': """You are a risk assessment specialist. Your task is to:
1. Analyze the provided context from regulatory documents
2. Identify potential risks in the given scenario
3. Assess the severity and likelihood of each risk
4. Provide specific references to relevant regulations
5. Suggest risk mitigation strategies""",
            
            'general': """You are a regulatory expert assistant. Your task is to:
1. Analyze the provided regulatory context carefully
2. Answer questions based solely on the provided information
3. Cite specific references when making statements
4. Acknowledge if information is not found in the context
5. Maintain objectivity in your analysis"""
        }
        
        return prompts.get(task_type, prompts['general']) 