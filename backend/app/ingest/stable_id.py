import hashlib
from typing import Optional


def generate_source_id(filename: str, content_bytes: bytes, workspace_id: str = "default") -> str:
    """
    Generate a stable, reproducible ID for a source file.
    Based on workspace_id + filename + content hash to ensure re-uploading 
    the same file produces the same ID within a workspace.
    
    Sprint 8: Now includes workspace_id to allow same file in different workspaces.
    """
    hasher = hashlib.sha256()
    hasher.update(workspace_id.encode('utf-8'))
    hasher.update(filename.encode('utf-8'))
    hasher.update(content_bytes)
    return f"src_{hasher.hexdigest()[:16]}"


def generate_segment_id(
    source_id: str,
    index: int,
    text: str,
    speaker: Optional[str] = None,
    timestamp: Optional[str] = None,
    workspace_id: str = "default"
) -> str:
    """
    Generate a stable, reproducible ID for a segment.
    Based on workspace_id + source_id + index + text content to ensure 
    stability across re-uploads within a workspace.
    
    Sprint 8: Now includes workspace_id for multi-tenancy.
    """
    hasher = hashlib.sha256()
    hasher.update(workspace_id.encode('utf-8'))
    hasher.update(source_id.encode('utf-8'))
    hasher.update(str(index).encode('utf-8'))
    hasher.update(text.encode('utf-8'))
    if speaker:
        hasher.update(speaker.encode('utf-8'))
    if timestamp:
        hasher.update(timestamp.encode('utf-8'))
    return f"seg_{hasher.hexdigest()[:16]}"
