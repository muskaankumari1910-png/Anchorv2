# Anchor Backend Architecture

## Sprint 1: Ingest & Segment (Deterministic Pipeline)

### Data Flow

```
Upload File
    ↓
Detect File Type (.txt, .docx, .md, .vtt, transcript)
    ↓
Parse & Segment (character-perfect preservation)
    ↓
Generate Stable IDs (hash-based, reproducible)
    ↓
Persist to Database
    ↓
Return Source + Segments
```

### Failure Handling

```
Upload File
    ↓
Parse Attempt
    ↓
[Error?]
    ├─ UnparseableFileError → Create Source with status="rejected"
    ├─ NotMachineReadableError → Create Source with status="not_machine_readable"
    └─ Success → Create Source with status="processed" + Segments
```

### Database Schema

```sql
-- Sprint 1 tables

CREATE TABLE sources (
    id VARCHAR PRIMARY KEY,              -- src_{hash16}
    filename VARCHAR NOT NULL,
    type VARCHAR NOT NULL,               -- txt, docx, md, vtt, transcript
    status VARCHAR NOT NULL,             -- processed, rejected, not_machine_readable
    uploaded_at TIMESTAMP DEFAULT NOW(),
    error_message TEXT                   -- Populated on failure
);

CREATE TABLE segments (
    id VARCHAR PRIMARY KEY,              -- seg_{hash16}
    source_id VARCHAR REFERENCES sources(id) ON DELETE CASCADE,
    index INTEGER NOT NULL,              -- Sequential position in source
    speaker VARCHAR,                     -- For transcripts only
    timestamp VARCHAR,                   -- For transcripts only (HH:MM:SS)
    text TEXT NOT NULL                   -- Character-perfect original text
);

CREATE INDEX ix_segment_source_id ON segments(source_id);
CREATE INDEX ix_segment_source_index ON segments(source_id, index);
```

### Module Organization

```
app/
├── main.py                 # FastAPI application
│   └── Routes:
│       ├── POST /api/ingest         → ingest_file()
│       ├── GET  /api/sources        → list all
│       └── GET  /api/sources/{id}   → get one
│
├── models.py              # SQLAlchemy models
│   ├── Source (id, filename, type, status, uploaded_at, error_message)
│   └── Segment (id, source_id, index, speaker, timestamp, text)
│
├── database.py            # SQLAlchemy setup
│   ├── engine (connection)
│   ├── SessionLocal (session factory)
│   └── get_db() (dependency)
│
├── config.py              # Pydantic settings
│   └── Settings (database_url, huggingface_api_key, environment)
│
└── ingest/
    ├── service.py         # Orchestration
    │   ├── ingest_file()         → Main entry point
    │   └── handle_ingest_error() → Failure tracking
    │
    ├── parsers.py         # File-type-specific parsing
    │   ├── parse_txt()       → Paragraph segmentation
    │   ├── parse_md()        → Heading/paragraph segmentation
    │   ├── parse_docx()      → Paragraph segmentation (python-docx)
    │   ├── parse_vtt()       → Caption segmentation (webvtt-py)
    │   └── parse_transcript() → Utterance segmentation (regex)
    │
    ├── stable_id.py       # Hash-based ID generation
    │   ├── generate_source_id()  → sha256(filename + content)
    │   └── generate_segment_id() → sha256(source_id + index + text + ...)
    │
    └── exceptions.py      # Custom exceptions
        ├── UnparseableFileError      → File cannot be parsed
        └── NotMachineReadableError   → No extractable text
```

### Stable ID Algorithm

```python
# Source ID (reproducible on re-upload)
sha256(filename + file_bytes) → "src_{first_16_hex}"

# Segment ID (reproducible on re-segmentation)
sha256(source_id + index + text + speaker + timestamp) → "seg_{first_16_hex}"
```

**Property**: Same input → same IDs, guaranteed.

### Character-Perfect Preservation

**Requirement**: Original text must be stored exactly as provided, with no:
- Normalization (case changes, unicode normalization)
- Trimming (beyond paragraph-level whitespace)
- Reflowing (line break changes)

