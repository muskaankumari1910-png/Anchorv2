import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import AuditEvent, Requirement


def generate_audit_id(requirement_id: str, action: str, timestamp: str) -> str:
    """Generate stable ID for audit event"""
    hasher = hashlib.sha256()
    hasher.update(requirement_id.encode('utf-8'))
    hasher.update(action.encode('utf-8'))
    hasher.update(timestamp.encode('utf-8'))
    return f"aud_{hasher.hexdigest()[:16]}"


def log_action(
    requirement_id: str,
    action: str,
    before: Optional[Dict[Any, Any]],
    after: Optional[Dict[Any, Any]],
    actor: str,
    notes: Optional[str],
    db: Session,
    workspace_id: str
) -> AuditEvent:
    """
    Log a user action on a requirement.
    
    Actions: accept, reject, edit, merge, unmerge
    Sprint 8: Now scoped to workspace.
    """
    timestamp = datetime.utcnow().isoformat()
    audit_id = generate_audit_id(requirement_id, action, timestamp)
    
    audit_event = AuditEvent(
        id=audit_id,
        workspace_id=workspace_id,
        requirement_id=requirement_id,
        action=action,
        before=json.dumps(before) if before else None,
        after=json.dumps(after) if after else None,
        actor=actor,
        notes=notes
    )
    
    db.add(audit_event)
    db.commit()
    
    return audit_event


def accept_requirement(
    requirement_id: str,
    actor: str,
    db: Session,
    workspace_id: str
) -> Requirement:
    """
    Accept a requirement (mark as reviewed and accepted).
    Logs audit event.
    Sprint 8: Now scoped to workspace.
    """
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.workspace_id == workspace_id
    ).first()
    
    if not requirement:
        raise ValueError(f"Requirement {requirement_id} not found in workspace {workspace_id}")
    
    # Log action
    before = {"statement": requirement.statement, "grounding": requirement.grounding.value}
    
    # Mark as accepted (we can add an 'accepted' field if needed, for now just log)
    # In a full implementation, you'd add a 'review_status' field
    
    after = {"statement": requirement.statement, "grounding": requirement.grounding.value}
    
    log_action(
        requirement_id=requirement_id,
        action="accept",
        before=before,
        after=after,
        actor=actor,
        notes="Requirement accepted by reviewer",
        db=db,
        workspace_id=workspace_id
    )
    
    return requirement


def reject_requirement(
    requirement_id: str,
    actor: str,
    reason: str,
    db: Session,
    workspace_id: str
) -> Requirement:
    """
    Reject a requirement.
    Logs audit event.
    Sprint 8: Now scoped to workspace.
    """
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.workspace_id == workspace_id
    ).first()
    
    if not requirement:
        raise ValueError(f"Requirement {requirement_id} not found in workspace {workspace_id}")
    
    before = {"statement": requirement.statement, "grounding": requirement.grounding.value}
    
    # Mark as rejected (in practice, might set is_merged=1 or add a 'rejected' status)
    requirement.is_merged = 1  # Soft delete
    
    after = {"statement": requirement.statement, "is_merged": 1}
    
    log_action(
        requirement_id=requirement_id,
        action="reject",
        before=before,
        after=after,
        actor=actor,
        notes=f"Rejected: {reason}",
        db=db,
        workspace_id=workspace_id
    )
    
    db.commit()
    
    return requirement


def edit_requirement(
    requirement_id: str,
    new_statement: str,
    actor: str,
    db: Session,
    workspace_id: str
) -> Requirement:
    """
    Edit a requirement statement.
    Logs audit event with before/after.
    Sprint 8: Now scoped to workspace.
    """
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.workspace_id == workspace_id
    ).first()
    
    if not requirement:
        raise ValueError(f"Requirement {requirement_id} not found in workspace {workspace_id}")
    
    before = {"statement": requirement.statement}
    
    requirement.statement = new_statement
    
    after = {"statement": new_statement}
    
    log_action(
        requirement_id=requirement_id,
        action="edit",
        before=before,
        after=after,
        actor=actor,
        notes="Statement edited by reviewer",
        db=db,
        workspace_id=workspace_id
    )
    
    db.commit()
    db.refresh(requirement)
    
    return requirement


def get_audit_trail(
    requirement_id: str,
    db: Session,
    workspace_id: str
):
    """
    Get all audit events for a requirement.
    Sprint 8: Now scoped to workspace.
    """
    events = db.query(AuditEvent).filter(
        AuditEvent.requirement_id == requirement_id,
        AuditEvent.workspace_id == workspace_id
    ).order_by(AuditEvent.timestamp.desc()).all()
    
    return events
