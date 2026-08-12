# Anchor - Grounded Requirements Extraction System

**Version 2.0 (In Progress)**  
*LLM proposes → Code verifies → Humans decide*

Anchor extracts requirements from stakeholder interviews and documents with **zero tolerance for hallucination**. Every requirement must be grounded in verbatim source quotes, verified by deterministic code.

## 🚀 Quick Start

```bash
# 1. Start backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 2. Start frontend (new terminal)
cd frontend
npm install
npm run dev

# 3. Access application
Frontend: http://localhost:3001
Backend API: http://localhost:8000
```

## 📊 V2 Progress

### ✅ Completed (MVP + V2 Sprints 8-9)
- **Sprint 1-5**: Complete MVP (~7,800 lines)
  - File ingest & segmentation
  - LLM extraction + deterministic grounding
  - Deduplication & coverage analysis
  - Four-lane review UI
  - Export (DOCX/MD) + eval harness
- **Sprint 8**: Multi-tenancy (workspace isolation)
- **Sprint 9**: Feedback loop (few-shot learning from accepted requirements)
- **File Formats**: TXT, MD, DOCX, VTT support (200MB limit)
- **Upload UI**: Complete drag-and-drop interface

### 🔄 In Progress
- Sprint 10: Contradiction detection at scale
- Sprint 11: Concurrency & caching
- Sprint 12: Multi-language support
- Sprint 13: Integrations

## 🎯 Core Features

### 1. Upload & Extract
- Upload transcripts or documents (TXT, MD, DOCX, VTT)
- Automatic segmentation
- LLM extraction with citations
- Deterministic grounding verification
- Few-shot learning from workspace feedback

### 2. Four-Lane Review Board
- **Confirmed**: Grounded requirements ready for use
- **Needs Review**: Quarantined or ungrounded candidates
- **Conflicts**: Detected contradictions
- **Possible Gaps**: Unconsumed substantive segments

### 3. Multi-Tenancy
- Workspace-isolated data
- Same content can exist in different workspaces
- Row-level scoping on all queries

### 4. Feedback Loop
- Accepted requirements become few-shot examples
- Workspace-specific prompt optimization
- Tracks acceptance rate improvements

## 🛡️ Core Guarantees

- **`ungrounded_shipped_rate = 0.0%`** - No hallucinations in production
- **Character-perfect preservation** - Original text never altered
- **Deterministic verification** - Code checks every citation
- **Human-in-the-loop** - No auto-resolution of conflicts
- **Workspace isolation** - Client data never mixes

## 📁 Project Structure

```
Anchor/
├── backend/              # Python/FastAPI backend
│   ├── app/
│   │   ├── extraction/   # LLM client + grounding
│   │   ├── ingest/       # File parsing
│   │   ├── feedback/     # Sprint 9: Few-shot learning
│   │   ├── audit/        # Action tracking
│   │   ├── dedup/        # Duplicate detection
│   │   ├── coverage/     # Gap analysis
│   │   ├── contradiction/# Conflict detection
│   │   └── export/       # DOCX/MD export
│   └── tests/            # Acceptance tests
├── frontend/             # React/TypeScript UI
│   └── src/
│       └── components/   # Upload, Review, Detail
└── docs/                 # Documentation
```

## 🔧 Tech Stack

- **Backend**: Python 3.12, FastAPI, PostgreSQL, SQLAlchemy
- **Frontend**: React 18, TypeScript, Tailwind CSS
- **LLM**: Groq Cloud (Qwen 3.6-27B)
- **Grounding**: rapidfuzz (deterministic fuzzy matching)

## 📖 Documentation

- [QUICKSTART.md](QUICKSTART.md) - 5-minute setup guide
- [ARCHITECTURE.md](backend/ARCHITECTURE.md) - System design
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Simple explanation
- [COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md) - V2 roadmap details

## 🧪 Testing

```bash
cd backend
pytest tests/                    # Run all tests
python -m app.feedback.scheduler # Update feedback examples
```

## 📝 License

MIT License - See [LICENSE](LICENSE)

## 🎯 V2 Roadmap

**Sprint 10**: Pre-filtering for contradiction detection  
**Sprint 11**: Request queuing + result caching  
**Sprint 12**: Multi-language transcripts  
**Sprint 13**: Meeting tool integrations  

---

**Status**: V2 Development - Sprints 8-9 Complete  
**Last Updated**: 2026-08-12 System

