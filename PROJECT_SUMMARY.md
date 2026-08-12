# Anchor - Project Summary

## What is Anchor?

Anchor is a **grounded requirements extraction system** that prevents LLM hallucinations from reaching production.

### The Problem
When using LLMs to extract requirements from interviews:
- LLMs make up requirements that were never mentioned
- No way to verify which requirements are real
- Manual checking is slow and unreliable

### The Solution
Anchor automatically:
1. Extracts requirements using LLMs
2. Verifies each one with exact quotes
3. Quarantines anything without evidence
4. Guarantees 0% ungrounded requirements ship

---

## How It Works (Simple Explanation)

```
Interview Transcript
        ↓
   [Upload File]
        ↓
   Split into chunks (segments)
        ↓
   LLM extracts requirements
        ↓
   For each requirement:
     → Find exact quote in transcript
     → If found ✅ = Grounded
     → If not found ❌ = Quarantined
        ↓
   Review in 4-lane board
        ↓
   Export with evidence
```

---

## Tech Stack

**Backend:**
- Python 3.12
- FastAPI (web framework)
- PostgreSQL (database)
- Groq/Qwen (LLM)
- rapidfuzz (grounding verification)

**Frontend:**
- React + TypeScript
- Tailwind CSS
- Vite (build tool)

**Infrastructure:**
- Docker (Postgres)
- uvicorn (ASGI server)

---

## Project Structure

```
Anchor/
├── backend/           # Python API server
│   ├── app/          # Application code
│   │   ├── ingest/   # File upload & parsing
│   │   ├── extraction/ # LLM + grounding
│   │   ├── audit/    # Action tracking
│   │   └── export/   # DOCX/MD export
│   └── tests/        # Acceptance tests
│
├── frontend/         # React UI
│   └── src/
│       └── components/ # Review board UI
│
├── README.md         # Full documentation
├── QUICKSTART.md     # 5-minute setup guide
└── PROJECT_SUMMARY.md # This file
```

---

## Key Features

### 1. Deterministic Grounding ✅
Uses code (not LLM) to verify requirements against source text.

### 2. Four-Lane Review 📊
- **Lane 1:** Confirmed (grounded, ready to ship)
- **Lane 2:** Needs Review (human decision needed)
- **Lane 3:** Conflicts (contradictions found)
- **Lane 4:** Gaps (uncovered transcript sections)

### 3. Audit Trail 📝
Tracks every action: who, what, when, why.

### 4. Export with Evidence 📄
DOCX/Markdown files include requirements + exact quotes + traceability.

### 5. Zero-Ungrounded Guarantee 🎯
Built-in test ensures no hallucinations reach production.

---

## Success Metrics

✅ **100% grounding rate** - All shipped requirements have evidence  
✅ **0% ungrounded rate** - Zero hallucinations in production  
✅ **Full traceability** - Every requirement links to source  
✅ **Audit compliance** - Complete action history  

---

## Use Cases

### Product Management
- Extract requirements from customer interviews
- Verify every requirement has evidence
- Export for stakeholder review

### Business Analysis
- Process discovery workshops
- Requirements gathering sessions
- Stakeholder alignment meetings

### Compliance & Audit
- Maintain evidence chain
- Track requirement changes
- Generate audit reports

---

## What Makes It Different?

Most requirement tools:
- Trust LLM output blindly
- No verification mechanism
- Requirements lack evidence
- Can't prove traceability

Anchor:
- ✅ Verifies every requirement with code
- ✅ Deterministic grounding check
- ✅ Evidence = exact verbatim quotes
- ✅ Full audit trail
- ✅ Zero ungrounded guarantee

---

## Core Principle

**"LLM Proposes, Code Verifies, Humans Decide"**

- **LLM**: Smart but unreliable - proposes requirements
- **Code**: Reliable but dumb - verifies with exact matches
- **Human**: Both smart and reliable - makes final decisions

Never let unverified LLM output reach production.

---

## Development Approach

Built in 5 sprints (MVP methodology):

1. **Sprint 1:** Ingest & Segment - File processing
2. **Sprint 2:** Extract & Ground - LLM + verification
3. **Sprint 3:** Dedup & Coverage - Quality analysis
4. **Sprint 4:** Review & Contradictions - Human workflow
5. **Sprint 5:** Export & Eval - Production ready

Each sprint has acceptance tests that must pass.

---

## Getting Started

**Quick:** See `QUICKSTART.md` (5 minutes)  
**Detailed:** See `README.md` (full documentation)  
**Architecture:** See `backend/ARCHITECTURE.md` (technical details)

---

## Example Results

From a 5-minute interview transcript:

**Input:**
- 8 transcript segments
- ~500 words

**Output:**
- 7 requirements extracted
- 7 grounded (100%)
- 0 quarantined
- Each has exact quote evidence

**Time:** ~30 seconds total processing

---

## Critical Success Metric

```python
# This MUST be 0.0
ungrounded_shipped_rate_pct = 0.0
```

If this test fails, ungrounded requirements are shipping. The system is designed to make this mathematically impossible.

---

## Future Enhancements

- Multi-user authentication
- Real-time collaboration
- Semantic similarity matching
- Bulk file processing
- Integration with Jira/Confluence
- PDF export with signatures

---

## License

MIT License - Free to use, modify, and distribute.

---

## Support

- **Issues:** Check `README.md` troubleshooting section
- **Architecture:** See `backend/ARCHITECTURE.md`
- **API Docs:** http://localhost:8000/docs
- **Tests:** Run `pytest tests/ -v` in backend folder

---

**Summary:** Anchor stops LLM hallucinations from becoming production requirements. Every requirement is verified with exact source quotes. Zero trust in LLM output.

Built for teams who ship requirements they can trust. 🚀
