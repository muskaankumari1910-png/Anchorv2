import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Source, Segment, SourceType, SourceStatus
from app.extraction.grounding import GroundingVerifier


@pytest.fixture
def db_session():
    """Create a fresh in-memory database for each test"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_source_with_segments(db_session):
    """Create a source with segments for testing"""
    source = Source(
        id="src_test123",
        filename="test.txt",
        type=SourceType.TXT,
        status=SourceStatus.PROCESSED
    )
    db_session.add(source)
    
    segment1 = Segment(
        id="seg_abc123",
        source_id="src_test123",
        index=0,
        text='The system must support multi-factor authentication using SMS codes.'
    )
    
    segment2 = Segment(
        id="seg_def456",
        source_id="src_test123",
        index=1,
        text='Users should be able to choose their preferred MFA method.'
    )
    
    segment3 = Segment(
        id="seg_ghi789",
        source_id="src_test123",
        index=2,
        text='Password must be at least 12 characters long.'
    )
    
    db_session.add(segment1)
    db_session.add(segment2)
    db_session.add(segment3)
    db_session.commit()
    
    return source, [segment1, segment2, segment3]


class TestGroundingVerifier:
    """Test the deterministic grounding verification"""
    
    def test_exact_match_verification(self, db_session, sample_source_with_segments):
        """Test that exact quote matches are verified"""
        source, segments = sample_source_with_segments
        
        # Exact quote from segment 1
        quote = "multi-factor authentication using SMS codes"
        segment_id = "seg_abc123"
        
        verified, method, message = GroundingVerifier.verify_quote(
            quote, segment_id, db_session
        )
        
        assert verified is True
        assert method == "exact_match"
        assert "exactly" in message.lower()
    
    def test_fuzzy_match_whitespace_variations(self, db_session, sample_source_with_segments):
        """Test that whitespace/casing variations are handled with fuzzy match"""
        source, segments = sample_source_with_segments
        
        # Same content but different whitespace/casing
        quote = "Multi-Factor  Authentication   Using SMS Codes"
        segment_id = "seg_abc123"
        
        verified, method, message = GroundingVerifier.verify_quote(
            quote, segment_id, db_session
        )
        
        assert verified is True
        assert method == "fuzzy_match"
    
    def test_fabricated_quote_not_verified(self, db_session, sample_source_with_segments):
        """CRITICAL TEST: Fabricated quote must NOT be verified"""
        source, segments = sample_source_with_segments
        
        # Quote that doesn't exist anywhere
        fabricated_quote = "The system must support biometric authentication"
        segment_id = "seg_abc123"
        
        verified, method, message = GroundingVerifier.verify_quote(
            fabricated_quote, segment_id, db_session
        )
        
        assert verified is False
        assert method == "not_found"
        assert "not found" in message.lower()
    
    def test_source_mismatch_detection(self, db_session, sample_source_with_segments):
        """Test that quote in wrong segment is caught (source mismatch)"""
        source, segments = sample_source_with_segments
        
        # Quote from segment 3, but cited as segment 1
        quote = "Password must be at least 12 characters"
        wrong_segment_id = "seg_abc123"  # Quote is actually in seg_ghi789
        
        verified, method, message = GroundingVerifier.verify_quote(
            quote, wrong_segment_id, db_session
        )
        
        assert verified is False
        assert method == "source_mismatch"
        assert "seg_ghi789" in message
    
    def test_partial_quote_verification(self, db_session, sample_source_with_segments):
        """Test that partial quotes are verified"""
        source, segments = sample_source_with_segments
        
        # Partial quote from segment 1
        quote = "multi-factor authentication"
        segment_id = "seg_abc123"
        
        verified, method, message = GroundingVerifier.verify_quote(
            quote, segment_id, db_session
        )
        
        assert verified is True
        assert method in ["exact_match", "fuzzy_match"]
    
    def test_verify_requirement_with_valid_evidence(self, db_session, sample_source_with_segments):
        """Test requirement verification with valid evidence"""
        source, segments = sample_source_with_segments
        
        requirement_data = {
            "statement": "System must support MFA",
            "evidence": [
                {
                    "source_id": "src_test123",
                    "segment_id": "seg_abc123",
                    "verbatim_quote": "multi-factor authentication using SMS codes"
                }
            ]
        }
        
        all_verified, fabrication_count, evidence_results = GroundingVerifier.verify_requirement_evidence(
            requirement_data, db_session
        )
        
        assert all_verified is True
        assert fabrication_count == 0
        assert len(evidence_results) == 1
        assert evidence_results[0]["verified"] is True
    
    def test_verify_requirement_with_fabricated_evidence(self, db_session, sample_source_with_segments):
        """CRITICAL TEST: Requirement with fabricated evidence must fail verification"""
        source, segments = sample_source_with_segments
        
        requirement_data = {
            "statement": "System must support biometric auth",
            "evidence": [
                {
                    "source_id": "src_test123",
                    "segment_id": "seg_abc123",
                    "verbatim_quote": "biometric authentication with fingerprint scanner"
                }
            ]
        }
        
        all_verified, fabrication_count, evidence_results = GroundingVerifier.verify_requirement_evidence(
            requirement_data, db_session
        )
        
        assert all_verified is False, "Fabricated evidence MUST fail verification"
        assert fabrication_count == 1, "Fabrication count must be incremented"
        assert len(evidence_results) == 1
        assert evidence_results[0]["verified"] is False
        assert evidence_results[0]["method"] == "not_found"
    
    def test_verify_requirement_with_mixed_evidence(self, db_session, sample_source_with_segments):
        """Test requirement with some valid and some fabricated evidence"""
        source, segments = sample_source_with_segments
        
        requirement_data = {
            "statement": "System auth requirements",
            "evidence": [
                {
                    "source_id": "src_test123",
                    "segment_id": "seg_abc123",
                    "verbatim_quote": "multi-factor authentication"  # Valid
                },
                {
                    "source_id": "src_test123",
                    "segment_id": "seg_def456",
                    "verbatim_quote": "facial recognition support"  # Fabricated
                }
            ]
        }
        
        all_verified, fabrication_count, evidence_results = GroundingVerifier.verify_requirement_evidence(
            requirement_data, db_session
        )
        
        assert all_verified is False, "Must fail if ANY evidence is fabricated"
        assert fabrication_count == 1
        assert evidence_results[0]["verified"] is True
        assert evidence_results[1]["verified"] is False
    
    def test_verify_requirement_with_no_evidence(self, db_session, sample_source_with_segments):
        """Test that requirement with no evidence fails verification"""
        source, segments = sample_source_with_segments
        
        requirement_data = {
            "statement": "Some requirement",
            "evidence": []
        }
        
        all_verified, fabrication_count, evidence_results = GroundingVerifier.verify_requirement_evidence(
            requirement_data, db_session
        )
        
        assert all_verified is False
        assert fabrication_count == 1  # No evidence counts as fabrication
        assert len(evidence_results) == 0
    
    def test_nonexistent_segment_id(self, db_session, sample_source_with_segments):
        """Test that citing a nonexistent segment ID fails"""
        source, segments = sample_source_with_segments
        
        quote = "some quote"
        fake_segment_id = "seg_doesnotexist"
        
        verified, method, message = GroundingVerifier.verify_quote(
            quote, fake_segment_id, db_session
        )
        
        assert verified is False
        assert method == "not_found"
        assert "does not exist" in message.lower()
