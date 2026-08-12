# Anchor Backend

FastAPI backend for grounded requirements extraction.

## Current Sprint: Sprint 2 - Grounded Extraction + Verification

**Core Principle**: LLM proposes citations → Code verifies → Humans decide

### Sprint 2 Features

1. **LLM Extraction**: Qwen3 extracts requirements with verbatim quotes
2. **Deterministic Grounding**: Application code verifies citations (NOT the LLM)
3. **Quarantine System**: Fabricated citations are automatically quarantined
4. **Fabrication Tracking**: Counter increments for failed verifications

### Key Architecture

```
Segments (Sprint 1)
    ↓
LLM Extraction (proposes requirements + citations)
    ↓
Grounding Verification (deterministic code checks)
    ├─ Pass → grounding = "grounded"
    └─ Fail → grounding = "quarantined", fabrication_attempts++
    ↓
Requirements Database
```

**Hard Rule**: No requirement reaches "confirmed" status without passing deterministic grounding verification.

### Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure database**:
   Copy `.env.example` to `.env` and update `DATABASE_URL`:
   ```bash
   cp .env.example .env
   ```

3. **Run Postgres** (example with Docker):
   ```bash
   docker run --name anchor-db -e POSTGRES_USER=anchor_user -e POSTGRES_PASSWORD=anchor_pass -e POSTGRES_DB=anchor_db -p 5432:5432 -d postgres:15
   ```

4. **Start the server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   API will be available at: http://localhost:8000

### Run Tests

```bash
pytest tests/ -v
```

### API Endpoints

**Sprint 1 - Ingest**

**POST /api/ingest**
- Upload a file for ingestion
- Returns: Source with Segments (stable IDs)

**GET /api/sources**
- List all sources

**GET /api/sources/{source_id}**
- Get source with segments

**Sprint 2 - Extraction**

**POST /api/extract/{source_id}**
- Extract requirements from source
- Returns: Requirements with evidence and grounding status
- Stats: grounded count, quarantined count, fabrication attempts

**GET /api/requirements?grounding=grounded|quarantined|ungrounded_candidate**
- List requirements, optionally filtered by grounding status

**GET /api/requirements/{requirement_id}**
- Get requirement with evidence

### Supported File Types

1. **Plain text (.txt)**: Split at paragraph level (double newlines)
2. **Markdown (.md)**: Split at headings and paragraphs
3. **Word documents (.docx)**: Split at paragraph level
4. **WebVTT (.vtt)**: Split at caption level, preserve timestamps
5. **Speaker-labeled transcripts**: Format `Speaker: text` or `Speaker (timestamp): text`

### Stable IDs

- **Source IDs**: Hash of `filename + content` → re-uploading same file produces same ID
- **Segment IDs**: Hash of `source_id + index + text + speaker + timestamp` → reproducible

### Character-Perfect Preservation

Original text is preserved exactly as uploaded (no normalization, trimming, or reflowing). This is critical for exact-match grounding in Sprint 2.

### Failure Handling

- Unparseable files are rejected with a named error message
- Files with no extractable text are flagged as "not_machine_readable"
- Failed uploads are tracked in the database with error details
- No silent failures or dropped files

## Architecture

```
app/
├── main.py              # FastAPI routes (Sprint 1 + 2)
├── config.py            # Settings (database, HF API key)
├── database.py          # SQLAlchemy setup
├── models.py            # Source, Segment, Requirement, Evidence
├── ingest/              # Sprint 1: File processing
│   ├── service.py       # Ingest orchestration
│   ├── parsers.py       # File-type parsers
│   ├── stable_id.py     # Hash-based ID generation
│   └── exceptions.py    # Custom exceptions
└── extraction/          # Sprint 2: LLM + grounding
    ├── service.py       # Extraction orchestration
    ├── llm_client.py    # Hugging Face API client
    ├── grounding.py     # DETERMINISTIC verification
    ├── schemas.py       # Pydantic models
    └── prompt.py        # LLM prompts
```

### Grounding Verification (Critical)

`extraction/grounding.py` - **This is application code, NOT the LLM**

Algorithm:
1. Look up segment by segment_id
2. Try exact string match (quote IN segment.text)
3. If not exact, try fuzzy match (≥95%, for whitespace/case only)
4. Check if quote in OTHER segments (source mismatch)
5. Return: verified (bool), method (exact_match|fuzzy_match|not_found|source_mismatch)

**Pass** → requirement.grounding = "grounded"  
**Fail** → requirement.grounding = "quarantined", fabrication_attempts++
