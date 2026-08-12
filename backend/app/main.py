from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
from app.database import get_db, engine, Base
from app.models import Source, Segment, Requirement, Evidence, MergeSuggestion, Gap, Contradiction, AuditEvent, GroundingStatus
from app.workspace import get_workspace_id, scope_query_to_workspace  # Sprint 8
from app.ingest.service import ingest_file, handle_ingest_error
from app.ingest.exceptions import UnparseableFileError, NotMachineReadableError
from app.extraction.service import extract_and_ground_requirements
from app.dedup.service import detect_duplicates, merge_requirements, unmerge_requirements
from app.coverage.service import analyze_coverage
from app.contradiction.service import detect_contradictions, resolve_contradiction
from app.audit.service import accept_requirement, reject_requirement, edit_requirement, get_audit_trail
from app.export.service import export_to_docx, export_to_markdown
from app.eval.harness import run_eval_harness
from app.feedback.service import update_workspace_examples, measure_acceptance_rate, track_improvements  # Sprint 9
from pydantic import BaseModel

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Anchor API", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",        # nginx reverse proxy (port 80)
        "http://localhost:80",
        "http://localhost:3000",   # Vite dev server
        "http://localhost:3001",   # frontend container (mapped 3001:80)
        "http://localhost:5173",   # Vite preview
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Response models
class SegmentResponse(BaseModel):
    id: str
    source_id: str
    index: int
    speaker: str | None
    timestamp: str | None
    text: str

    class Config:
        from_attributes = True


class SourceResponse(BaseModel):
    id: str
    filename: str
    type: str
    status: str
    uploaded_at: str
    error_message: str | None
    segments: List[SegmentResponse] = []

    class Config:
        from_attributes = True


@app.get("/")
def root():
    return {"message": "Anchor API - Sprint 5: Export + Eval + Non-AI Fallback"}


