from typing import Tuple, List
from pathlib import Path
from sqlalchemy.orm import Session
from app.models import Source, Segment, SourceType, SourceStatus
from app.ingest.stable_id import generate_source_id, generate_segment_id
from app.ingest.parsers import (
    parse_txt, parse_md, parse_docx, parse_vtt, parse_transcript, SegmentData
)
from app.ingest.exceptions import UnparseableFileError, NotMachineReadableError


def ingest_file(
    filename: str,
    file_bytes: bytes,
    db: Session,
    workspace_id: str = "default"  # Sprint 8: Multi-tenancy
) -> Tuple[Source, List[Segment]]:
    """
    Ingest a file: parse, segment, generate stable IDs, persist to database.
    
    Sprint 8: Now accepts workspace_id to scope data to a workspace.
    
    Args:
        filename: Name of the uploaded file
        file_bytes: Raw file content
        db: Database session
        workspace_id: Workspace identifier (default: "default")
    
    Returns:
        Tuple of (Source, List[Segment])
    
    Raises:
        UnparseableFileError: File cannot be parsed
        NotMachineReadableError: File has no extractable text
    """
    # Determine file type
    ext = Path(filename).suffix.lower()
    
    if ext == '.txt':
        source_type = SourceType.TXT
        content = file_bytes.decode('utf-8')
        segment_data = parse_txt(content, filename)
    elif ext == '.md':
        source_type = SourceType.MD
        content = file_bytes.decode('utf-8')
        segment_data = parse_md(content, filename)
    elif ext == '.docx':
        source_type = SourceType.DOCX
        segment_data = parse_docx(file_bytes, filename)
    elif ext == '.vtt':
        source_type = SourceType.VTT
        content = file_bytes.decode('utf-8')
        segment_data = parse_vtt(content, filename)
    else:
        # Try to parse as transcript (speaker-labeled text)
        try:
            content = file_bytes.decode('utf-8')
            segment_data = parse_transcript(content, filename)
            source_type = SourceType.TRANSCRIPT
        except (UnicodeDecodeError, NotMachineReadableError):
            raise UnparseableFileError(filename, f"Unsupported file type '{ext}' and not a valid transcript")
    
    # Generate stable source ID
    source_id = generate_source_id(filename, file_bytes, workspace_id)
    
    # Check if source already exists (re-upload case)
    # Sprint 8: Also check workspace_id to prevent cross-workspace collisions
    existing_source = db.query(Source).filter(
        Source.id == source_id,
        Source.workspace_id == workspace_id
    ).first()
    if existing_source:
        # Return existing source and segments (stable IDs guarantee)
        existing_segments = db.query(Segment).filter(
            Segment.source_id == source_id,
            Segment.workspace_id == workspace_id
        ).order_by(Segment.index).all()
        return existing_source, existing_segments
    
    # Create new source
    source = Source(
        id=source_id,
        workspace_id=workspace_id,  # Sprint 8
        filename=filename,
        type=source_type,
        status=SourceStatus.PROCESSED
    )
    db.add(source)
    
    # Create segments with stable IDs
    segments = []
    for seg_data in segment_data:
        segment_id = generate_segment_id(
            source_id=source_id,
            index=seg_data.index,
            text=seg_data.text,
            speaker=seg_data.speaker,
            timestamp=seg_data.timestamp,
            workspace_id=workspace_id
        )
        
        segment = Segment(
            id=segment_id,
            workspace_id=workspace_id,  # Sprint 8
            source_id=source_id,
            index=seg_data.index,
            text=seg_data.text,
            speaker=seg_data.speaker,
            timestamp=seg_data.timestamp
        )
        db.add(segment)
        segments.append(segment)
    
    db.commit()
    db.refresh(source)
    
    return source, segments


def handle_ingest_error(
    filename: str,
    error: Exception,
    file_bytes: bytes,
    db: Session,
    workspace_id: str = "default"  # Sprint 8: Multi-tenancy
) -> Source:
    """
    Handle ingest errors by creating a Source record with error status.
    This ensures failed uploads are tracked, not silently dropped.
    
    Sprint 8: Now scoped to workspace.
    """
    source_id = generate_source_id(filename, file_bytes, workspace_id)
    
    if isinstance(error, NotMachineReadableError):
        status = SourceStatus.NOT_MACHINE_READABLE
        error_message = str(error)
    else:
        status = SourceStatus.REJECTED
        error_message = str(error)
    
    source = Source(
        id=source_id,
        workspace_id=workspace_id,  # Sprint 8
        filename=filename,
        type=SourceType.TXT,  # Default, doesn't matter for failed uploads
        status=status,
        error_message=error_message
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    
    return source
