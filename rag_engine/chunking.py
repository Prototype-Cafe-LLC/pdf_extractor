"""Document chunking strategies for technical documentation.

This module provides specialized chunking strategies for technical documents,
particularly AT command manuals and IoT device documentation.
"""

import re
import tiktoken
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocumentChunk:
    """Represents a chunk of document with metadata."""
    content: str
    metadata: Dict[str, Any]
    chunk_id: str
    start_char: int
    end_char: int


class DocumentChunker:
    """Chunks technical documents while preserving context and structure."""
    
    def __init__(self, max_tokens: int = 512, overlap_tokens: int = 50):
        """Initialize the document chunker.
        
        Args:
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Number of overlapping tokens between chunks
        """
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Patterns for technical documentation
        self.at_command_pattern = r'AT\+[A-Z0-9]+'
        self.section_pattern = r'^#{1,6}\s+(.+)$'
        self.page_pattern = r'(\d+)\s*/\s*(\d+)'
        
    def chunk_by_sections(self, markdown_content: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Chunk document by sections while preserving AT command context.
        
        Args:
            markdown_content: The markdown content to chunk
            metadata: Document metadata
            
        Returns:
            List of document chunks with metadata
        """
        chunks = []
        lines = markdown_content.split('\n')
        current_chunk = []
        current_metadata = metadata.copy()
        chunk_id = 0
        
        for i, line in enumerate(lines):
            # Check if this line starts a new section
            section_match = re.match(self.section_pattern, line)
            
            if section_match and current_chunk:
                # Save current chunk if it exists
                chunk_content = '\n'.join(current_chunk)
                if chunk_content.strip():
                    chunk = self._create_chunk(
                        chunk_content, current_metadata, chunk_id, i - len(current_chunk), i
                    )
                    chunks.append(chunk)
                    chunk_id += 1
                
                # Start new chunk with section header
                current_chunk = [line]
                current_metadata = metadata.copy()
                current_metadata['section'] = section_match.group(1)
            else:
                current_chunk.append(line)
                
                # Check if current chunk exceeds token limit
                chunk_text = '\n'.join(current_chunk)
                tokens = len(self.tokenizer.encode(chunk_text))
                
                if tokens > self.max_tokens:
                    # Split chunk at sentence boundary
                    split_chunk = self._split_chunk_at_boundary(current_chunk)
                    if split_chunk:
                        chunk_content = '\n'.join(split_chunk)
                        chunk = self._create_chunk(
                            chunk_content, current_metadata, chunk_id, i - len(split_chunk), i
                        )
                        chunks.append(chunk)
                        chunk_id += 1
                        
                        # Keep remaining content for next chunk
                        current_chunk = current_chunk[len(split_chunk):]
        
        # Add final chunk
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            if chunk_content.strip():
                chunk = self._create_chunk(
                    chunk_content, current_metadata, chunk_id, len(lines) - len(current_chunk), len(lines)
                )
                chunks.append(chunk)
        
        return chunks
    
    def chunk_by_tokens(self, markdown_content: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Chunk document by token count with overlap.
        
        Args:
            markdown_content: The markdown content to chunk
            metadata: Document metadata
            
        Returns:
            List of document chunks with metadata
        """
        chunks = []
        tokens = self.tokenizer.encode(markdown_content)
        chunk_id = 0
        
        for i in range(0, len(tokens), self.max_tokens - self.overlap_tokens):
            chunk_tokens = tokens[i:i + self.max_tokens]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            # Find character boundaries
            start_char = len(self.tokenizer.decode(tokens[:i]))
            end_char = len(self.tokenizer.decode(tokens[:i + len(chunk_tokens)]))
            
            chunk = self._create_chunk(
                chunk_text, metadata, chunk_id, start_char, end_char
            )
            chunks.append(chunk)
            chunk_id += 1
        
        return chunks
    
    def chunk_by_at_commands(self, markdown_content: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Chunk document by AT command sections.
        
        Args:
            markdown_content: The markdown content to chunk
            metadata: Document metadata
            
        Returns:
            List of document chunks with metadata
        """
        chunks = []
        lines = markdown_content.split('\n')
        current_chunk = []
        current_metadata = metadata.copy()
        chunk_id = 0
        
        for i, line in enumerate(lines):
            # Check for AT command patterns
            at_matches = re.findall(self.at_command_pattern, line)
            
            if at_matches and current_chunk:
                # Save current chunk if it contains AT commands
                chunk_content = '\n'.join(current_chunk)
                if re.search(self.at_command_pattern, chunk_content):
                    chunk = self._create_chunk(
                        chunk_content, current_metadata, chunk_id, i - len(current_chunk), i
                    )
                    chunks.append(chunk)
                    chunk_id += 1
                
                # Start new chunk
                current_chunk = [line]
                current_metadata = metadata.copy()
                # Convert list to comma-separated string for ChromaDB compatibility
                current_metadata['at_commands'] = ', '.join(at_matches) if at_matches else ''
            else:
                current_chunk.append(line)
                
                # Check token limit
                chunk_text = '\n'.join(current_chunk)
                tokens = len(self.tokenizer.encode(chunk_text))
                
                if tokens > self.max_tokens:
                    # Split at sentence boundary
                    split_chunk = self._split_chunk_at_boundary(current_chunk)
                    if split_chunk:
                        chunk_content = '\n'.join(split_chunk)
                        chunk = self._create_chunk(
                            chunk_content, current_metadata, chunk_id, i - len(split_chunk), i
                        )
                        chunks.append(chunk)
                        chunk_id += 1
                        current_chunk = current_chunk[len(split_chunk):]
        
        # Add final chunk
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            if chunk_content.strip():
                chunk = self._create_chunk(
                    chunk_content, current_metadata, chunk_id, len(lines) - len(current_chunk), len(lines)
                )
                chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(self, content: str, metadata: Dict[str, Any], 
                     chunk_id: int, start_char: int, end_char: int) -> DocumentChunk:
        """Create a document chunk with metadata.
        
        Args:
            content: Chunk content
            metadata: Document metadata
            chunk_id: Unique chunk identifier
            start_char: Starting character position
            end_char: Ending character position
            
        Returns:
            DocumentChunk instance
        """
        chunk_metadata = metadata.copy()
        # Find AT commands in content
        at_commands_found = re.findall(self.at_command_pattern, content)
        
        # Create the full chunk ID with document name
        full_chunk_id = f"{metadata.get('document', 'unknown')}_{chunk_id}"
        
        chunk_metadata.update({
            'chunk_id': full_chunk_id,  # Store the FULL chunk ID with document name
            'chunk_index': chunk_id,     # Store the numeric index separately
            'start_char': start_char,
            'end_char': end_char,
            'token_count': len(self.tokenizer.encode(content)),
            # Convert list to comma-separated string for ChromaDB compatibility
            'at_commands': ', '.join(at_commands_found) if at_commands_found else '',
            'at_command_count': len(at_commands_found),
            'has_code_blocks': '```' in content,
            'has_tables': '|' in content and '\n' in content,
        })
        
        return DocumentChunk(
            content=content,
            metadata=chunk_metadata,
            chunk_id=full_chunk_id,
            start_char=start_char,
            end_char=end_char
        )
    
    def _split_chunk_at_boundary(self, lines: List[str]) -> Optional[List[str]]:
        """Split chunk at sentence or paragraph boundary.
        
        Args:
            lines: Lines to split
            
        Returns:
            First part of the split, or None if no good split point
        """
        # Look for sentence boundaries (period followed by space or newline)
        for i in range(len(lines) - 1, 0, -1):
            line = lines[i]
            if re.search(r'[.!?]\s*$', line):
                return lines[:i + 1]
        
        # Look for paragraph boundaries (empty lines)
        for i in range(len(lines) - 1, 0, -1):
            if not lines[i].strip():
                return lines[:i]
        
        # If no good boundary, return half
        mid_point = len(lines) // 2
        return lines[:mid_point] if mid_point > 0 else None 