import hashlib
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models import (
    Source, Segment, Requirement, Evidence,
    RequirementType, GroundingStatus, ConfidenceLevel
)
from app.extraction.llm_client import LLMClient
from app.extraction.grounding import GroundingVerifier
from app.extraction.schemas import ExtractionOutputSchema
from app.feedback.service import get_workspace_examples
from app.extraction.cache import get_extraction_cache  # Sprint 11


def generate_requirement_id(statement: str, workspace_id: str = "default") -> str:
    """
    Generate stable ID for a requirement.
    
    Sprint 8: Now includes workspace_id to allow same statement 
    in different workspaces.
    """
    hasher = hashlib.sha256()
    hasher.update(workspace_id.encode('utf-8'))
    hasher.update(statement.encode('utf-8'))
    return f"req_{hasher.hexdigest()[:16]}"


def generate_evidence_id(requirement_id: str, segment_id: str, quote: str, workspace_id: str = "default") -> str:
    """
    Generate stable ID for an evidence entry.
    
    Sprint 8: Now includes workspace_id for multi-tenancy.
    """
    hasher = hashlib.sha256()
    hasher.update(workspace_id.encode('utf-8'))
    hasher.update(requirement_id.encode('utf-8'))
    hasher.update(segment_id.encode('utf-8'))
    hasher.update(quote.encode('utf-8'))
    return f"evd_{hasher.hexdigest()[:16]}"


async def extract_and_ground_requirements(
    source_id: str,
    db: Session,
    workspace_id: str
) -> Tuple[List[Requirement], dict]:
    """
    Extract requirements from a source and verify grounding.
    
    This is the main pipeline:
    1. Get segments for source
    2. Call LLM to extract requirements with citations (STAGE A)
    3. Verify each citation with deterministic code (STAGE B)
    4. Mark requirements as grounded or quarantined
    5. Persist to database
    
    Sprint 8: Now scoped to workspace.
    
    Returns:
        (list of Requirements, stats dict)
    """
    # Get source and segments
    source = db.query(Source).filter(Source.id == source_id, Source.workspace_id == workspace_id).first()
    if not source:
        raise ValueError(f"Source {source_id} not found in workspace {workspace_id}")
    
    segments = db.query(Segment).filter(
        Segment.source_id == source_id
    ).order_by(Segment.index).all()
    
    if not segments:
        raise ValueError(f"No segments found for source {source_id}")
    
    # Prepare segments for LLM
    segment_data = [
        {
            "id": seg.id,
            "source_id": seg.source_id,
            "index": seg.index,
            "speaker": seg.speaker,
            "timestamp": seg.timestamp,
            "text": seg.text
        }
        for seg in segments
    ]
    
    # STAGE A: LLM Extraction (proposes requirements with citations)
    # Sprint 11: Check cache first
    cache = get_extraction_cache()
    cached_result = cache.get(segment_data)
    
    if cached_result:
        # Use cached extraction result
        extraction_output = ExtractionOutputSchema(**cached_result)
    else:
        # Call LLM
        llm_client = LLMClient()
        
        # Sprint 9: Get few-shot examples for this workspace
        few_shot_examples = get_workspace_examples(workspace_id, db, max_examples=3)
        
        extraction_output = await llm_client.extract_requirements(segment_data, few_shot_examples)
        
        # Sprint 11: Cache the result
        cache.set(segment_data, extraction_output.model_dump())
    
    # Stats tracking
    stats = {
        "total_proposed": len(extraction_output.requirements),
        "grounded": 0,
        "quarantined": 0,
        "ungrounded_candidates": len(extraction_output.ungrounded_candidates),
        "fabrication_attempts": 0
    }
    
    requirements_created = []
    
    # STAGE B: Grounding Verification (deterministic code checks each citation)
    for req_data in extraction_output.requirements:
        # Verify evidence
        all_verified, fabrication_count, evidence_results = GroundingVerifier.verify_requirement_evidence(
            req_data.model_dump(),
            db
        )
        
        # Determine grounding status based on verification
        if all_verified:
            grounding = GroundingStatus.GROUNDED
            stats["grounded"] += 1
        else:
            grounding = GroundingStatus.QUARANTINED
            stats["quarantined"] += 1
            stats["fabrication_attempts"] += fabrication_count
        
        # Create requirement
        req_id = generate_requirement_id(req_data.statement, workspace_id)
        
        requirement = Requirement(
            id=req_id,
            workspace_id=workspace_id,
            statement=req_data.statement,
            category=req_data.category,
            type=RequirementType(req_data.type),
            grounding=grounding,
            confidence=ConfidenceLevel(req_data.confidence),
            fabrication_attempts=fabrication_count
        )
        
        db.add(requirement)
        
        # Create evidence entries
        for evd_result in evidence_results:
            evd_id = generate_evidence_id(
                req_id,
                evd_result["segment_id"],
                evd_result["verbatim_quote"],
                workspace_id
            )
            
            evidence = Evidence(
                id=evd_id,
                workspace_id=workspace_id,
                requirement_id=req_id,
                source_id=evd_result["source_id"],
                segment_id=evd_result["segment_id"],
                verbatim_quote=evd_result["verbatim_quote"],
                verified=1 if evd_result["verified"] else -1,
                verification_method=evd_result["method"],
                source_mismatch=1 if evd_result["method"] == "source_mismatch" else 0
            )
            
            db.add(evidence)
        
        requirements_created.append(requirement)
    
    # Handle ungrounded candidates
    for candidate in extraction_output.ungrounded_candidates:
        req_id = generate_requirement_id(candidate.statement, workspace_id)
        
        requirement = Requirement(
            id=req_id,
            workspace_id=workspace_id,
            statement=candidate.statement,
            category="ungrounded",
            type=RequirementType.FUNCTIONAL,  # Default
            grounding=GroundingStatus.UNGROUNDED_CANDIDATE,
            confidence=ConfidenceLevel.LOW,
            ungrounded_reasoning=candidate.reasoning,
            fabrication_attempts=0
        )
        
        db.add(requirement)
        requirements_created.append(requirement)
    
    db.commit()
    
    return requirements_created, stats
