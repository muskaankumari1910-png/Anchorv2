import httpx
import json
from typing import Dict, Any, List
from app.config import settings
from app.extraction.schemas import ExtractionOutputSchema
from app.extraction.prompt import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt
from pydantic import ValidationError


class LLMExtractionError(Exception):
    """Base exception for LLM extraction errors"""
    pass


class LLMClient:
    """Client for Groq Cloud API"""
    
    def __init__(self, api_key: str = None):
        # Using Groq Cloud API with Qwen.
        # Prefer GROQ_API_KEY; fall back to the legacy HUGGINGFACE_API_KEY name.
        self.api_key = api_key or settings.groq_api_key or settings.huggingface_api_key
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = "qwen/qwen3.6-27b"  # Groq model name
    
    async def extract_requirements(self, segments: list, few_shot_examples: list = None) -> ExtractionOutputSchema:
        """
        Extract requirements from segments using LLM.
        
        Sprint 9: Now supports few-shot examples from feedback loop.
        
        Returns validated ExtractionOutputSchema.
        Raises LLMExtractionError on failure.
        """
        user_prompt = build_extraction_prompt(segments, few_shot_examples)
        
        # Try extraction with retry on JSON parse failure
        max_retries = 2
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response_text = await self._call_llm(user_prompt)
                
                # Try to extract JSON from response
                json_str = self._extract_json(response_text)
                
                # Parse and validate
                data = json.loads(json_str)
                validated = ExtractionOutputSchema(**data)
                
                return validated
            
            except (json.JSONDecodeError, ValidationError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Retry with more explicit instruction
                    user_prompt += "\n\nIMPORTANT: Output ONLY valid JSON, no markdown, no extra text."
                    continue
                else:
                    raise LLMExtractionError(f"Failed to get valid JSON after {max_retries} attempts: {e}")
            
            except Exception as e:
                raise LLMExtractionError(f"LLM call failed: {e}")
        
        raise LLMExtractionError(f"Extraction failed: {last_error}")
    
    async def detect_duplicates(self, requirements: List[Dict]) -> List[Dict]:
        """
        Detect near-duplicate requirements (Sprint 3).
        
        Returns list of duplicate pairs:
        [
            {
                "requirement_id_1": "req_...",
                "requirement_id_2": "req_...",
                "similarity_score": 0.9,
                "reasoning": "Both refer to MFA requirements"
            }
        ]
        """
        prompt = self._build_dedup_prompt(requirements)
        
        try:
            response_text = await self._call_llm(prompt)
            json_str = self._extract_json(response_text)
            data = json.loads(json_str)
            
            return data.get("duplicate_pairs", [])
        except Exception as e:
            raise LLMExtractionError(f"Duplicate detection failed: {e}")
    
    async def classify_filler(self, segments: List[Dict]) -> Dict[str, bool]:
        """
        Classify segments as filler/greeting vs substantive (Sprint 3).
        
        Returns dict: {segment_id: is_filler}
        """
        prompt = self._build_filler_prompt(segments)
        
        try:
            response_text = await self._call_llm(prompt)
            json_str = self._extract_json(response_text)
            data = json.loads(json_str)
            
            classifications = data.get("classifications", [])
            
            # Convert to dict
            result = {}
            for item in classifications:
                result[item["segment_id"]] = item["is_filler"]
            
            return result
        except Exception as e:
            raise LLMExtractionError(f"Filler classification failed: {e}")
    
    async def detect_contradictions(self, requirements: List[Dict]) -> List[Dict]:
        """
        Detect contradictions between requirements (Sprint 4).
        
        Returns list of contradiction pairs:
        [
            {
                "requirement_id_1": "req_...",
                "requirement_id_2": "req_...",
                "conflict_description": "Both sides with quotes"
            }
        ]
        """
        prompt = self._build_contradiction_prompt(requirements)
        
        try:
            response_text = await self._call_llm(prompt)
            json_str = self._extract_json(response_text)
            data = json.loads(json_str)
            
            return data.get("contradictions", [])
        except Exception as e:
            raise LLMExtractionError(f"Contradiction detection failed: {e}")
    
    def _build_dedup_prompt(self, requirements: List[Dict]) -> str:
        """Build prompt for duplicate detection"""
        prompt_parts = [
            "Analyze the following requirements and identify near-duplicates.",
            "Two requirements are duplicates if they express the same need, even with different wording.",
            "",
            "Requirements:"
        ]
        
        for req in requirements:
            prompt_parts.append(f"\n- ID: {req['id']}")
            prompt_parts.append(f"  Statement: {req['statement']}")
            prompt_parts.append(f"  Category: {req.get('category', 'N/A')}")
        
        prompt_parts.append("\n\nOutput JSON with duplicate pairs:")
        prompt_parts.append('''{
  "duplicate_pairs": [
    {
      "requirement_id_1": "req_...",
      "requirement_id_2": "req_...",
      "similarity_score": 0.95,
      "reasoning": "Both describe MFA requirements"
    }
  ]
}''')
        
        return "\n".join(prompt_parts)
    
    def _build_filler_prompt(self, segments: List[Dict]) -> str:
        """Build prompt for filler classification"""
        prompt_parts = [
            "Classify each segment as 'filler' (greetings, small talk, tangents) or 'substantive' (actual requirements/needs).",
            "",
            "Segments:"
        ]
        
        for seg in segments:
            prompt_parts.append(f"\n- ID: {seg['id']}")
            if seg.get('speaker'):
                prompt_parts.append(f"  Speaker: {seg['speaker']}")
            prompt_parts.append(f"  Text: {seg['text']}")
        
        prompt_parts.append("\n\nOutput JSON:")
        prompt_parts.append('''{
  "classifications": [
    {
      "segment_id": "seg_...",
      "is_filler": true,
      "reasoning": "Greeting/small talk"
    }
  ]
}''')
        
        return "\n".join(prompt_parts)
    
    def _build_contradiction_prompt(self, requirements: List[Dict]) -> str:
        """Build prompt for contradiction detection"""
        prompt_parts = [
            "Analyze requirements within the same category for contradictions.",
            "A contradiction exists when two requirements specify mutually exclusive or conflicting behaviors.",
            "",
            "Requirements with evidence:"
        ]
        
        for req in requirements:
            prompt_parts.append(f"\n- ID: {req['id']}")
            prompt_parts.append(f"  Statement: {req['statement']}")
            prompt_parts.append(f"  Evidence:")
            for evd in req.get('evidence', []):
                prompt_parts.append(f"    • {evd['quote']}")
        
        prompt_parts.append("\n\nOutput JSON with contradictions:")
        prompt_parts.append('''{
  "contradictions": [
    {
      "requirement_id_1": "req_...",
      "requirement_id_2": "req_...",
      "conflict_description": "Req1 says X but Req2 says Y. Quotes: '...' vs '...'"
    }
  ]
}''')
        
        return "\n".join(prompt_parts)
    
    async def _call_llm(self, user_prompt: str) -> str:
        """Call Groq Cloud API (OpenAI-compatible)"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": EXTRACTION_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": 0.1,  # Low temperature for consistency
            "max_tokens": 4000
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # OpenAI format: {"choices": [{"message": {"content": "..."}}]}
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                raise LLMExtractionError(f"Unexpected response format: {result}")
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from response that might contain markdown or extra text"""
        # Try to find JSON object in text
        text = text.strip()
        
        # Remove markdown code blocks if present
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()
        
        # Find JSON object boundaries
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        
        if brace_start != -1 and brace_end != -1:
            return text[brace_start:brace_end + 1]
        
        return text
