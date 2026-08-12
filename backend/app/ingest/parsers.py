import re
from typing import List, Dict, Optional
from pathlib import Path
import docx
import webvtt
from app.ingest.exceptions import UnparseableFileError, NotMachineReadableError


class SegmentData:
    """Data structure for a parsed segment before DB persistence"""
    def __init__(
        self,
        index: int,
        text: str,
        speaker: Optional[str] = None,
        timestamp: Optional[str] = None
    ):
        self.index = index
        self.text = text
        self.speaker = speaker
        self.timestamp = timestamp


def parse_txt(content: str, filename: str) -> List[SegmentData]:
    """
    Parse plain text file. Split at paragraph level (double newlines).
    Character-perfect preservation.
    """
    if not content.strip():
        raise NotMachineReadableError(filename)
    
    # Split on double newlines (paragraph breaks), preserve single newlines within paragraphs
    paragraphs = re.split(r'\n\s*\n', content)
    segments = []
    
    for idx, para in enumerate(paragraphs):
        text = para.strip()
        if text:  # Skip empty paragraphs
            segments.append(SegmentData(index=idx, text=text))
    
    if not segments:
        raise NotMachineReadableError(filename)
    
    return segments


def parse_md(content: str, filename: str) -> List[SegmentData]:
    """
    Parse Markdown file. Split at heading or paragraph level.
    Character-perfect preservation.
    """
    if not content.strip():
        raise NotMachineReadableError(filename)
    
    # Split on headings or double newlines
    # Keep heading with its content until next heading
    lines = content.split('\n')
    segments = []
    current_block = []
    idx = 0
    
    for line in lines:
        # Heading marker
        if line.strip().startswith('#'):
            if current_block:
                text = '\n'.join(current_block).strip()
                if text:
                    segments.append(SegmentData(index=idx, text=text))
                    idx += 1
                current_block = []
            current_block.append(line)
        elif line.strip() == '':
            if current_block:
                text = '\n'.join(current_block).strip()
                if text:
                    segments.append(SegmentData(index=idx, text=text))
                    idx += 1
                current_block = []
        else:
            current_block.append(line)
    
    # Final block
    if current_block:
        text = '\n'.join(current_block).strip()
        if text:
            segments.append(SegmentData(index=idx, text=text))
    
    if not segments:
        raise NotMachineReadableError(filename)
    
    return segments


def parse_docx(file_bytes: bytes, filename: str) -> List[SegmentData]:
    """
    Parse .docx file. Split at paragraph level.
    Character-perfect preservation of paragraph text.
    """
    try:
        from io import BytesIO
        doc = docx.Document(BytesIO(file_bytes))
    except Exception as e:
        raise UnparseableFileError(filename, f"DOCX parsing failed: {str(e)}")
    
    segments = []
    idx = 0
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:  # Skip empty paragraphs
            segments.append(SegmentData(index=idx, text=text))
            idx += 1
    
    if not segments:
        raise NotMachineReadableError(filename)
    
    return segments


def parse_vtt(content: str, filename: str) -> List[SegmentData]:
    """
    Parse WebVTT transcript file. Split at caption/utterance level.
    Preserve timestamp, infer speaker if present in text.
    """
    try:
        from io import StringIO
        vtt = webvtt.read_buffer(StringIO(content))
    except Exception as e:
        raise UnparseableFileError(filename, f"VTT parsing failed: {str(e)}")
    
    segments = []
    
    for idx, caption in enumerate(vtt):
        text = caption.text.strip()
        if not text:
            continue
        
        timestamp = caption.start  # Format: "00:00:01.000"
        
        # Try to extract speaker if format is "Speaker: text"
        speaker = None
        speaker_match = re.match(r'^([A-Z][^:]{0,30}):\s*(.+)$', text, re.DOTALL)
        if speaker_match:
            speaker = speaker_match.group(1)
            text = speaker_match.group(2).strip()
        
        segments.append(SegmentData(
            index=idx,
            text=text,
            speaker=speaker,
            timestamp=timestamp
        ))
    
    if not segments:
        raise NotMachineReadableError(filename)
    
    return segments


def parse_transcript(content: str, filename: str) -> List[SegmentData]:
    """
    Parse plain speaker-labeled transcript.
    Expected format: "Speaker: text" or "Speaker (timestamp): text"
    Split at utterance level (each speaker turn).
    """
    if not content.strip():
        raise NotMachineReadableError(filename)
    
    lines = content.split('\n')
    segments = []
    idx = 0
    
    # Pattern: "Speaker: text" or "Speaker (HH:MM:SS): text"
    speaker_pattern = re.compile(r'^([A-Z][^:(\n]{0,30})(?:\s*\(([^)]+)\))?\s*:\s*(.+)$', re.DOTALL)
    
    current_speaker = None
    current_timestamp = None
    current_text = []
    
    for line in lines:
        match = speaker_pattern.match(line)
        if match:
            # Save previous utterance
            if current_text:
                text = '\n'.join(current_text).strip()
                if text:
                    segments.append(SegmentData(
                        index=idx,
                        text=text,
                        speaker=current_speaker,
                        timestamp=current_timestamp
                    ))
                    idx += 1
            
            # Start new utterance
            current_speaker = match.group(1).strip()
            current_timestamp = match.group(2).strip() if match.group(2) else None
            current_text = [match.group(3).strip()]
        else:
            # Continuation of current utterance
            if line.strip():
                current_text.append(line.strip())
    
    # Save final utterance
    if current_text:
        text = '\n'.join(current_text).strip()
        if text:
            segments.append(SegmentData(
                index=idx,
                text=text,
                speaker=current_speaker,
                timestamp=current_timestamp
            ))
    
    if not segments:
        raise NotMachineReadableError(filename)
    
    return segments
