from pydantic import BaseModel, Field
from typing import List, Literal


class EvidenceSchema(BaseModel):
    """Evidence citation from LLM"""
    source_id: str = Field(description="The source ID")
    segment_id: str = Field(description="The segment ID where the quote appears")
    verbatim_quote: str = Field(description="The exact quote, character-for-character, from the segment")


class RequirementSchema(BaseModel):
    """A single extracted requirement with evidence"""
    statement: str = Field(description="The requirement statement")
    category: str = Field(description="Category like 'authentication', 'reporting', etc.")
    type: Literal["functional", "non-functional", "constraint", "business-rule"]
    evidence: List[EvidenceSchema] = Field(description="Evidence citations supporting this requirement")
    confidence: Literal["high", "medium", "low"]


class UngroundedCandidateSchema(BaseModel):
    """A potential requirement that lacks grounding"""
    statement: str
    reasoning: str = Field(description="Why this lacks supporting text")


class ExtractionOutputSchema(BaseModel):
    """Complete LLM extraction output"""
    requirements: List[RequirementSchema]
    ungrounded_candidates: List[UngroundedCandidateSchema]
