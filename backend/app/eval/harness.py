from typing import Dict, List
from sqlalchemy.orm import Session
from app.ingest.service import ingest_file
from app.extraction.service import extract_and_ground_requirements
from app.coverage.service import analyze_coverage
from app.contradiction.service import detect_contradictions
from app.models import Requirement, Evidence, GroundingStatus
from app.eval.synthetic_data import (
    SYNTHETIC_TRANSCRIPT,
    GOLD_REQUIREMENTS,
    GOLD_CONTRADICTIONS,
    GOLD_UNGROUNDABLE
)


async def run_eval_harness(db: Session) -> Dict:
    """
    Run evaluation harness on synthetic transcript.
    
    Returns metrics dict with:
    - grounding_integrity: % of grounded requirements that should be grounded
    - fabrication_attempt_rate: % of requirements with fabrication attempts
    - ungrounded_shipped_rate: MUST BE 0 (critical)
    - precision: % of extracted requirements in gold set
    - recall: % of gold requirements extracted
    - contradiction_recall: % of gold contradictions detected
    """
    # Step 1: Ingest synthetic transcript
    filename = "synthetic_eval.txt"
    file_bytes = SYNTHETIC_TRANSCRIPT.encode('utf-8')
    
    source, segments = ingest_file(filename, file_bytes, db)
    
    # Step 2: Extract requirements
    requirements, extraction_stats = await extract_and_ground_requirements(source.id, db)
    
    # Step 3: Detect contradictions
    contradictions = await detect_contradictions(source.id, db)
    
    # Step 4: Analyze coverage
    coverage_data = await analyze_coverage(source.id, db)
    
    # Step 5: Calculate metrics
    
    # Get all grounded requirements
    grounded_reqs = [r for r in requirements if r.grounding == GroundingStatus.GROUNDED]
    quarantined_reqs = [r for r in requirements if r.grounding == GroundingStatus.QUARANTINED]
    ungrounded_reqs = [r for r in requirements if r.grounding == GroundingStatus.UNGROUNDED_CANDIDATE]
    
    # CRITICAL: ungrounded_shipped_rate MUST be 0
    # This means no requirement with fabricated citations reached "grounded" status
    total_requirements = len(requirements)
    requirements_with_fabrications = len([r for r in requirements if r.fabrication_attempts > 0])
    
    # Check if any fabricated requirement is grounded (MUST NOT HAPPEN)
    grounded_with_fabrications = [
        r for r in grounded_reqs if r.fabrication_attempts > 0
    ]
    ungrounded_shipped_rate = len(grounded_with_fabrications) / total_requirements if total_requirements > 0 else 0
    
    # Grounding integrity
    # All grounded requirements should match gold set
    correctly_grounded = 0
    for req in grounded_reqs:
        # Check if requirement matches gold set (simplified - check statement similarity)
        for gold in GOLD_REQUIREMENTS:
            if gold["grounded"] and _statements_similar(req.statement, gold["statement"]):
                correctly_grounded += 1
                break
    
    grounding_integrity = (correctly_grounded / len(grounded_reqs)) * 100 if grounded_reqs else 0
    
    # Fabrication attempt rate
    fabrication_attempt_rate = (requirements_with_fabrications / total_requirements) * 100 if total_requirements > 0 else 0
    
    # Precision: % of extracted requirements in gold set
    matched_extracted = 0
    for req in grounded_reqs:
        for gold in GOLD_REQUIREMENTS:
            if _statements_similar(req.statement, gold["statement"]):
                matched_extracted += 1
                break
    
    precision = (matched_extracted / len(grounded_reqs)) * 100 if grounded_reqs else 0
    
    # Recall: % of gold requirements extracted
    matched_gold = 0
    for gold in GOLD_REQUIREMENTS:
        if not gold["grounded"]:
            continue
        for req in grounded_reqs:
            if _statements_similar(req.statement, gold["statement"]):
                matched_gold += 1
                break
    
    recall = (matched_gold / len(GOLD_REQUIREMENTS)) * 100 if GOLD_REQUIREMENTS else 0
    
    # Contradiction recall
    contradiction_recall = (len(contradictions) / len(GOLD_CONTRADICTIONS)) * 100 if GOLD_CONTRADICTIONS else 0
    
    return {
        "total_requirements": total_requirements,
        "grounded": len(grounded_reqs),
        "quarantined": len(quarantined_reqs),
        "ungrounded_candidates": len(ungrounded_reqs),
        
        # Critical metrics
        "grounding_integrity_pct": round(grounding_integrity, 2),
        "fabrication_attempt_rate_pct": round(fabrication_attempt_rate, 2),
        "ungrounded_shipped_rate_pct": round(ungrounded_shipped_rate * 100, 2),  # MUST BE 0
        
        # Quality metrics
        "precision_pct": round(precision, 2),
        "recall_pct": round(recall, 2),
        "contradiction_recall_pct": round(contradiction_recall, 2),
        
        # Additional stats
        "contradictions_detected": len(contradictions),
        "coverage_pct": coverage_data["coverage_percentage"],
        "gaps_count": len(coverage_data["gaps"]),
        
        # Pass/Fail
        "PASS": ungrounded_shipped_rate == 0,  # Critical: must be exactly 0
        "grounding_check_working": ungrounded_shipped_rate == 0
    }


def _statements_similar(s1: str, s2: str) -> bool:
    """
    Simple similarity check for evaluation.
    In production, use more sophisticated matching.
    """
    # Normalize and check for substantial overlap
    s1_words = set(s1.lower().split())
    s2_words = set(s2.lower().split())
    
    if not s1_words or not s2_words:
        return False
    
    overlap = len(s1_words & s2_words)
    smaller_len = min(len(s1_words), len(s2_words))
    
    return (overlap / smaller_len) > 0.5  # 50% word overlap
