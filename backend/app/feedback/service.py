"""
Sprint 9: Feedback Loop Service

Collects accepted/edited requirements from audit events and converts them
into few-shot examples for improving LLM extraction prompts.

Key principles:
- Only use ACCEPTED, unedited requirements as positive examples
- Track workspace-specific learning (each client gets their own examples)
- Periodically select diverse sample to avoid prompt bloat
- Measure acceptance rate improvements over time
"""
import hashlib
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from app.models import (
    Requirement, Evidence, AuditEvent, Source, Segment,
    GroundingStatus, FeedbackExample
)
import json


def generate_example_id(requirement_id: str, workspace_id: str) -> str:
    """Generate stable ID for feedback example"""
    hasher = hashlib.sha256()
    hasher.update(requirement_id.encode('utf-8'))
    hasher.update(workspace_id.encode('utf-8'))
    return f"fbk_{hasher.hexdigest()[:16]}"


def collect_positive_examples(
    workspace_id: str,
    db: Session,
    max_examples: int = 10
) -> List[Dict]:
    """
    Collect positive training examples for a workspace.
    
    Criteria for positive examples:
    1. Requirement is GROUNDED
    2. Requirement was ACCEPTED (has 'accept' audit event)
    3. Requirement was NOT edited after acceptance
    4. Has verified evidence
    
    Returns list of few-shot examples formatted for prompt.
    """
    # Find accepted requirements that haven't been edited after acceptance
    accepted_reqs = db.query(Requirement).join(AuditEvent).filter(
        Requirement.workspace_id == workspace_id,
        Requirement.grounding == GroundingStatus.GROUNDED,
        Requirement.is_merged == 0,
        AuditEvent.requirement_id == Requirement.id,
        AuditEvent.action == "accept"
    ).all()
    
    positive_examples = []
    
    for req in accepted_reqs:
        # Check if requirement was edited AFTER being accepted
        accept_events = db.query(AuditEvent).filter(
            AuditEvent.requirement_id == req.id,
            AuditEvent.action == "accept"
        ).order_by(AuditEvent.timestamp.desc()).all()
        
        if not accept_events:
            continue
            
        latest_accept = accept_events[0]
        
        # Check for edits after acceptance
        edits_after = db.query(AuditEvent).filter(
            AuditEvent.requirement_id == req.id,
            AuditEvent.action == "edit",
            AuditEvent.timestamp > latest_accept.timestamp
        ).count()
        
        if edits_after > 0:
            # Skip - requirement was edited after acceptance
            continue
        
        # Get verified evidence
        evidence_list = db.query(Evidence).filter(
            Evidence.requirement_id == req.id,
            Evidence.verified == 1
        ).all()
        
        if not evidence_list:
            continue
        
        # Get original segments for context
        segments_data = []
        for evd in evidence_list:
            segment = db.query(Segment).filter(Segment.id == evd.segment_id).first()
            if segment:
                segments_data.append({
                    "id": segment.id,
                    "source_id": segment.source_id,
                    "index": segment.index,
                    "text": segment.text,
                    "speaker": segment.speaker,
                    "timestamp": segment.timestamp
                })
        
        # Create example
        example = {
            "segments": segments_data,
            "expected_output": {
                "statement": req.statement,
                "category": req.category,
                "type": req.type.value,
                "evidence": [
                    {
                        "source_id": evd.source_id,
                        "segment_id": evd.segment_id,
                        "verbatim_quote": evd.verbatim_quote
                    }
                    for evd in evidence_list
                ],
                "confidence": req.confidence.value
            }
        }
        
        positive_examples.append(example)
        
        if len(positive_examples) >= max_examples:
            break
    
    return positive_examples


