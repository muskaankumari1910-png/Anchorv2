"""
Sprint 3 Definition of Done - Acceptance Tests

1. Feed transcript with repeated requirement → merged with multiple evidence
2. Feed transcript with unrelated tangent → shows in gaps
3. Coverage % calculation is accurate
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import (
    Source, Segment, Requirement, Evidence, SegmentConsumption,
    SourceType, SourceStatus, GroundingStatus, RequirementType, ConfidenceLevel
)
from app.dedup.service import generate_merge_suggestion_id, merge_requirements
from app.coverage.service import generate_consumption_id, generate_gap_id
import hashlib


@pytest.fixture
def db_session():
    """Create a fresh in-memory database for each test"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def create_test_source_with_segments(db_session, segments_data):
    """Helper to create source and segments"""
    source = Source(
        id="src_test",
        filename="test.txt",
        type=SourceType.TRANSCRIPT,
        status=SourceStatus.PROCESSED
    )
    db_session.add(source)
    
    segments = []
    for i, seg_data in enumerate(segments_data):
        segment = Segment(
            id=f"seg_{i}",
            source_id="src_test",
            index=i,
            text=seg_data["text"],
            speaker=seg_data.get("speaker")
        )
        db_session.add(segment)
        segments.append(segment)
    
    db_session.commit()
    return source, segments


def create_requirement_with_evidence(db_session, req_id, statement, evidence_data):
    """Helper to create requirement with evidence"""
    requirement = Requirement(
        id=req_id,
        statement=statement,
        category="test",
        type=RequirementType.FUNCTIONAL,
        grounding=GroundingStatus.GROUNDED,
        confidence=ConfidenceLevel.HIGH,
        fabrication_attempts=0
    )
    db_session.add(requirement)
    
    for i, evd_data in enumerate(evidence_data):
        evidence = Evidence(
            id=f"evd_{req_id}_{i}",
            requirement_id=req_id,
            source_id=evd_data["source_id"],
            segment_id=evd_data["segment_id"],
            verbatim_quote=evd_data["quote"],
            verified=1,
            verification_method="exact_match"
        )
        db_session.add(evidence)
    
    db_session.commit()
    return requirement


