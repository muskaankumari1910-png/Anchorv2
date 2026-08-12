import json

EXTRACTION_SYSTEM_PROMPT = """You are a requirements extraction assistant. Your job is to extract requirements from stakeholder interviews and documents.

CRITICAL RULES:
1. Every requirement you output MUST include a quote copied exactly, character-for-character, from the provided text, along with the segment ID it came from.
2. If you cannot find supporting text for a requirement, do NOT output it as a requirement. Instead, list it under ungrounded_candidates with your reasoning.
3. Never paraphrase a quote. Copy it EXACTLY as it appears in the source.
4. Never invent a source. Only cite segments that were actually provided to you.
5. Match the capitalization, punctuation, and wording exactly from the source text.

Your output must be valid JSON matching this schema:
{
  "requirements": [
    {
      "statement": "Brief requirement statement",
      "category": "authentication|reporting|etc",
      "type": "functional|non-functional|constraint|business-rule",
      "evidence": [
        {
          "source_id": "src_...",
          "segment_id": "seg_...",
          "verbatim_quote": "exact text from segment"
        }
      ],
      "confidence": "high|medium|low"
    }
  ],
  "ungrounded_candidates": [
    {
      "statement": "Potential requirement without clear evidence",
      "reasoning": "Why this lacks supporting text"
    }
  ]
}

Think carefully. If you're unsure whether text supports a requirement, put it in ungrounded_candidates."""


def build_extraction_prompt(segments: list, few_shot_examples: list = None) -> str:
    """
    Build the user prompt with segments and optional few-shot examples.
    
    Sprint 9: Includes workspace-specific few-shot examples from feedback loop.
    """
    prompt_parts = []
    
    # Add few-shot examples if available
    if few_shot_examples:
        prompt_parts.append("Here are some examples of correct requirement extraction:\n")
        
        for i, example in enumerate(few_shot_examples, 1):
            prompt_parts.append(f"--- EXAMPLE {i} ---")
            prompt_parts.append("Input segments:")
            
            for seg in example["segments"]:
                prompt_parts.append(f"Segment {seg['index']}: {seg['text']}")
            
            prompt_parts.append("\nCorrect output:")
            prompt_parts.append(json.dumps({"requirements": [example["expected_output"]]}, indent=2))
            prompt_parts.append("")
        
        prompt_parts.append("Now extract requirements from the following NEW segments:\n")
    else:
        prompt_parts.append("Extract requirements from the following segments:\n")
    
    # Add current segments to extract from
    for seg in segments:
        prompt_parts.append(f"\n--- Segment {seg['index']} ---")
        prompt_parts.append(f"Source ID: {seg['source_id']}")
        prompt_parts.append(f"Segment ID: {seg['id']}")
        if seg.get('speaker'):
            prompt_parts.append(f"Speaker: {seg['speaker']}")
        if seg.get('timestamp'):
            prompt_parts.append(f"Timestamp: {seg['timestamp']}")
        prompt_parts.append(f"Text: {seg['text']}")
        prompt_parts.append("")
    
    prompt_parts.append("\nExtract requirements with evidence citations. Output valid JSON only.")
    
    return "\n".join(prompt_parts)