**Stop shipping hallucinated requirements.** Anchor extracts requirements from stakeholder interviews and verifies every single one against the source transcript - automatically.

---

## 🎯 What Does Anchor Do?

Anchor takes messy stakeholder interview transcripts and produces **verified, traceable requirements** that you can trust.

### The Problem It Solves

When extracting requirements from interviews:
- ❌ LLMs hallucinate "requirements" that were never mentioned
- ❌ Requirements lack evidence and traceability
- ❌ No way to verify what's real vs. what's fabricated
- ❌ Manual verification is time-consuming and error-prone

### The Anchor Solution

✅ **Extracts** requirements using LLMs (Groq/Qwen, Claude, or OpenAI)  
✅ **Grounds** every requirement with exact quotes from the transcript  
✅ **Verifies** using deterministic code (not LLM self-assessment)  
✅ **Quarantines** ungrounded requirements automatically  
✅ **Guarantees** zero ungrounded requirements ship to production  

---

## 🏗️ Architecture

```
┌─────────────────┐
│  Upload File    │  1. Ingest transcript (txt, docx)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Segment Text   │  2. Split into addressable chunks
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM Extracts   │  3. Propose requirements
│  Requirements   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Deterministic  │  4. Verify each with exact quotes
│  Grounding      │     (using rapidfuzz, NOT LLM)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Four-Lane UI   │  5. Review grounded requirements
│  Review Board   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Export         │  6. Export with full traceability
│  (DOCX/MD)      │
└─────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL** (or Docker)
- **LLM API Key**: Groq (recommended), OpenAI, or Anthropic

### Installation

1. **Clone and navigate:**
   ```bash
   cd Anchor
   ```

2. **Setup Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env and add your API key
   ```

3. **Setup Database:**
   ```bash
   # Using Docker (recommended)
   docker run --name anchor-db \
     -e POSTGRES_USER=anchor_user \
     -e POSTGRES_PASSWORD=anchor_pass \
     -e POSTGRES_DB=anchor_db \
     -p 5432:5432 -d postgres:15
   
   # OR install Postgres locally and create database manually
   ```

4. **Setup Frontend:**
   ```bash
   cd ../frontend
   npm install
   ```

5. **Start Services:**
   ```bash
   # Terminal 1 - Backend
   cd backend
   uvicorn app.main:app --reload
   
   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

6. **Open Browser:**
   ```
   http://localhost:3000
   ```

---

## 🎮 Usage

### 1. Upload Transcript

Upload a stakeholder interview transcript (`.txt` or `.docx`):

```bash
POST /api/ingest
```

**Result:** File is segmented into addressable chunks with stable IDs.

### 2. Extract Requirements

Trigger LLM extraction and grounding:

```bash
POST /api/extract/{source_id}
```

**What happens:**
1. LLM proposes requirements
2. System searches for exact/fuzzy matches in transcript
3. Requirements without valid evidence are quarantined
4. Only grounded requirements proceed

### 3. Review in UI

Open `http://localhost:3000` to see the **Four-Lane Review Board**:

- **Lane 1 (Confirmed):** ✅ Grounded requirements ready to ship
- **Lane 2 (Needs Review):** ⚠️ Requires human decision
- **Lane 3 (Conflicts):** ⚔️ Contradictory requirements
- **Lane 4 (Gaps):** 📋 Segments not covered by requirements

Click any requirement to see:
- Full requirement statement
- Verbatim quote from transcript
- Source segment with context
- Audit trail of all actions

### 4. Export

Export with full traceability:

```bash
GET /api/export/{source_id}/docx   # Microsoft Word
GET /api/export/{source_id}/markdown  # Markdown
```

**Includes:**
- All confirmed requirements
- Evidence section with exact quotes
- Source references
- Traceability matrix

---

## 🔧 Configuration

### Environment Variables (`.env`)

```bash
# Database
DATABASE_URL=postgresql://anchor_user:anchor_pass@localhost:5432/anchor_db

# LLM API Key (use one of these)
HUGGINGFACE_API_KEY=your_api_key_here  # For Groq, OpenAI, or Anthropic

# Environment
ENVIRONMENT=development
```

### Supported LLM Providers

Edit `backend/app/extraction/llm_client.py` to switch providers:

**Current: Groq (Fast & Free Tier)**
```python
self.base_url = "https://api.groq.com/openai/v1"
self.model = "qwen/qwen3.6-27b"
```