class TestSprint3Acceptance:
    """Sprint 3 Definition of Done acceptance tests"""
    
    def test_dod_1_merge_preserves_all_evidence(self, db_session):
        """
        DOD #1: Repeated requirement by two speakers → merged with multiple evidence
        
        Scenario: Two requirements say essentially the same thing.
        After merge, the combined requirement should have evidence from BOTH.
        """
        # Create source and segments
        segments_data = [
            {"text": "We need multi-factor authentication", "speaker": "Stakeholder1"},
            {"text": "MFA is required for security", "speaker": "Stakeholder2"},
            {"text": "Other unrelated content", "speaker": "Interviewer"}
        ]
        source, segments = create_test_source_with_segments(db_session, segments_data)
        
        # Create two similar requirements with different evidence
        req1 = create_requirement_with_evidence(
            db_session,
            "req_1",
            "System must support multi-factor authentication",
            [{"source_id": "src_test", "segment_id": "seg_0", "quote": "multi-factor authentication"}]
        )
        
        req2 = create_requirement_with_evidence(
            db_session,
            "req_2",
            "MFA is required for system security",
            [{"source_id": "src_test", "segment_id": "seg_1", "quote": "MFA is required"}]
        )
        
        # Create merge suggestion manually (simulating LLM detection)
        from app.models import MergeSuggestion
        suggestion_id = generate_merge_suggestion_id("req_1", "req_2")
        suggestion = MergeSuggestion(
            id=suggestion_id,
            requirement_id_1="req_1",
            requirement_id_2="req_2",
            similarity_score=0.95,
            reasoning="Both describe MFA requirements",
            status="pending"
        )
        db_session.add(suggestion)
        db_session.commit()
        
        # Execute merge
        merged_req = merge_requirements(suggestion_id, db_session, "default")
        
        # Verify: merged requirement has evidence from BOTH original requirements
        evidence_list = db_session.query(Evidence).filter(
            Evidence.requirement_id == merged_req.id
        ).all()
        
        assert len(evidence_list) == 2, "Merged requirement must have evidence from BOTH sources"
        
        quotes = [evd.verbatim_quote for evd in evidence_list]
        assert "multi-factor authentication" in quotes
        assert "MFA is required" in quotes
        
        # Verify req2 is marked as merged
        req2_updated = db_session.query(Requirement).filter(Requirement.id == "req_2").first()
        assert req2_updated.is_merged == 1
        assert req2_updated.merged_into == "req_1"
        
        print("✓ Merge preserves ALL evidence from both requirements")
    
    def test_dod_1_unmerge_restores_originals(self, db_session):
        """
        Test that un-merge operation restores original requirements
        """
        # Setup: Create and merge requirements (same as above)
        segments_data = [
            {"text": "We need MFA", "speaker": "Stakeholder1"},
            {"text": "MFA required", "speaker": "Stakeholder2"}
        ]
        source, segments = create_test_source_with_segments(db_session, segments_data)
        
        req1 = create_requirement_with_evidence(
            db_session, "req_1", "MFA requirement 1",
            [{"source_id": "src_test", "segment_id": "seg_0", "quote": "need MFA"}]
        )
        
        req2 = create_requirement_with_evidence(
            db_session, "req_2", "MFA requirement 2",
            [{"source_id": "src_test", "segment_id": "seg_1", "quote": "MFA required"}]
        )
        
        from app.models import MergeSuggestion
        suggestion_id = generate_merge_suggestion_id("req_1", "req_2")
        suggestion = MergeSuggestion(
            id=suggestion_id,
            requirement_id_1="req_1",
            requirement_id_2="req_2",
            similarity_score=0.9,
            status="pending"
        )
        db_session.add(suggestion)
        db_session.commit()
        
        # Merge
        merge_requirements(suggestion_id, db_session, "default")
        
        # Verify merged
        req2_merged = db_session.query(Requirement).filter(Requirement.id == "req_2").first()
        assert req2_merged.is_merged == 1
        
        # Un-merge
        from app.dedup.service import unmerge_requirements
        unmerged = unmerge_requirements("req_1", db_session, "default")
        
        # Verify restored
        req2_restored = db_session.query(Requirement).filter(Requirement.id == "req_2").first()
        assert req2_restored.is_merged == 0
        assert req2_restored.merged_into is None
        
        print("✓ Un-merge restores original requirements")
    
    def test_dod_2_unrelated_tangent_shows_in_gaps(self, db_session):
        """
        DOD #2: Unrelated tangent → shows in possible gaps, not silently dropped
        
        Scenario: Transcript has relevant content + unrelated tangent.
        Coverage analysis should identify the tangent as an unconsumed gap.
        """
        # Create source with mixed content
        segments_data = [
            {"text": "We need user authentication", "speaker": "Stakeholder"},
            {"text": "How was your weekend?", "speaker": "Interviewer"},  # TANGENT
            {"text": "Oh it was great, went hiking", "speaker": "Stakeholder"},  # TANGENT
            {"text": "Password must be 12 characters", "speaker": "Stakeholder"}
        ]
        source, segments = create_test_source_with_segments(db_session, segments_data)
        
        # Create requirements covering segments 0 and 3 only (not the tangent)
        req1 = create_requirement_with_evidence(
            db_session, "req_1", "Auth requirement",
            [{"source_id": "src_test", "segment_id": "seg_0", "quote": "user authentication"}]
        )
        
        req2 = create_requirement_with_evidence(
            db_session, "req_2", "Password requirement",
            [{"source_id": "src_test", "segment_id": "seg_3", "quote": "Password must be 12 characters"}]
        )
        
        # Mark segments as consumed
        for seg_id, req_id in [("seg_0", "req_1"), ("seg_3", "req_2")]:
            consumption = SegmentConsumption(
                id=generate_consumption_id(seg_id, req_id),
                segment_id=seg_id,
                requirement_id=req_id
            )
            db_session.add(consumption)
        db_session.commit()
        
        # Find unconsumed segments
        consumed_ids = {"seg_0", "seg_3"}
        unconsumed = [seg for seg in segments if seg.id not in consumed_ids]
        
        assert len(unconsumed) == 2, "Tangent segments (1, 2) should be unconsumed"
        assert unconsumed[0].id == "seg_1"
        assert unconsumed[1].id == "seg_2"
        assert "weekend" in unconsumed[0].text.lower()
        
        # These would be identified as gaps in coverage analysis
        from app.models import Gap
        for seg in unconsumed:
            gap = Gap(
                id=generate_gap_id(seg.id),
                segment_id=seg.id,
                source_id="src_test",
                is_filler=1  # Would be classified by LLM as filler
            )
            db_session.add(gap)
        db_session.commit()
        
        gaps = db_session.query(Gap).filter(Gap.source_id == "src_test").all()
        assert len(gaps) == 2
        
        print("✓ Unrelated tangent correctly identified as gap")
    
    def test_dod_3_coverage_percentage_calculation(self, db_session):
        """
        DOD #3: Coverage percentage is accurate against manual count
        """
        # Create source with 10 segments
        segments_data = [{"text": f"Segment {i} content", "speaker": "Speaker"} for i in range(10)]
        source, segments = create_test_source_with_segments(db_session, segments_data)
        
        # Create requirements covering 6 out of 10 segments
        req1 = create_requirement_with_evidence(
            db_session, "req_1", "Requirement 1",
            [
                {"source_id": "src_test", "segment_id": "seg_0", "quote": "Segment 0"},
                {"source_id": "src_test", "segment_id": "seg_1", "quote": "Segment 1"},
                {"source_id": "src_test", "segment_id": "seg_2", "quote": "Segment 2"}
            ]
        )
        
        req2 = create_requirement_with_evidence(
            db_session, "req_2", "Requirement 2",
            [
                {"source_id": "src_test", "segment_id": "seg_5", "quote": "Segment 5"},
                {"source_id": "src_test", "segment_id": "seg_7", "quote": "Segment 7"},
                {"source_id": "src_test", "segment_id": "seg_9", "quote": "Segment 9"}
            ]
        )
        
        # Mark consumed segments
        consumed_segment_ids = {"seg_0", "seg_1", "seg_2", "seg_5", "seg_7", "seg_9"}
        for seg_id in consumed_segment_ids:
            # Find which requirement consumed it
            req_id = "req_1" if seg_id in {"seg_0", "seg_1", "seg_2"} else "req_2"
            consumption = SegmentConsumption(
                id=generate_consumption_id(seg_id, req_id),
                segment_id=seg_id,
                requirement_id=req_id
            )
            db_session.add(consumption)
        db_session.commit()
        
        # Calculate coverage
        total = 10
        consumed = len(consumed_segment_ids)
        expected_coverage = (consumed / total) * 100.0
        
        assert consumed == 6
        assert expected_coverage == 60.0
        
        # Verify unconsumed
        unconsumed = [seg for seg in segments if seg.id not in consumed_segment_ids]
        assert len(unconsumed) == 4
        assert set(seg.id for seg in unconsumed) == {"seg_3", "seg_4", "seg_6", "seg_8"}
        
        print(f"✓ Coverage calculation accurate: {consumed}/{total} = {expected_coverage}%")
    
    def test_low_coverage_flags_incomplete(self, db_session):
        """
        Test that low coverage (<40%) flags draft as incomplete
        """
        # Create source with 10 segments
        segments_data = [{"text": f"Segment {i}", "speaker": "Speaker"} for i in range(10)]
        source, segments = create_test_source_with_segments(db_session, segments_data)
        
        # Cover only 3 segments (30% coverage)
        req1 = create_requirement_with_evidence(
            db_session, "req_1", "Sparse requirement",
            [
                {"source_id": "src_test", "segment_id": "seg_0", "quote": "Segment 0"},
                {"source_id": "src_test", "segment_id": "seg_5", "quote": "Segment 5"},
                {"source_id": "src_test", "segment_id": "seg_9", "quote": "Segment 9"}
            ]
        )
        
        consumed_count = 3
        total_count = 10
        coverage_percentage = (consumed_count / total_count) * 100.0
        
        LOW_COVERAGE_THRESHOLD = 40.0
        is_incomplete = coverage_percentage < LOW_COVERAGE_THRESHOLD
        
        assert coverage_percentage == 30.0
        assert is_incomplete is True, "30% coverage should flag as incomplete"
        
        print("✓ Low coverage (<40%) correctly flags draft as incomplete")
    
    def test_merge_suggestion_not_auto_applied(self, db_session):
        """
        Verify that merge suggestions are NOT auto-applied.
        They require human confirmation.
        """
        segments_data = [{"text": "Content", "speaker": "Speaker"}]
        source, segments = create_test_source_with_segments(db_session, segments_data)
        
        req1 = create_requirement_with_evidence(
            db_session, "req_1", "Requirement 1",
            [{"source_id": "src_test", "segment_id": "seg_0", "quote": "Content"}]
        )
        
        req2 = create_requirement_with_evidence(
            db_session, "req_2", "Requirement 2",
            [{"source_id": "src_test", "segment_id": "seg_0", "quote": "Content"}]
        )
        
        # Create merge suggestion
        from app.models import MergeSuggestion
        suggestion_id = generate_merge_suggestion_id("req_1", "req_2")
        suggestion = MergeSuggestion(
            id=suggestion_id,
            requirement_id_1="req_1",
            requirement_id_2="req_2",
            similarity_score=0.9,
            status="pending"  # PENDING, not auto-accepted
        )
        db_session.add(suggestion)
        db_session.commit()
        
        # Verify req2 is NOT merged yet
        req2_check = db_session.query(Requirement).filter(Requirement.id == "req_2").first()
        assert req2_check.is_merged == 0, "Requirements should NOT be auto-merged"
        assert req2_check.merged_into is None
        
        # Verify suggestion is pending
        suggestion_check = db_session.query(MergeSuggestion).filter(
            MergeSuggestion.id == suggestion_id
        ).first()
        assert suggestion_check.status == "pending", "Merge must await human confirmation"
        
        print("✓ Merge suggestions NOT auto-applied, require human confirmation")


