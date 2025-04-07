"""Document chunking module for splitting text into manageable pieces."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import re

@dataclass
class ChunkConfig:
    """Configuration for text chunking."""
    chunk_size: int = 512  # Maximum number of characters per chunk
    chunk_overlap: int = 50  # Number of characters to overlap between chunks
    min_chunk_size: int = 20  # Minimum chunk size to avoid tiny chunks
    split_on_newline: bool = True  # Whether to try to split on newlines
    respect_sentences: bool = True  # Whether to try to keep sentences together
    
    def __post_init__(self):
        """Validate configuration."""
        if self.chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        if self.chunk_overlap < 0:
            raise ValueError("Chunk overlap must be non-negative")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")
        if self.min_chunk_size <= 0:
            raise ValueError("Minimum chunk size must be positive")
        if self.min_chunk_size > self.chunk_size:
            raise ValueError("Minimum chunk size must not exceed chunk size")

@dataclass
class TextChunk:
    """A chunk of text with metadata."""
    text: str
    metadata: Dict[str, Any]
    start_char: int
    end_char: int
    chunk_index: int

class ChunkingStrategy(ABC):
    """Abstract base class for text chunking strategies."""
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        """Initialize the chunking strategy.
        
        Args:
            config (Optional[ChunkConfig]): Chunking configuration
        """
        self.config = config or ChunkConfig()
    
    @abstractmethod
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """Split text into chunks.
        
        Args:
            text (str): Text to split into chunks
            metadata (Optional[Dict[str, Any]]): Optional metadata to attach to chunks
        
        Returns:
            List[TextChunk]: List of text chunks with metadata
        """
        pass

class SimpleChunker(ChunkingStrategy):
    """Simple chunking strategy that tries to respect sentence boundaries."""
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """Split text into chunks, trying to respect sentence boundaries.
        
        Args:
            text (str): Text to split into chunks
            metadata (Optional[Dict[str, Any]]): Optional metadata to attach to chunks
        
        Returns:
            List[TextChunk]: List of text chunks with metadata
        """
        if not text:
            return []
            
        metadata = metadata or {}
        chunks = []
        current_pos = 0
        chunk_index = 0
        
        while current_pos < len(text):
            # Calculate the end position for this chunk
            chunk_end = min(current_pos + self.config.chunk_size, len(text))
            
            # If we're splitting on newlines, try to find a good newline to split on
            if self.config.split_on_newline and chunk_end < len(text):
                newline_pos = self._find_newline_boundary(text, current_pos, chunk_end)
                if newline_pos > current_pos + self.config.min_chunk_size:
                    chunk_end = newline_pos
            
            # If we're not at the end of the text and we want to respect sentences
            if chunk_end < len(text) and self.config.respect_sentences:
                # Look for sentence boundaries
                sentence_end = self._find_sentence_boundary(text, current_pos, chunk_end)
                if sentence_end > current_pos + self.config.min_chunk_size:
                    chunk_end = sentence_end
            
            # Create the chunk
            chunk_text = text[current_pos:chunk_end].strip()
            if chunk_text:  # Only add non-empty chunks
                # Split on newlines if enabled and this isn't the last chunk
                if self.config.split_on_newline and chunk_end < len(text):
                    lines = chunk_text.split('\n')
                    # Add all but the last line as separate chunks
                    for line in lines[:-1]:
                        line = line.strip()
                        if line:
                            start_char = text.find(line, current_pos)
                            chunks.append(TextChunk(
                                text=line,
                                metadata=metadata.copy(),
                                start_char=start_char,
                                end_char=start_char + len(line),
                                chunk_index=chunk_index
                            ))
                            chunk_index += 1
                    # Keep the last line for the next iteration
                    chunk_text = lines[-1].strip()
                
                if chunk_text:  # Add remaining text as a chunk
                    start_char = text.find(chunk_text, current_pos)
                    chunks.append(TextChunk(
                        text=chunk_text,
                        metadata=metadata.copy(),
                        start_char=start_char,
                        end_char=start_char + len(chunk_text),
                        chunk_index=chunk_index
                    ))
                    chunk_index += 1
            
            # Move to next chunk position, accounting for overlap
            current_pos = chunk_end - self.config.chunk_overlap
            if current_pos <= current_pos:  # Ensure we make progress
                current_pos = chunk_end
        
        return chunks
    
    def _find_sentence_boundary(self, text: str, start_pos: int, end_pos: int) -> int:
        """Find the nearest sentence boundary between start and end positions.
        
        Args:
            text (str): Text to search in
            start_pos (int): Start position
            end_pos (int): End position
        
        Returns:
            int: Position of the nearest sentence boundary
        """
        # Look for sentence endings within the range
        search_text = text[start_pos:end_pos]
        
        # Find all sentence boundaries in the range
        boundaries = []
        for match in re.finditer(r'[.!?][\s"\')\]}]*', search_text):
            pos = start_pos + match.end()
            # Only consider boundaries that leave enough text for the next chunk
            if pos > start_pos + self.config.min_chunk_size:
                boundaries.append(pos)
        
        if not boundaries:
            return end_pos
            
        # Find the last boundary before the end position
        for pos in reversed(boundaries):
            if pos <= end_pos:
                return pos
                
        return end_pos
    
    def _find_newline_boundary(self, text: str, start_pos: int, end_pos: int) -> int:
        """Find the nearest newline boundary between start and end positions.
        
        Args:
            text (str): Text to search in
            start_pos (int): Start position
            end_pos (int): End position
        
        Returns:
            int: Position of the nearest newline boundary
        """
        # Look for newlines within the range
        search_text = text[start_pos:end_pos]
        
        # Find all newlines in the range
        boundaries = []
        for match in re.finditer(r'\n', search_text):
            pos = start_pos + match.start()
            # Only consider boundaries that leave enough text for the next chunk
            if pos > start_pos + self.config.min_chunk_size:
                boundaries.append(pos)
        
        if not boundaries:
            return end_pos
            
        # Find the first boundary after the minimum chunk size
        for pos in boundaries:
            if pos > start_pos + self.config.min_chunk_size:
                return pos
                
        return end_pos

class RecursiveChunker(ChunkingStrategy):
    """Recursive chunking strategy that splits text into increasingly smaller pieces."""
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """Split text into chunks recursively.
        
        This strategy first splits on major boundaries (e.g. multiple newlines),
        then on minor boundaries (e.g. single newlines), and finally on sentences
        if chunks are still too large.
        
        Args:
            text (str): Text to split into chunks
            metadata (Optional[Dict[str, Any]]): Optional metadata to attach to chunks
        
        Returns:
            List[TextChunk]: List of text chunks with metadata
        """
        if not text:
            return []
            
        metadata = metadata or {}
        chunks = []
        chunk_index = 0
        
        # First split on major boundaries (multiple newlines)
        major_sections = re.split(r'\n\s*\n', text)
        
        for section in major_sections:
            section = section.strip()
            if not section:
                continue
                
            # If section is small enough, add it as a chunk
            if len(section) <= self.config.chunk_size:
                chunks.append(TextChunk(
                    text=section,
                    metadata=metadata.copy(),
                    start_char=text.find(section),
                    end_char=text.find(section) + len(section),
                    chunk_index=chunk_index
                ))
                chunk_index += 1
                continue
            
            # Split larger sections on single newlines
            subsections = section.split('\n')
            current_chunk = []
            current_length = 0
            
            for subsection in subsections:
                subsection = subsection.strip()
                if not subsection:
                    continue
                
                # If adding this subsection would exceed chunk size
                if current_length + len(subsection) > self.config.chunk_size and current_chunk:
                    # Save current chunk
                    chunk_text = '\n'.join(current_chunk)
                    start_char = text.find(chunk_text)
                    chunks.append(TextChunk(
                        text=chunk_text,
                        metadata=metadata.copy(),
                        start_char=start_char,
                        end_char=start_char + len(chunk_text),
                        chunk_index=chunk_index
                    ))
                    chunk_index += 1
                    current_chunk = []
                    current_length = 0
                
                # If subsection itself is too large, split on sentences
                if len(subsection) > self.config.chunk_size:
                    sentences = re.split(r'(?<=[.!?])\s+', subsection)
                    for sentence in sentences:
                        if len(sentence) > self.config.chunk_size:
                            # If sentence is too large, split arbitrarily
                            for i in range(0, len(sentence), self.config.chunk_size):
                                chunk_text = sentence[i:i + self.config.chunk_size]
                                start_char = text.find(chunk_text)
                                chunks.append(TextChunk(
                                    text=chunk_text,
                                    metadata=metadata.copy(),
                                    start_char=start_char,
                                    end_char=start_char + len(chunk_text),
                                    chunk_index=chunk_index
                                ))
                                chunk_index += 1
                        else:
                            current_chunk.append(sentence)
                            current_length += len(sentence)
                            
                            if current_length > self.config.chunk_size:
                                chunk_text = '\n'.join(current_chunk)
                                start_char = text.find(chunk_text)
                                chunks.append(TextChunk(
                                    text=chunk_text,
                                    metadata=metadata.copy(),
                                    start_char=start_char,
                                    end_char=start_char + len(chunk_text),
                                    chunk_index=chunk_index
                                ))
                                chunk_index += 1
                                current_chunk = []
                                current_length = 0
                else:
                    current_chunk.append(subsection)
                    current_length += len(subsection)
            
            # Add any remaining text as a final chunk
            if current_chunk:
                chunk_text = '\n'.join(current_chunk)
                start_char = text.find(chunk_text)
                chunks.append(TextChunk(
                    text=chunk_text,
                    metadata=metadata.copy(),
                    start_char=start_char,
                    end_char=start_char + len(chunk_text),
                    chunk_index=chunk_index
                ))
                chunk_index += 1
        
        return chunks 