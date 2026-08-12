import hashlib
from typing import List
from sqlalchemy.orm import Session
from app.models import Requirement, Evidence, Contradiction, GroundingStatus
from app.extraction.llm_client import LLMClient


def generate_contradiction_id(req_id_1: str, req_id_2: str) -> str:
    """Generate stable ID for contradiction"""
    hasher = hashlib.sha256()
    ids = sorted([req_id_1, req_id_2])
    hasher.update(ids[0].encode('utf-8'))
    hasher.update(ids[1].encode('utf-8'))
    return f"ctr_{hasher.hexdigest()[:16]}"


async def detect_contradictions(
    source_id: str,
    db: Session,
    workspace_id: str
) -> List[Contradiction]:
    """
    Detect contradictions within the same category.
    
    Important: This only FLAGS contradictions, never auto-resolves.
    Human must decide in UI (Sprint 4).
    Sprint 8: Now scoped to workspace.
    Sprint 10: Added pre-filtering to reduce LLM calls at scale.
    """
    # Get all grounded requirements for this source, grouped by category
    requirements = db.query(Requirement).join(Evidence).filter(
        Evidence.source_id == source_id,
        Evidence.workspace_id == workspace_id,
        Requirement.workspace_id == workspace_id,
        Requirement.grounding == GroundingStatus.GROUNDED,
        Requirement.is_merged == 0
    ).distinct().all()
    
    if len(requirements) < 2:
        return []
    
    # Group by category
    by_category = {}
    for req in requirements:
        category = req.category or "uncategorized"
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(req)
    
    # Detect contradictions within each category
    contradictions = []
    llm_client = LLMClient()
    
    for category, reqs in by_category.items():
        if len(reqs) < 2:
            continue
        
        # Sprint 10: Pre-filter candidates using keyword overlap
        # This reduces quadratic LLM calls to linear cost
        candidate_pairs = _pre_filter_contradiction_candidates(reqs)
        
        if not candidate_pairs:
            continue
        
        # Get evidence for candidate pairs only
        reqs_with_evidence = []
        req_ids_in_candidates = set()
        for req_id_1, req_id_2 in candidate_pairs:
            req_ids_in_candidates.add(req_id_1)
            req_ids_in_candidates.add(req_id_2)
        
        for req in reqs:
            if req.id not in req_ids_in_candidates:
                continue
                
            evidence_list = db.query(Evidence).filter(
                Evidence.requirement_id == req.id,
                Evidence.verified == 1
            ).all()
            
            reqs_with_evidence.append({
                "id": req.id,
                "statement": req.statement,
                "evidence": [
                    {
                        "segment_id": evd.segment_id,
                        "quote": evd.verbatim_quote
                    }
                    for evd in evidence_list
                ]
            })
        
        if not reqs_with_evidence:
            continue
        
        # Call LLM to detect contradictions (only on pre-filtered candidates)
        conflict_pairs = await llm_client.detect_contradictions(reqs_with_evidence)
        
        # Create contradiction records
        for pair in conflict_pairs:
            req_id_1 = pair["requirement_id_1"]
            req_id_2 = pair["requirement_id_2"]
            description = pair["conflict_description"]
            
            contradiction_id = generate_contradiction_id(req_id_1, req_id_2)
            
            # Check if already exists
            existing = db.query(Contradiction).filter(
                Contradiction.id == contradiction_id
            ).first()
            
            if not existing:
                contradiction = Contradiction(
                    id=contradiction_id,
                    workspace_id=workspace_id,
                    requirement_id_1=req_id_1,
                    requirement_id_2=req_id_2,
                    conflict_description=description,
                    status="open"
                )
                db.add(contradiction)
                contradictions.append(contradiction)
    
    db.commit()
    
    return contradictions


def _pre_filter_contradiction_candidates(requirements: List[Requirement]) -> List[tuple]:
    """
    Sprint 10: Pre-filter requirement pairs that might contradict.
    
    Uses keyword overlap to identify candidates before sending to LLM.
    This reduces cost from O(n²) to O(k) where k << n².
    
    Returns list of (req_id_1, req_id_2) tuples to check with LLM.
    """
    import re
    from collections import defaultdict
    
    # Extract keywords from each requirement (nouns, verbs, significant terms)
    req_keywords = {}
    keyword_to_reqs = defaultdict(set)
    
    for req in requirements:
        # Simple keyword extraction: words 4+ chars, lowercase, no stopwords
        stopwords = {'must', 'should', 'will', 'can', 'the', 'and', 'for', 'with', 'that', 'this', 'from'}
        words = re.findall(r'\b\w{4,}\b', req.statement.lower())
        keywords = set(w for w in words if w not in stopwords)
        
        req_keywords[req.id] = keywords
        
        # Build inverted index
        for keyword in keywords:
            keyword_to_reqs[keyword].add(req.id)
    
    # Find pairs with overlapping keywords
    candidates = set()
    
    for keyword, req_ids in keyword_to_reqs.items():
        if len(req_ids) >= 2:
            # Requirements sharing this keyword might contradict
            req_list = list(req_ids)
            for i in range(len(req_list)):
                for j in range(i + 1, len(req_list)):
                    req_id_1, req_id_2 = sorted([req_list[i], req_list[j]])
                    
                    # Check if they share enough keywords (threshold: 2+)
                    overlap = len(req_keywords[req_id_1] & req_keywords[req_id_2])
                    if overlap >= 2:
                        candidates.add((req_id_1, req_id_2))
    
    return list(candidates)


def resolve_contradiction(
    contradiction_id: str,
    resolution: str,
    notes: str,
    db: Session,
    workspace_id: str
) -> Contradiction:
    """
    Mark contradiction as resolved (human decision).
    
    resolution: "resolved" or "dismissed"
    Sprint 8: Now scoped to workspace.
    """
    contradiction = db.query(Contradiction).filter(
        Contradiction.id == contradiction_id,
        Contradiction.workspace_id == workspace_id
    ).first()
    
    if not contradiction:
        raise ValueError(f"Contradiction {contradiction_id} not found")
    
    contradiction.status = resolution
    contradiction.resolution_notes = notes
    
    db.commit()
    db.refresh(contradiction)
    
    return contradiction
