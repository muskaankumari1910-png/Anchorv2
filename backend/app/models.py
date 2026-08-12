from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Index, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime
import enum


class SourceType(str, enum.Enum):
    TXT = "txt"
    DOCX = "docx"
    MD = "md"
    VTT = "vtt"
    TRANSCRIPT = "transcript"


class SourceStatus(str, enum.Enum):
    PROCESSED = "processed"
    NOT_MACHINE_READABLE = "not_machine_readable"
    REJECTED = "rejected"


class RequirementType(str, enum.Enum):
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non-functional"
    CONSTRAINT = "constraint"
    BUSINESS_RULE = "business-rule"


class GroundingStatus(str, enum.Enum):
    GROUNDED = "grounded"
    QUARANTINED = "quarantined"
    UNGROUNDED_CANDIDATE = "ungrounded_candidate"


class ConfidenceLevel(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Source(Base):
    """
    Represents an uploaded source file (transcript or document).
    Sprint 8: Added workspace_id for multi-tenancy.
    """
    __tablename__ = "sources"

    id = Column(String, primary_key=True)  # Stable hash-based ID
    workspace_id = Column(String, nullable=False, index=True, default="default", server_default="default")  # Sprint 8: Multi-tenancy
    filename = Column(String, nullable=False)
    type = Column(SQLEnum(SourceType), nullable=False)
    status = Column(SQLEnum(SourceStatus), nullable=False, default=SourceStatus.PROCESSED)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    error_message = Column(Text, nullable=True)  # For rejected/unreadable files

    # Relationships
    segments = relationship("Segment", back_populates="source", cascade="all, delete-orphan")


class Segment(Base):
    """
    Represents a single addressable unit of text from a source.
    For transcripts: one utterance (speaker turn).
    For documents: one paragraph or heading.
    Sprint 8: Added workspace_id for multi-tenancy.
    """
    __tablename__ = "segments"

    id = Column(String, primary_key=True)  # Stable hash-based ID
    workspace_id = Column(String, nullable=False, index=True, default="default", server_default="default")  # Sprint 8: Multi-tenancy
    source_id = Column(String, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    index = Column(Integer, nullable=False)  # Sequential position in source
    speaker = Column(String, nullable=True)  # For transcripts only
    timestamp = Column(String, nullable=True)  # For transcripts only (e.g., "00:01:23")
    text = Column(Text, nullable=False)  # Character-perfect original text

    # Relationships
    source = relationship("Source", back_populates="segments")

    # Indexes for efficient lookup
    __table_args__ = (
        Index("ix_segment_source_id", "source_id"),
        Index("ix_segment_source_index", "source_id", "index"),
        Index("ix_segment_workspace", "workspace_id"),  # Sprint 8
    )


class Requirement(Base):
    """
    Represents an extracted requirement.
    Sprint 2: Grounded extraction with evidence.
    Sprint 3: De-duplication support.
    Sprint 8: Added workspace_id for multi-tenancy.
    """
    __tablename__ = "requirements"

    id = Column(String, primary_key=True)  # req_{hash}
    workspace_id = Column(String, nullable=False, index=True, default="default", server_default="default")  # Sprint 8: Multi-tenancy
    statement = Column(Text, nullable=False)
    category = Column(String, nullable=True)  # e.g., "authentication", "reporting"
    type = Column(SQLEnum(RequirementType), nullable=False)
    grounding = Column(SQLEnum(GroundingStatus), nullable=False)
    confidence = Column(SQLEnum(ConfidenceLevel), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Fabrication tracking
    fabrication_attempts = Column(Integer, default=0, nullable=False)
    
    # If ungrounded_candidate, why?
    ungrounded_reasoning = Column(Text, nullable=True)
    
    # Sprint 3: De-duplication
    merged_into = Column(String, ForeignKey("requirements.id"), nullable=True)  # If this was merged into another
    is_merged = Column(Integer, default=0, nullable=False)  # 1 if merged (inactive)

    # Relationships
    evidence = relationship("Evidence", back_populates="requirement", cascade="all, delete-orphan")
    feedback_examples = relationship("FeedbackExample", back_populates="requirement", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_requirement_grounding", "grounding"),
        Index("ix_requirement_type", "type"),
        Index("ix_requirement_workspace", "workspace_id"),  # Sprint 8
    )



class Evidence(Base):
    """
    Links a requirement to its source quote (grounding).
    One requirement can have multiple evidence entries (multiple quotes).
    Sprint 8: Added workspace_id for multi-tenancy.
    """
    __tablename__ = "evidence"

    id = Column(String, primary_key=True)  # evd_{hash}
    workspace_id = Column(String, nullable=False, index=True, default="default", server_default="default")  # Sprint 8: Multi-tenancy
    requirement_id = Column(String, ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(String, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    segment_id = Column(String, ForeignKey("segments.id", ondelete="CASCADE"), nullable=False)
    verbatim_quote = Column(Text, nullable=False)
    
    # Grounding verification metadata
    verified = Column(Integer, default=0, nullable=False)  # 0 = not verified, 1 = passed, -1 = failed
    verification_method = Column(String, nullable=True)  # "exact_match" or "fuzzy_match"
    source_mismatch = Column(Integer, default=0, nullable=False)  # 1 = quote found but in wrong segment

    # Relationships
    requirement = relationship("Requirement", back_populates="evidence")
    source = relationship("Source")
    segment = relationship("Segment")

    __table_args__ = (
        Index("ix_evidence_requirement", "requirement_id"),
        Index("ix_evidence_segment", "segment_id"),
        Index("ix_evidence_workspace", "workspace_id"),  # Sprint 8
    )



class FeedbackExample(Base):
    """
    Sprint 9: Feedback examples for few-shot learning.
    
    Stores accepted/edited requirements as training examples
    to improve extraction prompts over time.
    """
    __tablename__ = "feedback_examples"
    
    id = Column(String, primary_key=True)  # fbk_...
    workspace_id = Column(String, nullable=False, index=True, default="default", server_default="default")
    requirement_id = Column(String, ForeignKey("requirements.id"), nullable=False)
    example_type = Column(String, nullable=False)  # "positive" or "negative"
    segments_json = Column(Text, nullable=False)  # JSON array of segments
    expected_output_json = Column(Text, nullable=False)  # JSON of expected requirement
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    requirement = relationship("Requirement", back_populates="feedback_examples")


class MergeSuggestion(Base):
    """
    Suggests two requirements that might be duplicates.
    Sprint 3: De-duplication requires human confirmation.
    Sprint 8: Added workspace_id for multi-tenancy.
    """
    __tablename__ = "merge_suggestions"

    id = Column(String, primary_key=True)  # mrg_{hash}
    workspace_id = Column(String, nullable=False, index=True, default="default", server_default="default")  # Sprint 8: Multi-tenancy
    requirement_id_1 = Column(String, ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    requirement_id_2 = Column(String, ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    similarity_score = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=True)
    status = Column(String, default="pending", nullable=False)  # pending, accepted, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_merge_suggestion_status", "status"),
        Index("ix_merge_workspace", "workspace_id"),  # Sprint 8
    )


class SegmentConsumption(Base):
    """
    Tracks which segments have been consumed (contributed to requirements).
    Sprint 3: Coverage analysis.
    Sprint 8: Added workspace_id for multi-tenancy.
    """
    __tablename__ = "segment_consumption"

    id = Column(String, primary_key=True)  # con_{hash}
    workspace_id = Column(String, nullable=False, index=True, default="default", server_default="default")  # Sprint 8: Multi-tenancy
    segment_id = Column(String, ForeignKey("segments.id", ondelete="CASCADE"), nullable=False)
    requirement_id = Column(String, ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    consumed_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_consumption_segment", "segment_id"),
        Index("ix_consumption_requirement", "requirement_id"),
        Index("ix_consumption_workspace", "workspace_id"),  # Sprint 8
    )


class Gap(Base):
    """
    Represents a potential gap - unconsumed substantive segment.
    Sprint 3: Coverage analysis.
    Sprint 8: Added workspace_id for multi-tenancy.
    """
    __tablename__ = "gaps"

    id = Column(String, primary_key=True)  # gap_{hash}
    workspace_id = Column(String, nullable=False, index=True, default="default", server_default="default")  # Sprint 8: Multi-tenancy
    segment_id = Column(String, ForeignKey("segments.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(String, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    is_filler = Column(Integer, default=0, nullable=False)  # 1 = greeting/filler, 0 = substantive
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    segment = relationship("Segment")
    source = relationship("Source")

    __table_args__ = (
        Index("ix_gap_is_filler", "is_filler"),
        Index("ix_gap_source", "source_id"),
        Index("ix_gap_workspace", "workspace_id"),  # Sprint 8
    )



class Contradiction(Base):
    """
    Represents a detected contradiction between two requirements.
    Sprint 4: Contradiction detection (no auto-resolution).
    Sprint 8: Added workspace_id for multi-tenancy.
    """
    __tablename__ = "contradictions"

    id = Column(String, primary_key=True)  # ctr_{hash}
    workspace_id = Column(String, nullable=False, index=True, default="default", server_default="default")  # Sprint 8: Multi-tenancy
    requirement_id_1 = Column(String, ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    requirement_id_2 = Column(String, ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    conflict_description = Column(Text, nullable=False)
    status = Column(String, default="open", nullable=False)  # open, resolved, dismissed
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    req1 = relationship("Requirement", foreign_keys=[requirement_id_1])
    req2 = relationship("Requirement", foreign_keys=[requirement_id_2])

    __table_args__ = (
        Index("ix_contradiction_status", "status"),
        Index("ix_contradiction_workspace", "workspace_id"),  # Sprint 8
    )

class AuditEvent(Base):
    """
    Tracks all human actions on requirements.
    Sprint 4: Audit trail for accept/edit/reject.
    Sprint 8: Added workspace_id for multi-tenancy.
    """
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True)  # aud_{hash}
    workspace_id = Column(String, nullable=False, index=True, default="default", server_default="default")  # Sprint 8: Multi-tenancy
    requirement_id = Column(String, ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    action = Column(String, nullable=False)  # accept, reject, edit, merge, unmerge
    before = Column(Text, nullable=True)  # JSON snapshot before action
    after = Column(Text, nullable=True)  # JSON snapshot after action
    actor = Column(String, default="user", nullable=False)  # User identifier
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)

    # Relationship
    requirement = relationship("Requirement")

    __table_args__ = (
        Index("ix_audit_requirement", "requirement_id"),
        Index("ix_audit_action", "action"),
        Index("ix_audit_timestamp", "timestamp"),
        Index("ix_audit_workspace", "workspace_id"),  # Sprint 8
    )