**Rationale**: Sprint 2's grounding verification uses exact string matching. If we normalize text during ingest, we won't be able to verify LLM citations match the original source.

**Example**:
```
Original: 'User said: "Password MUST be 12+ chars."'
Stored:   'User said: "Password MUST be 12+ chars."'  ✓ EXACT
NOT:      'User said: Password must be 12+ chars.'    ✗ Modified
```

### Parser Segmentation Rules

| File Type | Segmentation Strategy | Metadata Extracted |
|-----------|----------------------|-------------------|
| `.txt` | Double newlines (paragraphs) | None |
| `.md` | Headings + double newlines | None |
| `.docx` | Paragraph elements | None |
| `.vtt` | Caption entries | `timestamp` (start time) |
| Transcript | Speaker turns | `speaker`, `timestamp` (if present) |

**Transcript format examples**:
```
# Format 1: Simple
Speaker1: First statement.
Speaker2: Second statement.

# Format 2: With timestamps
Speaker1 (00:01:23): First statement.
Speaker2 (00:02:45): Second statement.
```

### Error Handling Strategy

**Philosophy**: Never silently drop or ignore failures.

1. **Unparseable files** (corrupted, wrong format):
   - Raise `UnparseableFileError(filename, reason)`
   - Create Source with `status="rejected"`, `error_message=reason`
   - Return 400 HTTP error with file name in response

2. **No extractable text** (empty, whitespace-only, scanned PDF):
   - Raise `NotMachineReadableError(filename)`
   - Create Source with `status="not_machine_readable"`
   - Return 400 HTTP error with file name in response

3. **All failures**:
   - Generate stable source ID (same failed file = same error record)
   - Persist error to database for tracking
   - Never return success with zero segments

### API Response Format

```typescript
// Success response
{
  "id": "src_a1b2c3d4e5f6g7h8",
  "filename": "interview.txt",
  "type": "transcript",
  "status": "processed",
  "uploaded_at": "2026-08-12T10:30:00Z",
  "error_message": null,
  "segments": [
    {
      "id": "seg_x1y2z3a4b5c6d7e8",
      "source_id": "src_a1b2c3d4e5f6g7h8",
      "index": 0,
      "speaker": "Interviewer",
      "timestamp": "00:00:05",
      "text": "Can you describe the main requirement?"
    },
    // ... more segments
  ]
}

// Error response (400)
{
  "detail": {
    "error": "NotMachineReadableError",
    "message": "File 'empty.txt' contains no extractable text (not machine-readable)",
    "source_id": "src_a1b2c3d4e5f6g7h8",
    "status": "not_machine_readable"
  }
}
```

## Dependencies

**Core**:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation, settings
- `sqlalchemy` - ORM
- `psycopg2-binary` - Postgres driver
- `alembic` - Database migrations (future)

**Parsing**:
- `python-docx` - DOCX parsing
- `webvtt-py` - WebVTT parsing

**Testing**:
- `pytest` - Test framework
- `httpx` - Async HTTP client for testing

**Future (Sprint 2+)**:
- `rapidfuzz` - Fuzzy string matching for grounding verification
- `httpx` - HTTP client for Hugging Face API

## Testing Strategy

### Unit Tests (`test_ingest.py`)
- Individual parser functions
- Stable ID generation
- Character preservation
- Error handling

### Acceptance Tests (`test_sprint1_acceptance.py`)
- Definition of Done verification
- End-to-end workflows
- All file types supported
- Re-upload stability

### Integration Tests (Future)
- Full API endpoint testing with FastAPI TestClient
- Database transaction rollback
- Concurrent upload handling

## Next: Sprint 2

Sprint 2 will add:
1. `requirements` table (statement, category, type, grounding, evidence)
2. `evidence` table (requirement_id, source_id, segment_id, verbatim_quote)
3. Extraction service (LLM call to Qwen3-32B)
4. **Grounding verification service (deterministic code, NOT LLM)**
5. Quarantine system for unverified citations
6. Fabrication attempt counter

**Key principle for Sprint 2**: The LLM proposes citations, but application code (exact string matching with rapidfuzz fallback) verifies them. No requirement reaches "confirmed" status without passing the grounding check.