def store_feedback_example(
    requirement_id: str,
    workspace_id: str,
    example_type: str,
    segments_json: str,
    expected_output_json: str,
    db: Session
) -> FeedbackExample:
    """
    Store a feedback example in the database.
    
    example_type: "positive" (accepted) or "negative" (rejected/edited)
    """
    example_id = generate_example_id(requirement_id, workspace_id)
    
    # Check if already exists
    existing = db.query(FeedbackExample).filter(
        FeedbackExample.id == example_id
    ).first()
    
    if existing:
        return existing
    
    example = FeedbackExample(
        id=example_id,
        workspace_id=workspace_id,
        requirement_id=requirement_id,
        example_type=example_type,
        segments_json=segments_json,
        expected_output_json=expected_output_json
    )
    
    db.add(example)
    db.commit()
    
    return example


def update_workspace_examples(
    workspace_id: str,
    db: Session
) -> int:
    """
    Update stored feedback examples for a workspace.
    
    Scans recent audit events and creates/updates examples.
    Returns count of examples processed.
    """
    examples_processed = 0
    
    # Find recently accepted requirements
    recent_accepts = db.query(AuditEvent).filter(
        AuditEvent.workspace_id == workspace_id,
        AuditEvent.action == "accept",
        AuditEvent.timestamp >= datetime.utcnow() - timedelta(days=7)
    ).all()
    
    for audit in recent_accepts:
        req = db.query(Requirement).filter(
            Requirement.id == audit.requirement_id,
            Requirement.workspace_id == workspace_id
        ).first()
        
        if not req or req.grounding != GroundingStatus.GROUNDED:
            continue
        
        # Get evidence and segments
        evidence_list = db.query(Evidence).filter(
            Evidence.requirement_id == req.id,
            Evidence.verified == 1
        ).all()
        
        if not evidence_list:
            continue
        
        segments_data = []
        for evd in evidence_list:
            segment = db.query(Segment).filter(Segment.id == evd.segment_id).first()
            if segment:
                segments_data.append({
                    "id": segment.id,
                    "source_id": segment.source_id,
                    "index": segment.index,
                    "text": segment.text,
                    "speaker": segment.speaker,
                    "timestamp": segment.timestamp
                })
        
        expected_output = {
            "statement": req.statement,
            "category": req.category,
            "type": req.type.value,
            "evidence": [
                {
                    "source_id": evd.source_id,
                    "segment_id": evd.segment_id,
                    "verbatim_quote": evd.verbatim_quote
                }
                for evd in evidence_list
            ],
            "confidence": req.confidence.value
        }
        
        # Store example
        store_feedback_example(
            requirement_id=req.id,
            workspace_id=workspace_id,
            example_type="positive",
            segments_json=json.dumps(segments_data),
            expected_output_json=json.dumps(expected_output),
            db=db
        )
        
        examples_processed += 1
    
    return examples_processed


def get_workspace_examples(
    workspace_id: str,
    db: Session,
    example_type: str = "positive",
    max_examples: int = 5
) -> List[Dict]:
    """
    Get stored feedback examples for a workspace.
    
    Returns examples formatted for few-shot prompting.
    """
    examples = db.query(FeedbackExample).filter(
        FeedbackExample.workspace_id == workspace_id,
        FeedbackExample.example_type == example_type
    ).order_by(FeedbackExample.created_at.desc()).limit(max_examples).all()
    
    formatted_examples = []
    
    for example in examples:
        try:
            segments = json.loads(example.segments_json)
            expected_output = json.loads(example.expected_output_json)
            
            formatted_examples.append({
                "segments": segments,
                "expected_output": expected_output
            })
        except json.JSONDecodeError:
            continue
    
    return formatted_examples


