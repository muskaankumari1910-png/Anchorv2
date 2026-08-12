import hashlib
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Source, Segment, Evidence, SegmentConsumption, Gap, Requirement, GroundingStatus
from app.extraction.llm_client import LLMClient


def generate_consumption_id(segment_id: str, requirement_id: str) -> str:
    """Generate stable ID for consumption record"""
    hasher = hashlib.sha256()
    hasher.update(segment_id.encode('utf-8'))
    hasher.update(requirement_id.encode('utf-8'))
    return f"con_{hasher.hexdigest()[:16]}"


def generate_gap_id(segment_id: str) -> str:
    """Generate stable ID for gap record"""
    hasher = hashlib.sha256()
    hasher.update(segment_id.encode('utf-8'))
    return f"gap_{hasher.hexdigest()[:16]}"


async def analyze_coverage(
    source_id: str,
    db: Session,
    workspace_id: str,
    low_coverage_threshold: float = 0.4
) -> Dict:
    """
    Analyze coverage for a source:
    1. Mark segments as consumed (contributed to grounded requirements)
    2. Identify unconsumed segments
    3. Filter filler/greetings from unconsumed
    4. Calculate coverage percentage
    5. Flag draft as incomplete if coverage too low
    
    Sprint 8: Now scoped to workspace.
    Returns coverage stats and gaps.
    """
    # Get source and all segments
    source = db.query(Source).filter(
        Source.id == source_id,
        Source.workspace_id == workspace_id
    ).first()
    if not source:
        raise ValueError(f"Source {source_id} not found in workspace {workspace_id}")
    
    segments = db.query(Segment).filter(Segment.source_id == source_id).all()
    total_segments = len(segments)
    
    if total_segments == 0:
        return {
            "source_id": source_id,
            "total_segments": 0,
            "consumed_segments": 0,
            "coverage_percentage": 0.0,
            "is_incomplete": True,
            "gaps": []
        }
    
    # Find all grounded requirements for this source
    grounded_reqs = db.query(Requirement).join(Evidence).filter(
        Evidence.source_id == source_id,
        Evidence.workspace_id == workspace_id,
        Requirement.workspace_id == workspace_id,
        Requirement.grounding == GroundingStatus.GROUNDED,
        Requirement.is_merged == 0
    ).distinct().all()
    
    # Track consumed segments
    consumed_segment_ids = set()
    
    for req in grounded_reqs:
        evidence_list = db.query(Evidence).filter(
            Evidence.requirement_id == req.id,
            Evidence.verified == 1  # Only count verified evidence
        ).all()
        
        for evd in evidence_list:
            segment_id = evd.segment_id
            consumed_segment_ids.add(segment_id)
            
            # Create consumption record if not exists
            consumption_id = generate_consumption_id(segment_id, req.id)
            existing = db.query(SegmentConsumption).filter(
                SegmentConsumption.id == consumption_id
            ).first()
            
            if not existing:
                consumption = SegmentConsumption(
                    id=consumption_id,
                    workspace_id=workspace_id,
                    segment_id=segment_id,
                    requirement_id=req.id
                )
                db.add(consumption)
    
    # Find unconsumed segments
    unconsumed_segments = [seg for seg in segments if seg.id not in consumed_segment_ids]
    
    # Filter filler from unconsumed
    if unconsumed_segments:
        filler_classification = await classify_filler_segments(unconsumed_segments)
    else:
        filler_classification = {}
    
    # Create gap records for unconsumed segments
    gaps = []
    for seg in unconsumed_segments:
        is_filler = filler_classification.get(seg.id, False)
        
        gap_id = generate_gap_id(seg.id)
        existing_gap = db.query(Gap).filter(Gap.id == gap_id).first()
        
        if not existing_gap:
            gap = Gap(
                id=gap_id,
                workspace_id=workspace_id,
                segment_id=seg.id,
                source_id=source_id,
                is_filler=1 if is_filler else 0
            )
            db.add(gap)
            gaps.append({
                "segment_id": seg.id,
                "segment_index": seg.index,
                "segment_text": seg.text,
                "speaker": seg.speaker,
                "is_filler": is_filler
            })
        else:
            gaps.append({
                "segment_id": seg.id,
                "segment_index": seg.index,
                "segment_text": seg.text,
                "speaker": seg.speaker,
                "is_filler": bool(existing_gap.is_filler)
            })
    
    db.commit()
    
    # Calculate coverage
    consumed_count = len(consumed_segment_ids)
    coverage_percentage = (consumed_count / total_segments) * 100.0
    is_incomplete = coverage_percentage < (low_coverage_threshold * 100)
    
    # Filter to substantive gaps only
    substantive_gaps = [g for g in gaps if not g["is_filler"]]
    
    return {
        "source_id": source_id,
        "total_segments": total_segments,
        "consumed_segments": consumed_count,
        "unconsumed_segments": len(unconsumed_segments),
        "coverage_percentage": round(coverage_percentage, 2),
        "is_incomplete": is_incomplete,
        "low_coverage_threshold": low_coverage_threshold * 100,
        "gaps": substantive_gaps,  # Only substantive gaps
        "filler_count": len([g for g in gaps if g["is_filler"]])
    }


async def classify_filler_segments(segments: List[Segment]) -> Dict[str, bool]:
    """
    Use LLM to classify segments as filler/greeting vs substantive.
    
    Returns dict: {segment_id: is_filler}
    """
    llm_client = LLMClient()
    
    segment_data = [
        {
            "id": seg.id,
            "text": seg.text,
            "speaker": seg.speaker
        }
        for seg in segments
    ]
    
    classifications = await llm_client.classify_filler(segment_data)
    
    return classifications
