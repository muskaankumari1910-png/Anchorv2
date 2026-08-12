from rapidfuzz import fuzz
from typing import Tuple, Literal
from sqlalchemy.orm import Session
from app.models import Segment


class GroundingVerifier:
    """
    Deterministic grounding verification using exact string matching.
    
    CRITICAL: This is application code, NOT the LLM.
    The LLM proposes citations, this code verifies them.
    """
    
    # Fuzzy match threshold (only for whitespace/casing differences, not semantics)
    FUZZY_THRESHOLD = 95  # Very high - we want near-identical matches only
    
    @staticmethod
    def verify_quote(
        quote: str,
        segment_id: str,
        db: Session
    ) -> Tuple[bool, Literal["exact_match", "fuzzy_match", "not_found", "source_mismatch"], str]:
        """
        Verify that a quote actually appears in the referenced segment.
        
        Returns:
            (verified, method, message)
            - verified: True if quote found, False otherwise
            - method: How it was found (exact_match, fuzzy_match, not_found, source_mismatch)
            - message: Human-readable explanation
        
        Algorithm:
            1. Look up segment by segment_id
            2. Try exact string match (quote IN segment.text)
            3. If not exact, try fuzzy match (>= 95% similar, for whitespace/case only)
            4. Check if quote exists in OTHER segments (source mismatch)
            5. If none of above, return not_found
        """
        # Look up the segment
        segment = db.query(Segment).filter(Segment.id == segment_id).first()
        
        if not segment:
            return False, "not_found", f"Segment {segment_id} does not exist"
        
        segment_text = segment.text
        
        # Step 1: Exact match (preferred)
        if quote in segment_text:
            return True, "exact_match", f"Quote found exactly in segment {segment_id}"
        
        # Step 2: Fuzzy match (for whitespace/casing differences only)
        # Normalize both strings for comparison
        quote_normalized = " ".join(quote.split())
        segment_normalized = " ".join(segment_text.split())
        
        # Check if normalized quote appears in normalized segment
        if quote_normalized.lower() in segment_normalized.lower():
            # Calculate similarity to ensure it's close enough
            similarity = fuzz.ratio(quote_normalized.lower(), 
                                   segment_normalized.lower())
            
            if similarity >= GroundingVerifier.FUZZY_THRESHOLD:
                return True, "fuzzy_match", f"Quote found with fuzzy match (similarity: {similarity}%) in segment {segment_id}"
        
        # Also try partial ratio for substring matching
        partial_similarity = fuzz.partial_ratio(quote_normalized.lower(),
                                                segment_normalized.lower())
        
        if partial_similarity >= GroundingVerifier.FUZZY_THRESHOLD:
            return True, "fuzzy_match", f"Quote found with partial match (similarity: {partial_similarity}%) in segment {segment_id}"
        
        # Step 3: Check if quote exists in OTHER segments (source mismatch)
        # This is a fabrication of a different kind - right text, wrong location
        other_segments = db.query(Segment).filter(
            Segment.source_id == segment.source_id,
            Segment.id != segment_id
        ).all()
        
        for other_seg in other_segments:
            if quote in other_seg.text or quote_normalized.lower() in " ".join(other_seg.text.split()).lower():
                return False, "source_mismatch", f"Quote found in segment {other_seg.id}, not {segment_id}"
        
        # Step 4: Not found anywhere
        return False, "not_found", f"Quote not found in segment {segment_id} or nearby segments"
    
    @staticmethod
    def verify_requirement_evidence(
        requirement_data: dict,
        db: Session
    ) -> Tuple[bool, int, list]:
        """
        Verify all evidence citations for a requirement.
        
        Returns:
            (all_verified, fabrication_count, evidence_results)
            - all_verified: True if ALL evidence passed verification
            - fabrication_count: Number of failed verifications (fabrications)
            - evidence_results: List of dicts with verification details for each evidence
        
        This is the GATEKEEPER function. If this returns all_verified=False,
        the requirement MUST be quarantined.
        """
        evidence_list = requirement_data.get("evidence", [])
        
        if not evidence_list:
            return False, 1, []  # No evidence = fabrication
        
        evidence_results = []
        fabrication_count = 0
        all_verified = True
        
        for evd in evidence_list:
            quote = evd.get("verbatim_quote", "")
            segment_id = evd.get("segment_id", "")
            source_id = evd.get("source_id", "")
            
            verified, method, message = GroundingVerifier.verify_quote(
                quote, segment_id, db
            )
            
            evidence_results.append({
                "source_id": source_id,
                "segment_id": segment_id,
                "verbatim_quote": quote,
                "verified": verified,
                "method": method,
                "message": message
            })
            
            if not verified:
                fabrication_count += 1
                all_verified = False
        
        return all_verified, fabrication_count, evidence_results