**Alternative: OpenAI**
```python
self.base_url = "https://api.openai.com/v1"
self.model = "gpt-4-turbo"
```

**Alternative: Anthropic Claude**
```python
self.base_url = "https://api.anthropic.com/v1"
self.model = "claude-3-5-sonnet-20241022"
```

---

## 📊 Key Features

### 1. Deterministic Grounding

**Problem:** LLMs can't reliably verify their own output.

**Solution:** Deterministic code using `rapidfuzz` library:
- Exact match detection
- Fuzzy matching for whitespace/casing variations
- Character-perfect text preservation
- No LLM in the verification loop

### 2. Zero Ungrounded Shipping

**Guarantee:** `ungrounded_shipped_rate = 0.0%`

The system has an **eval harness** that runs synthetic tests:
```bash
POST /api/eval/run
```

If ANY ungrounded requirement reaches "confirmed" status, the test fails.

### 3. Audit Trail

Every action is logged:
- Who accepted/rejected a requirement
- When it happened
- Why (reason field)
- What was the previous state

```bash
GET /api/requirements/{req_id}/audit
```

### 4. Four-Lane Review

Inspired by Kanban, requirements flow through lanes:
1. **Confirmed** → Ready to ship
2. **Needs Review** → Human decision needed
3. **Conflicts** → Contradictions detected
4. **Gaps** → Missing coverage

### 5. Coverage Analysis

Identifies segments not covered by any requirement:
- Filler detection (greetings, chitchat)
- Gap highlighting
- Coverage percentage

```bash
GET /api/coverage/{source_id}
```

---

## 🧪 Testing

Run acceptance tests for each sprint:

```bash
cd backend

# Sprint 1: Ingest
pytest tests/test_sprint1_acceptance.py -v

# Sprint 2: Extract & Ground
pytest tests/test_sprint2_acceptance.py -v

# Sprint 3: Dedup & Coverage
pytest tests/test_sprint3_acceptance.py -v

# Sprint 4: Contradictions
pytest tests/test_sprint4_acceptance.py -v

# Sprint 5: Export & Eval
pytest tests/test_sprint5_acceptance.py -v

# All tests
pytest tests/ -v
```

**Critical Test:**
```bash
pytest tests/test_sprint2_acceptance.py::test_zero_ungrounded_rate -v
```
This MUST pass. If it fails, ungrounded requirements are shipping.

---

## 📁 Project Structure

```
Anchor/
├── backend/                 # Python FastAPI server
│   ├── app/
│   │   ├── audit/          # Audit trail service
│   │   ├── contradiction/  # Conflict detection
│   │   ├── coverage/       # Gap analysis
│   │   ├── dedup/          # Duplicate detection
│   │   ├── eval/           # Eval harness
│   │   ├── export/         # DOCX/MD export
│   │   ├── extraction/     # LLM extraction + grounding
│   │   ├── ingest/         # File parsing
│   │   ├── config.py       # Configuration
│   │   ├── database.py     # SQLAlchemy setup
│   │   ├── main.py         # FastAPI routes
│   │   └── models.py       # Database models
│   ├── tests/              # Acceptance tests
│   ├── test_fixtures/      # Sample transcripts
│   ├── .env                # Environment config
│   ├── requirements.txt    # Python dependencies
│   └── pytest.ini          # Test configuration
│
├── frontend/               # React + TypeScript UI
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── RequirementCard.tsx
│   │   │   ├── RequirementDetail.tsx
│   │   │   └── ReviewBoard.tsx
│   │   ├── api.ts          # API client
│   │   ├── types.ts        # TypeScript types
│   │   ├── App.tsx         # Main app
│   │   └── main.tsx        # Entry point
│   ├── package.json        # NPM dependencies
│   └── vite.config.ts      # Vite config
│
└── README.md               # This file
```

---

## 🎯 Core Principles

### 1. LLM Proposes, Code Verifies, Humans Decide

- **LLM:** Extracts requirements from text (smart but unreliable)
- **Code:** Verifies grounding with deterministic matching (reliable but dumb)
- **Human:** Makes final accept/reject decisions (both smart and reliable)

### 2. Zero Trust in LLM Output

Never trust LLM responses without verification. Every requirement must have:
- Exact verbatim quote from source
- Character-perfect match (or verified fuzzy match)
- Source segment ID for traceability

### 3. Character-Perfect Text Preservation

Original text is never modified during segmentation:
- No normalization
- No whitespace cleanup
- No encoding changes

