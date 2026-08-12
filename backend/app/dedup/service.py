import hashlib
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models import Requirement, Evidence, MergeSuggestion, GroundingStatus
from app.extraction.llm_client import LLMClient
import json


def generate_merge_suggestion_id(req_id_1: str, req_id_2: str) -> str:
    """Generate stable ID for merge suggestion"""
    hasher = hashlib.sha256()
    # Sort IDs to ensure same pair = same ID regardless of order
    ids = sorted([req_id_1, req_id_2])
    hasher.update(ids[0].encode('utf-8'))
    hasher.update(ids[1].encode('utf-8'))
    return f"mrg_{hasher.hexdigest()[:16]}"


async def detect_duplicates(
    source_id: str,
    db: Session,
    workspace_id: str
) -> List[MergeSuggestion]:
    """
    Detect near-duplicate requirements within a source.
    
    Returns list of MergeSuggestion objects (not auto-applied).
    Human must confirm merges in Sprint 4 UI.
    Sprint 8: Now scoped to workspace.
    """
    # Get all grounded requirements for this source
    # Only check grounded requirements - don't dedupe quarantined ones
    requirements = db.query(Requirement).join(Evidence).filter(
        Evidence.source_id == source_id,
        Evidence.workspace_id == workspace_id,
        Requirement.workspace_id == workspace_id,
        Requirement.grounding == GroundingStatus.GROUNDED,
        Requirement.is_merged == 0
    ).distinct().all()
    
    if len(requirements) < 2:
        return []
    
    # Prepare data for LLM
    req_data = [
        {
            "id": req.id,
            "statement": req.statement,
            "category": req.category,
            "type": req.type.value
        }
        for req in requirements
    ]
    
    # Call LLM to detect duplicates
    llm_client = LLMClient()
    duplicate_pairs = await llm_client.detect_duplicates(req_data)
    
    # Create merge suggestions (not auto-applied)
    suggestions = []
    for pair in duplicate_pairs:
        req_id_1 = pair["requirement_id_1"]
        req_id_2 = pair["requirement_id_2"]
        similarity = pair["similarity_score"]
        reasoning = pair["reasoning"]
        
        # Check if suggestion already exists
        suggestion_id = generate_merge_suggestion_id(req_id_1, req_id_2)
        existing = db.query(MergeSuggestion).filter(
            MergeSuggestion.id == suggestion_id
        ).first()
        
        if not existing:
            suggestion = MergeSuggestion(
                id=suggestion_id,
                workspace_id=workspace_id,
                requirement_id_1=req_id_1,
                requirement_id_2=req_id_2,
                similarity_score=similarity,
                reasoning=reasoning,
                status="pending"
            )
            db.add(suggestion)
            suggestions.append(suggestion)
    
    db.commit()
    
    return suggestions


def merge_requirements(
    merge_suggestion_id: str,
    db: Session,
    workspace_id: str
) -> Requirement:
    """
    Execute a merge: combine two requirements, preserving ALL evidence.
    
    Algorithm:
    1. Get both requirements
    2. Create new merged statement (or keep one)
    3. Transfer ALL evidence from both to merged requirement
    4. Mark originals as merged (is_merged=1)
    5. Update suggestion status to "accepted"
    
    Sprint 8: Now scoped to workspace.
    Returns the merged requirement.
    """
    suggestion = db.query(MergeSuggestion).filter(
        MergeSuggestion.id == merge_suggestion_id,
        MergeSuggestion.workspace_id == workspace_id
    ).first()
    
    if not suggestion:
        raise ValueError(f"Merge suggestion {merge_suggestion_id} not found")
    
    if suggestion.status != "pending":
        raise ValueError(f"Merge suggestion already {suggestion.status}")
    
    req1 = db.query(Requirement).filter(Requirement.id == suggestion.requirement_id_1).first()
    req2 = db.query(Requirement).filter(Requirement.id == suggestion.requirement_id_2).first()
    
    if not req1 or not req2:
        raise ValueError("One or both requirements not found")
    
    # Keep req1, mark req2 as merged into req1
    req2.is_merged = 1
    req2.merged_into = req1.id
    
    # Transfer all evidence from req2 to req1
    evidence_from_req2 = db.query(Evidence).filter(Evidence.requirement_id == req2.id).all()
    for evd in evidence_from_req2:
        evd.requirement_id = req1.id
    
    # Update suggestion status
    suggestion.status = "accepted"
    
    db.commit()
    db.refresh(req1)
    
    return req1


def unmerge_requirements(
    requirement_id: str,
    db: Session,
    workspace_id: str
) -> List[Requirement]:
    """
    Undo a merge: restore original requirements.
    
    Sprint 8: Now scoped to workspace.
    Returns list of unmerged requirements.
    """
    # Find all requirements that were merged into this one
    merged_reqs = db.query(Requirement).filter(
        Requirement.merged_into == requirement_id,
        Requirement.workspace_id == workspace_id
    ).all()
    
    for req in merged_reqs:
        req.is_merged = 0
        req.merged_into = None
    
    # Find the merge suggestion and mark as rejected
    suggestions = db.query(MergeSuggestion).filter(
        (MergeSuggestion.requirement_id_1 == requirement_id) |
        (MergeSuggestion.requirement_id_2 == requirement_id),
        MergeSuggestion.status == "accepted"
    ).all()
    
    for suggestion in suggestions:
        suggestion.status = "rejected"
    
    db.commit()
    
    return merged_reqs