def measure_acceptance_rate(
    workspace_id: str,
    db: Session,
    days: int = 30
) -> Dict:
    """
    Measure acceptance rate for a workspace over time.
    
    Returns metrics to track if feedback loop is improving performance.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Count total extracted requirements (in time window)
    total_reqs = db.query(Requirement).filter(
        Requirement.workspace_id == workspace_id,
        Requirement.created_at >= cutoff_date
    ).count()
    
    if total_reqs == 0:
        return {
            "workspace_id": workspace_id,
            "time_window_days": days,
            "total_requirements": 0,
            "acceptance_rate": 0.0,
            "grounded_rate": 0.0,
            "edit_rate": 0.0
        }
    
    # Count grounded requirements
    grounded_reqs = db.query(Requirement).filter(
        Requirement.workspace_id == workspace_id,
        Requirement.grounding == GroundingStatus.GROUNDED,
        Requirement.created_at >= cutoff_date
    ).count()
    
    # Count accepted requirements
    accepted_reqs = db.query(Requirement).join(AuditEvent).filter(
        Requirement.workspace_id == workspace_id,
        AuditEvent.requirement_id == Requirement.id,
        AuditEvent.action == "accept",
        Requirement.created_at >= cutoff_date
    ).distinct().count()
    
    # Count edited requirements
    edited_reqs = db.query(Requirement).join(AuditEvent).filter(
        Requirement.workspace_id == workspace_id,
        AuditEvent.requirement_id == Requirement.id,
        AuditEvent.action == "edit",
        Requirement.created_at >= cutoff_date
    ).distinct().count()
    
    return {
        "workspace_id": workspace_id,
        "time_window_days": days,
        "total_requirements": total_reqs,
        "grounded_requirements": grounded_reqs,
        "accepted_requirements": accepted_reqs,
        "edited_requirements": edited_reqs,
        "grounded_rate": round((grounded_reqs / total_reqs) * 100, 2),
        "acceptance_rate": round((accepted_reqs / grounded_reqs) * 100, 2) if grounded_reqs > 0 else 0.0,
        "edit_rate": round((edited_reqs / grounded_reqs) * 100, 2) if grounded_reqs > 0 else 0.0
    }


def track_improvements(
    workspace_id: str,
    db: Session
) -> Dict:
    """
    Track improvements in acceptance rate over time.
    
    Compares last 30 days vs previous 30 days.
    """
    recent_metrics = measure_acceptance_rate(workspace_id, db, days=30)
    
    # Get previous period (31-60 days ago)
    cutoff_start = datetime.utcnow() - timedelta(days=60)
    cutoff_end = datetime.utcnow() - timedelta(days=30)
    
    prev_total = db.query(Requirement).filter(
        Requirement.workspace_id == workspace_id,
        Requirement.created_at >= cutoff_start,
        Requirement.created_at < cutoff_end
    ).count()
    
    if prev_total == 0:
        return {
            **recent_metrics,
            "previous_period_total": 0,
            "acceptance_rate_change": 0.0,
            "trend": "insufficient_data"
        }
    
    prev_grounded = db.query(Requirement).filter(
        Requirement.workspace_id == workspace_id,
        Requirement.grounding == GroundingStatus.GROUNDED,
        Requirement.created_at >= cutoff_start,
        Requirement.created_at < cutoff_end
    ).count()
    
    prev_accepted = db.query(Requirement).join(AuditEvent).filter(
        Requirement.workspace_id == workspace_id,
        AuditEvent.requirement_id == Requirement.id,
        AuditEvent.action == "accept",
        Requirement.created_at >= cutoff_start,
        Requirement.created_at < cutoff_end
    ).distinct().count()
    
    prev_acceptance_rate = (prev_accepted / prev_grounded * 100) if prev_grounded > 0 else 0.0
    
    change = recent_metrics["acceptance_rate"] - prev_acceptance_rate
    
    if change > 5.0:
        trend = "improving"
    elif change < -5.0:
        trend = "declining"
    else:
        trend = "stable"
    
    return {
        **recent_metrics,
        "previous_period_total": prev_total,
        "previous_acceptance_rate": round(prev_acceptance_rate, 2),
        "acceptance_rate_change": round(change, 2),
        "trend": trend
    }