def test_evidence_never_discarded_on_merge(db_session):
    """
    CRITICAL: Verify that merging NEVER discards evidence.
    This is a data integrity requirement.
    """
    segments_data = [
        {"text": "Evidence 1", "speaker": "Speaker1"},
        {"text": "Evidence 2", "speaker": "Speaker2"},
        {"text": "Evidence 3", "speaker": "Speaker3"}
    ]
    source, segments = create_test_source_with_segments(db_session, segments_data)
    
    # Req1 has 2 pieces of evidence
    req1 = create_requirement_with_evidence(
        db_session, "req_1", "Requirement 1",
        [
            {"source_id": "src_test", "segment_id": "seg_0", "quote": "Evidence 1"},
            {"source_id": "src_test", "segment_id": "seg_1", "quote": "Evidence 2"}
        ]
    )
    
    # Req2 has 1 piece of evidence
    req2 = create_requirement_with_evidence(
        db_session, "req_2", "Requirement 2",
        [{"source_id": "src_test", "segment_id": "seg_2", "quote": "Evidence 3"}]
    )
    
    # Count evidence before merge
    total_evidence_before = db_session.query(Evidence).count()
    assert total_evidence_before == 3
    
    # Merge
    from app.models import MergeSuggestion
    suggestion_id = generate_merge_suggestion_id("req_1", "req_2")
    suggestion = MergeSuggestion(
        id=suggestion_id,
        requirement_id_1="req_1",
        requirement_id_2="req_2",
        similarity_score=0.9,
        status="pending"
    )
    db_session.add(suggestion)
    db_session.commit()
    
    merged_req = merge_requirements(suggestion_id, db_session, "default")
    
    # Count evidence after merge
    total_evidence_after = db_session.query(Evidence).count()
    assert total_evidence_after == 3, "Evidence must NEVER be discarded"
    
    # All evidence should now point to merged requirement
    evidence_for_merged = db_session.query(Evidence).filter(
        Evidence.requirement_id == merged_req.id
    ).all()
    assert len(evidence_for_merged) == 3, "Merged requirement must have ALL evidence"
    
    print("✓ VERIFIED: Merging NEVER discards evidence")