This ensures grounding checks can find exact matches.

### 4. Stable IDs

All entities have deterministic IDs based on content hash:
- `src_<hash>` - Source files
- `seg_<hash>` - Segments
- `req_<hash>` - Requirements
- `evd_<hash>` - Evidence

Same input = same ID (reproducible builds)

---

## 🔒 Security & Compliance

### Data Privacy

- All processing happens on your infrastructure
- No data sent to third parties (except LLM API)
- Database encryption at rest (Postgres feature)
- API authentication ready (add middleware)

### Audit Compliance

- Full audit trail of all actions
- Immutable evidence chain
- Export includes traceability matrix
- Human-in-the-loop for all "confirmed" requirements

---

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check Python version
python --version  # Need 3.10+

# Reinstall dependencies
pip install -r requirements.txt

# Check .env file exists
cat .env
```

### Database connection error

```bash
# Check Postgres running
docker ps | grep anchor-db

# Restart if needed
docker restart anchor-db

# Check connection string in .env
DATABASE_URL=postgresql://anchor_user:anchor_pass@127.0.0.1:5432/anchor_db
```

### LLM API errors

```bash
# Test API key
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"

# Check rate limits
# Groq free tier: 30 requests/minute
```

### Frontend can't connect

```bash
# Check backend is running
curl http://localhost:8000/

# Check proxy in vite.config.ts
# Should proxy /api to http://localhost:8000
```

---

## 📚 Learn More

### Key Files to Read

1. **`backend/app/extraction/grounding.py`** - How grounding verification works
2. **`backend/app/extraction/llm_client.py`** - LLM integration
3. **`backend/app/models.py`** - Database schema
4. **`frontend/src/components/ReviewBoard.tsx`** - UI implementation
5. **`tests/test_sprint2_acceptance.py`** - Critical zero-ungrounded test

### Documentation

- **Architecture:** See `backend/ARCHITECTURE.md`
- **API Docs:** Visit `http://localhost:8000/docs` when backend is running
- **Database Schema:** Inspect `backend/app/models.py`

---

## 🤝 Contributing

This is a proof-of-concept MVP. Areas for improvement:

1. **Authentication:** Add user login and permissions
2. **Multi-tenancy:** Support multiple projects/teams
3. **Real-time:** WebSocket updates for UI
4. **Advanced grounding:** Semantic similarity matching
5. **Bulk operations:** Process multiple files at once
6. **Export formats:** PDF, HTML, Confluence, Jira

---

## 🗺️ V2 Roadmap

### Post-MVP Sprints (Sequenced)

**Sprint 8: Multi-tenancy** - Add workspace_id/engagement_id, row-level scoping  
**Sprint 9: Feedback loop** - Learn from accept/reject decisions (prompt-level, not fine-tuning)  
**Sprint 10: Contradiction scale** - Pre-filter candidates before O(n²) comparison  
**Sprint 11: Concurrency** - Request queue, caching, abstract LLM interface  
**Sprint 12: Multi-language** - Local language input → English output (grounding still matches original)  
**Sprint 13: Integrations** - Pull from Zoom/Teams/etc. (build last)  

**Core rule never changes:** A requirement is NEVER "confirmed" without passing deterministic grounding.

See `COMPLETION_SUMMARY.md` for detailed V2 specs.

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🎉 Success Metrics

Your Anchor installation is working correctly when:

✅ Backend starts without errors  
✅ Frontend loads at http://localhost:3000  
✅ Sprint 1 tests pass (ingest)  
✅ Can upload a transcript  
✅ Requirements extract and show in UI  
✅ **`ungrounded_shipped_rate = 0.0%`** (most critical!)  
✅ Can export to DOCX/MD  

---

## 💡 Example Workflow

1. **Product Manager** uploads interview transcript
2. **Anchor** extracts 50 requirements in 30 seconds
3. **System** grounds 42, quarantines 8
4. **PM** reviews the 42 grounded requirements
5. **PM** accepts 40, rejects 2 (out of scope)
6. **Anchor** exports 40 confirmed requirements with evidence
7. **Dev Team** implements from trusted, traceable requirements

**Result:** Zero hallucinated requirements in production. ✅

---

**Built with:** Python • FastAPI • React • TypeScript • PostgreSQL • Groq/Qwen  
**Focus:** Zero ungrounded requirements shipped  
**Principle:** Code verifies. Humans decide. LLMs propose.

---

Made for teams who ship requirements they can trust. 🚀