@app.post("/api/ingest", response_model=SourceResponse)
async def ingest_endpoint(
    file: UploadFile = File(..., description="Upload TXT, MD, DOCX, VTT, or transcript files (max 200MB)"),
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)  # Sprint 8: Multi-tenancy
):
    """
    Ingest a file (transcript or document) and segment it.
    Returns Source and Segment records with stable IDs.
    
    Supported formats:
    - TXT: Plain text documents
    - MD: Markdown documents  
    - DOCX: Microsoft Word documents
    - VTT: WebVTT transcript files
    - Transcript: Speaker-labeled text files
    
    File size limit: 200MB
    
    Sprint 8: Now scoped to workspace (via X-Workspace-ID header or defaults to "default").
    """
    # Check file size (200MB limit)
    MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB in bytes
    
    file_bytes = await file.read()
    file_size = len(file_bytes)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {file_size / (1024*1024):.1f}MB. Maximum allowed: 200MB"
        )
    
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    
    # Validate file extension
    supported_extensions = {'.txt', '.md', '.docx', '.vtt'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in supported_extensions and not _looks_like_transcript(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Supported: TXT, MD, DOCX, VTT, or transcript files"
        )
    
    try:
        source, segments = ingest_file(file.filename, file_bytes, db, workspace_id)
        
        return SourceResponse(
            id=source.id,
            filename=source.filename,
            type=source.type.value,
            status=source.status.value,
            uploaded_at=source.uploaded_at.isoformat(),
            error_message=source.error_message,
            segments=[
                SegmentResponse(
                    id=seg.id,
                    source_id=seg.source_id,
                    index=seg.index,
                    speaker=seg.speaker,
                    timestamp=seg.timestamp,
                    text=seg.text
                ) for seg in segments
            ]
        )
    
    except (UnparseableFileError, NotMachineReadableError) as e:
        # Create error source record, don't just fail
        source = handle_ingest_error(file.filename, e, file_bytes, db, workspace_id)
        raise HTTPException(status_code=400, detail={
            "error": type(e).__name__,
            "message": str(e),
            "source_id": source.id,
            "status": source.status.value,
            "supported_formats": "TXT, MD, DOCX, VTT, or speaker-labeled transcript"
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error during file processing: {str(e)}")


def _looks_like_transcript(filename: str) -> bool:
    """Check if filename suggests it's a transcript (even without standard extension)"""
    filename_lower = filename.lower()
    transcript_indicators = ['transcript', 'interview', 'meeting', 'call', 'conversation', 'discussion']
    return any(indicator in filename_lower for indicator in transcript_indicators)


@app.get("/api/sources", response_model=List[SourceResponse])
def list_sources(
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    List all sources.
    Sprint 8: Now scoped to workspace.
    """
    query = db.query(Source)
    query = scope_query_to_workspace(query, Source, workspace_id)
    sources = query.all()
    result = []
    
    for source in sources:
        segments = db.query(Segment).filter(
            Segment.source_id == source.id
        ).order_by(Segment.index).all()
        
        result.append(SourceResponse(
            id=source.id,
            filename=source.filename,
            type=source.type.value,
            status=source.status.value,
            uploaded_at=source.uploaded_at.isoformat(),
            error_message=source.error_message,
            segments=[
                SegmentResponse(
                    id=seg.id,
                    source_id=seg.source_id,
                    index=seg.index,
                    speaker=seg.speaker,
                    timestamp=seg.timestamp,
                    text=seg.text
                ) for seg in segments
            ]
        ))
    
    return result


@app.get("/api/sources/{source_id}", response_model=SourceResponse)
def get_source(
    source_id: str,
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    Get a specific source with its segments.
    Sprint 8: Now scoped to workspace.
    """
    source = db.query(Source).filter(
        Source.id == source_id,
        Source.workspace_id == workspace_id
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    segments = db.query(Segment).filter(
        Segment.source_id == source_id
    ).order_by(Segment.index).all()
    
    return SourceResponse(
        id=source.id,
        filename=source.filename,
        type=source.type.value,
        status=source.status.value,
        uploaded_at=source.uploaded_at.isoformat(),
        error_message=source.error_message,
        segments=[
            SegmentResponse(
                id=seg.id,
                source_id=seg.source_id,
                index=seg.index,
                speaker=seg.speaker,
                timestamp=seg.timestamp,
                text=seg.text
            ) for seg in segments
        ]
    )



# Sprint 2 response models
class EvidenceResponse(BaseModel):
    id: str
    requirement_id: str
    source_id: str
    segment_id: str
    verbatim_quote: str
    verified: int
    verification_method: str | None
    source_mismatch: int

    class Config:
        from_attributes = True


class RequirementResponse(BaseModel):
    id: str
    statement: str
    category: str | None
    type: str
    grounding: str
    confidence: str
    fabrication_attempts: int
    ungrounded_reasoning: str | None
    evidence: List[EvidenceResponse] = []

    class Config:
        from_attributes = True


class ExtractionStatsResponse(BaseModel):
    total_proposed: int
    grounded: int
    quarantined: int
    ungrounded_candidates: int
    fabrication_attempts: int


class ExtractionResponse(BaseModel):
    source_id: str
    requirements: List[RequirementResponse]
    stats: ExtractionStatsResponse


@app.post("/api/extract/{source_id}", response_model=ExtractionResponse)
async def extract_requirements_endpoint(
    source_id: str,
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    Extract requirements from a source and verify grounding.
    
    Pipeline:
    1. LLM extracts requirements with citations (proposes)
    2. Code verifies citations are real (deterministic check)
    3. Requirements marked grounded or quarantined
    
    Sprint 8: Now scoped to workspace.
    """
    # Fail fast with a clear message if the LLM key is not configured,
    # rather than surfacing an opaque 401 from the provider.
    from app.config import settings
    if not (settings.groq_api_key or settings.huggingface_api_key):
        raise HTTPException(
            status_code=503,
            detail="LLM API key is not configured. Set GROQ_API_KEY in your environment / .env file."
        )
    try:
        requirements, stats = await extract_and_ground_requirements(source_id, db, workspace_id)
        
        # Load evidence for each requirement
        requirements_with_evidence = []
        for req in requirements:
            evidence_list = db.query(Evidence).filter(
                Evidence.requirement_id == req.id,
                Evidence.workspace_id == workspace_id
            ).all()
            
            requirements_with_evidence.append(RequirementResponse(
                id=req.id,
                statement=req.statement,
                category=req.category,
                type=req.type.value,
                grounding=req.grounding.value,
                confidence=req.confidence.value,
                fabrication_attempts=req.fabrication_attempts,
                ungrounded_reasoning=req.ungrounded_reasoning,
                evidence=[
                    EvidenceResponse(
                        id=evd.id,
                        requirement_id=evd.requirement_id,
                        source_id=evd.source_id,
                        segment_id=evd.segment_id,
                        verbatim_quote=evd.verbatim_quote,
                        verified=evd.verified,
                        verification_method=evd.verification_method,
                        source_mismatch=evd.source_mismatch
                    ) for evd in evidence_list
                ]
            ))
        
        return ExtractionResponse(
            source_id=source_id,
            requirements=requirements_with_evidence,
            stats=ExtractionStatsResponse(**stats)
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.get("/api/requirements", response_model=List[RequirementResponse])
def list_requirements(
    grounding: str | None = None,
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    List all requirements, optionally filtered by grounding status.
    
    Query params:
    - grounding: Filter by 'grounded', 'quarantined', or 'ungrounded_candidate'
    
    Sprint 8: Now scoped to workspace.
    """
    query = db.query(Requirement)
    query = scope_query_to_workspace(query, Requirement, workspace_id)
    
    if grounding:
        query = query.filter(Requirement.grounding == grounding)
    
    requirements = query.all()
    
    result = []
    for req in requirements:
        evidence_list = db.query(Evidence).filter(
            Evidence.requirement_id == req.id,
            Evidence.workspace_id == workspace_id
        ).all()
        
        result.append(RequirementResponse(
            id=req.id,
            statement=req.statement,
            category=req.category,
            type=req.type.value,
            grounding=req.grounding.value,
            confidence=req.confidence.value,
            fabrication_attempts=req.fabrication_attempts,
            ungrounded_reasoning=req.ungrounded_reasoning,
            evidence=[
                EvidenceResponse(
                    id=evd.id,
                    requirement_id=evd.requirement_id,
                    source_id=evd.source_id,
                    segment_id=evd.segment_id,
                    verbatim_quote=evd.verbatim_quote,
                    verified=evd.verified,
                    verification_method=evd.verification_method,
                    source_mismatch=evd.source_mismatch
                ) for evd in evidence_list
            ]
        ))
    
    return result


@app.get("/api/requirements/{requirement_id}", response_model=RequirementResponse)
def get_requirement(
    requirement_id: str,
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    Get a specific requirement with its evidence.
    Sprint 8: Now scoped to workspace.
    """
    req = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.workspace_id == workspace_id
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    evidence_list = db.query(Evidence).filter(
        Evidence.requirement_id == req.id,
        Evidence.workspace_id == workspace_id
    ).all()
    
    return RequirementResponse(
        id=req.id,
        statement=req.statement,
        category=req.category,
        type=req.type.value,
        grounding=req.grounding.value,
        confidence=req.confidence.value,
        fabrication_attempts=req.fabrication_attempts,
        ungrounded_reasoning=req.ungrounded_reasoning,
        evidence=[
            EvidenceResponse(
                id=evd.id,
                requirement_id=evd.requirement_id,
                source_id=evd.source_id,
                segment_id=evd.segment_id,
                verbatim_quote=evd.verbatim_quote,
                verified=evd.verified,
                verification_method=evd.verification_method,
                source_mismatch=evd.source_mismatch
            ) for evd in evidence_list
        ]
    )



# Sprint 3 response models
class MergeSuggestionResponse(BaseModel):
    id: str
    requirement_id_1: str
    requirement_id_2: str
    similarity_score: float
    reasoning: str | None
    status: str

    class Config:
        from_attributes = True


class GapResponse(BaseModel):
    segment_id: str
    segment_index: int
    segment_text: str
    speaker: str | None
    is_filler: bool


class CoverageResponse(BaseModel):
    source_id: str
    total_segments: int
    consumed_segments: int
    unconsumed_segments: int
    coverage_percentage: float
    is_incomplete: bool
    low_coverage_threshold: float
    gaps: List[GapResponse]
    filler_count: int


@app.post("/api/dedup/{source_id}", response_model=List[MergeSuggestionResponse])
async def detect_duplicates_endpoint(
    source_id: str,
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    Detect near-duplicate requirements within a source.
    Returns merge suggestions - NOT auto-applied.
    Human must confirm in Sprint 4 UI.
    
    Sprint 8: Now scoped to workspace.
    """
    try:
        suggestions = await detect_duplicates(source_id, db, workspace_id)
        
        return [
            MergeSuggestionResponse(
                id=s.id,
                requirement_id_1=s.requirement_id_1,
                requirement_id_2=s.requirement_id_2,
                similarity_score=s.similarity_score,
                reasoning=s.reasoning,
                status=s.status
            ) for s in suggestions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Duplicate detection failed: {str(e)}")


@app.post("/api/merge/{merge_suggestion_id}", response_model=RequirementResponse)
def merge_requirements_endpoint(
    merge_suggestion_id: str,
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    Execute a merge (human-confirmed).
    Combines two requirements, preserving ALL evidence.
    
    Sprint 8: Now scoped to workspace.
    """
    try:
        merged_req = merge_requirements(merge_suggestion_id, db, workspace_id)
        
        evidence_list = db.query(Evidence).filter(
            Evidence.requirement_id == merged_req.id,
            Evidence.workspace_id == workspace_id
        ).all()
        
        return RequirementResponse(
            id=merged_req.id,
            statement=merged_req.statement,
            category=merged_req.category,
            type=merged_req.type.value,
            grounding=merged_req.grounding.value,
            confidence=merged_req.confidence.value,
            fabrication_attempts=merged_req.fabrication_attempts,
            ungrounded_reasoning=merged_req.ungrounded_reasoning,
            evidence=[
                EvidenceResponse(
                    id=evd.id,
                    requirement_id=evd.requirement_id,
                    source_id=evd.source_id,
                    segment_id=evd.segment_id,
                    verbatim_quote=evd.verbatim_quote,
                    verified=evd.verified,
                    verification_method=evd.verification_method,
                    source_mismatch=evd.source_mismatch
                ) for evd in evidence_list
            ]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Merge failed: {str(e)}")


@app.post("/api/unmerge/{requirement_id}")
def unmerge_requirements_endpoint(
    requirement_id: str,
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    Undo a merge - restore original requirements.
    Sprint 8: Now scoped to workspace.
    """
    try:
        unmerged = unmerge_requirements(requirement_id, db, workspace_id)
        return {"message": f"Unmerged {len(unmerged)} requirements", "count": len(unmerged)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unmerge failed: {str(e)}")


@app.post("/api/coverage/{source_id}", response_model=CoverageResponse)
async def analyze_coverage_endpoint(
    source_id: str,
    low_coverage_threshold: float = 0.4,
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    Analyze coverage for a source:
    - Mark consumed segments
    - Identify gaps (unconsumed substantive segments)
    - Calculate coverage percentage
    - Flag if coverage too low
    
    Sprint 8: Now scoped to workspace.
    """
    try:
        coverage_data = await analyze_coverage(source_id, db, workspace_id, low_coverage_threshold)
        
        return CoverageResponse(
            source_id=coverage_data["source_id"],
            total_segments=coverage_data["total_segments"],
            consumed_segments=coverage_data["consumed_segments"],
            unconsumed_segments=coverage_data["unconsumed_segments"],
            coverage_percentage=coverage_data["coverage_percentage"],
            is_incomplete=coverage_data["is_incomplete"],
            low_coverage_threshold=coverage_data["low_coverage_threshold"],
            gaps=[GapResponse(**gap) for gap in coverage_data["gaps"]],
            filler_count=coverage_data["filler_count"]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Coverage analysis failed: {str(e)}")


@app.get("/api/merge-suggestions", response_model=List[MergeSuggestionResponse])
def list_merge_suggestions(
    status: str | None = None,
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    List merge suggestions, optionally filtered by status.
    
    Query params:
    - status: Filter by 'pending', 'accepted', or 'rejected'
    
    Sprint 8: Now scoped to workspace.
    """
    query = db.query(MergeSuggestion)
    query = scope_query_to_workspace(query, MergeSuggestion, workspace_id)
    
    if status:
        query = query.filter(MergeSuggestion.status == status)
    
    suggestions = query.all()
    
    return [
        MergeSuggestionResponse(
            id=s.id,
            requirement_id_1=s.requirement_id_1,
            requirement_id_2=s.requirement_id_2,
            similarity_score=s.similarity_score,
            reasoning=s.reasoning,
            status=s.status
        ) for s in suggestions
    ]



# Sprint 4 response models
class ContradictionResponse(BaseModel):
    id: str
    requirement_id_1: str
    requirement_id_2: str
    conflict_description: str
    status: str
    resolution_notes: str | None

    class Config:
        from_attributes = True


class AuditEventResponse(BaseModel):
    id: str
    requirement_id: str
    action: str
    before: str | None
    after: str | None
    actor: str
    timestamp: str
    notes: str | None

    class Config:
        from_attributes = True


@app.post("/api/contradictions/{source_id}", response_model=List[ContradictionResponse])
async def detect_contradictions_endpoint(
    source_id: str,
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    Detect contradictions between requirements.
    Returns conflict pairs - NOT auto-resolved.
    Human must decide in UI.
    
    Sprint 8: Now scoped to workspace.
    """
    try:
        contradictions = await detect_contradictions(source_id, db, workspace_id)
        
        return [
            ContradictionResponse(
                id=c.id,
                requirement_id_1=c.requirement_id_1,
                requirement_id_2=c.requirement_id_2,
                conflict_description=c.conflict_description,
                status=c.status,
                resolution_notes=c.resolution_notes
            ) for c in contradictions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contradiction detection failed: {str(e)}")


@app.post("/api/contradictions/{contradiction_id}/resolve")
def resolve_contradiction_endpoint(
    contradiction_id: str,
    resolution: str,
    notes: str = "",
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    Mark contradiction as resolved or dismissed (human decision).
    Sprint 8: Now scoped to workspace.
    """
    try:
        contradiction = resolve_contradiction(contradiction_id, resolution, notes, db, workspace_id)
        
        return ContradictionResponse(
            id=contradiction.id,
            requirement_id_1=contradiction.requirement_id_1,
            requirement_id_2=contradiction.requirement_id_2,
            conflict_description=contradiction.conflict_description,
            status=contradiction.status,
            resolution_notes=contradiction.resolution_notes
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resolution failed: {str(e)}")


@app.get("/api/contradictions", response_model=List[ContradictionResponse])
def list_contradictions(
    status: str | None = None,
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    List contradictions, optionally filtered by status.
    Sprint 8: Now scoped to workspace.
    """
    query = db.query(Contradiction)
    query = scope_query_to_workspace(query, Contradiction, workspace_id)
    
    if status:
        query = query.filter(Contradiction.status == status)
    
    contradictions = query.all()
    
    return [
        ContradictionResponse(
            id=c.id,
            requirement_id_1=c.requirement_id_1,
            requirement_id_2=c.requirement_id_2,
            conflict_description=c.conflict_description,
            status=c.status,
            resolution_notes=c.resolution_notes
        ) for c in contradictions
    ]


@app.post("/api/requirements/{requirement_id}/accept")
def accept_requirement_endpoint(
    requirement_id: str,
    actor: str = "user",
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    Accept a requirement (logs audit event).
    Sprint 8: Now scoped to workspace.
    """
    try:
        requirement = accept_requirement(requirement_id, actor, db, workspace_id)
        return {"message": "Requirement accepted", "requirement_id": requirement.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/requirements/{requirement_id}/reject")
def reject_requirement_endpoint(
    requirement_id: str,
    reason: str,
    actor: str = "user",
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    Reject a requirement (logs audit event, soft deletes).
    Sprint 8: Now scoped to workspace.
    """
    try:
        requirement = reject_requirement(requirement_id, actor, reason, db, workspace_id)
        return {"message": "Requirement rejected", "requirement_id": requirement.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/requirements/{requirement_id}/edit")
def edit_requirement_endpoint(
    requirement_id: str,
    new_statement: str,
    actor: str = "user",
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    Edit a requirement statement (logs audit event with before/after).
    Sprint 8: Now scoped to workspace.
    """
    try:
        requirement = edit_requirement(requirement_id, new_statement, actor, db, workspace_id)
        return RequirementResponse(
            id=requirement.id,
            statement=requirement.statement,
            category=requirement.category,
            type=requirement.type.value,
            grounding=requirement.grounding.value,
            confidence=requirement.confidence.value,
            fabrication_attempts=requirement.fabrication_attempts,
            ungrounded_reasoning=requirement.ungrounded_reasoning,
            evidence=[]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/requirements/{requirement_id}/audit", response_model=List[AuditEventResponse])
def get_audit_trail_endpoint(
    requirement_id: str,
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    Get audit trail for a requirement.
    Sprint 8: Now scoped to workspace.
    """
    events = get_audit_trail(requirement_id, db, workspace_id)
    
    return [
        AuditEventResponse(
            id=e.id,
            requirement_id=e.requirement_id,
            action=e.action,
            before=e.before,
            after=e.after,
            actor=e.actor,
            timestamp=e.timestamp.isoformat(),
            notes=e.notes
        ) for e in events
    ]


@app.get("/api/review/lanes")
def get_review_lanes(
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    Get requirements organized into four review lanes.
    
    Lane 1: Confirmed (grounded, not reviewed)
    Lane 2: Needs review (quarantined + ungrounded_candidates)
    Lane 3: Conflicts (open contradictions)
    Lane 4: Possible gaps (unconsumed substantive segments)
    
    Sprint 8: Now scoped to workspace.
    """
    # Lane 1: Grounded requirements
    confirmed = db.query(Requirement).filter(
        Requirement.workspace_id == workspace_id,
        Requirement.grounding == GroundingStatus.GROUNDED,
        Requirement.is_merged == 0
    ).all()
    
    # Lane 2: Needs review (quarantined + ungrounded)
    needs_review = db.query(Requirement).filter(
        Requirement.workspace_id == workspace_id,
        (Requirement.grounding == GroundingStatus.QUARANTINED) |
        (Requirement.grounding == GroundingStatus.UNGROUNDED_CANDIDATE),
        Requirement.is_merged == 0
    ).all()
    
    # Lane 3: Conflicts (open contradictions)
    conflicts = db.query(Contradiction).filter(
        Contradiction.workspace_id == workspace_id,
        Contradiction.status == "open"
    ).all()
    
    # Lane 4: Gaps (unconsumed substantive segments)
    gaps = db.query(Gap).filter(
        Gap.workspace_id == workspace_id,
        Gap.is_filler == 0
    ).all()
    
    return {
        "lane1_confirmed": [req.id for req in confirmed],
        "lane2_needs_review": [req.id for req in needs_review],
        "lane3_conflicts": [c.id for c in conflicts],
        "lane4_gaps": [g.id for g in gaps],
        "counts": {
            "confirmed": len(confirmed),
            "needs_review": len(needs_review),
            "conflicts": len(conflicts),
            "gaps": len(gaps)
        }
    }



# Sprint 5: Export endpoints
@app.get("/api/export/{source_id}/docx")
async def export_docx_endpoint(
    source_id: str,
    include_quarantined: bool = False,
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    Export requirements to .docx with traceability appendix.
    Warns if unresolved conflicts exist.
    
    Sprint 8: Now scoped to workspace.
    """
    try:
        buffer = export_to_docx(source_id, db, workspace_id, include_quarantined)
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename=requirements_{source_id}.docx"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.get("/api/export/{source_id}/markdown")
async def export_markdown_endpoint(
    source_id: str,
    include_quarantined: bool = False,
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id)
):
    """
    Export requirements to markdown with traceability appendix.
    Sprint 8: Now scoped to workspace.
    """
    try:
        markdown = export_to_markdown(source_id, db, workspace_id, include_quarantined)
        
        return Response(
            content=markdown,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=requirements_{source_id}.md"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# Sprint 5: Eval harness
@app.post("/api/eval/run")
async def run_eval_endpoint(db: Session = Depends(get_db)):
    """
    Run evaluation harness on synthetic transcript.
    
    Returns metrics including:
    - ungrounded_shipped_rate (MUST BE 0)
    - grounding_integrity
    - fabrication_attempt_rate
    - precision, recall
    - contradiction_recall
    """
    try:
        metrics = await run_eval_harness(db)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eval harness failed: {str(e)}")


# Sprint 9: Feedback loop endpoints
@app.post("/api/feedback/update/{workspace_id}")
def update_feedback_examples_endpoint(
    workspace_id: str,
    db: Session = Depends(get_db)
):
    """
    Update feedback examples for a workspace.
    
    Scans recent audit events and creates training examples
    from accepted requirements.
    
    Sprint 9: Feedback loop for prompt improvement.
    """
    try:
        count = update_workspace_examples(workspace_id, db)
        return {
            "workspace_id": workspace_id,
            "examples_processed": count,
            "message": f"Updated {count} feedback examples"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback update failed: {str(e)}")


@app.get("/api/feedback/metrics/{workspace_id}")
def get_feedback_metrics_endpoint(
    workspace_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get acceptance rate metrics for a workspace.
    
    Measures:
    - Total requirements extracted
    - Grounded rate
    - Acceptance rate  
    - Edit rate
    
    Sprint 9: Track feedback loop effectiveness.
    """
    try:
        metrics = measure_acceptance_rate(workspace_id, db, days)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics calculation failed: {str(e)}")


@app.get("/api/feedback/improvements/{workspace_id}")
def get_improvement_trends_endpoint(
    workspace_id: str,
    db: Session = Depends(get_db)
):
    """
    Track improvements in acceptance rate over time.
    
    Compares recent 30 days vs previous 30 days to identify trends.
    
    Sprint 9: Measure feedback loop impact.
    """
    try:
        trends = track_improvements(workspace_id, db)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@app.post("/api/admin/feedback/update-all")
def update_all_feedback_examples_endpoint(db: Session = Depends(get_db)):
    """
    Update feedback examples for ALL workspaces.
    
    Admin endpoint for manual feedback loop updates.
    Scans all workspaces and updates their examples from recent audit events.
    
    Sprint 9: Batch feedback update.
    """
    try:
        from app.feedback.scheduler import update_all_workspaces
        import asyncio
        
        result = asyncio.run(update_all_workspaces())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch feedback update failed: {str(e)}")


# Sprint 11: Cache management endpoints
@app.get("/api/admin/cache/stats")
def get_cache_stats():
    """
    Get extraction cache statistics.
    
    Sprint 11: Cache monitoring.
    """
    from app.extraction.cache import get_extraction_cache
    
    cache = get_extraction_cache()
    return cache.get_stats()


@app.post("/api/admin/cache/clear")
def clear_cache():
    """
    Clear the extraction cache.
    
    Sprint 11: Cache management.
    """
    from app.extraction.cache import get_extraction_cache
    
    cache = get_extraction_cache()
    cache.clear()
    
    return {"message": "Cache cleared successfully"}
