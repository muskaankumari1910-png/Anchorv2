# 🚀 START HERE - Anchor Deployment

## What is Anchor?

**Anchor** extracts requirements from stakeholder interviews with **zero tolerance for hallucination**. Every requirement is grounded in verbatim source quotes, verified by deterministic code.

- ✅ Upload transcripts (TXT, MD, DOCX, VTT)
- ✅ LLM extracts requirements with citations
- ✅ Code verifies every citation (no hallucinations)
- ✅ Review in four-lane board
- ✅ Export with full traceability

**Core Guarantee**: `ungrounded_shipped_rate = 0.0%`

---

## ⚡ Deploy in 5 Minutes

### Windows (Double-click)

1. Open Command Prompt
2. Run:
   ```cmd
   cd c:\Users\kumar\Downloads\Anchor
   deploy.bat
   ```
3. Open: http://localhost

### Mac/Linux (Terminal)

```bash
cd ~/Downloads/Anchor
chmod +x deploy.sh
./deploy.sh
```

Then open: http://localhost

---

## What Gets Deployed?

Running `deploy.bat` starts 4 Docker containers:

1. **PostgreSQL** - Database (port 5432)
2. **Backend API** - FastAPI (port 8000)
3. **Frontend** - React app (port 80)
4. **Nginx** - Reverse proxy (port 80)

**Everything runs locally** - no cloud setup required!

---

## First Steps After Deployment

### 1. Verify It's Running

```bash
docker compose ps
```

All 4 services should show "Up" status.

### 2. Open the Application

Browser: http://localhost

### 3. Upload Your First File

1. Click "Upload & Extract"
2. Drag and drop a transcript (TXT, DOCX, VTT, or MD)
3. Click "Extract Requirements"
4. Wait 30 seconds
5. See results in Review Board

### 4. Review Requirements

Four lanes:
- **Confirmed** - Grounded requirements (ready to use)
- **Needs Review** - Quarantined (LLM proposed but couldn't verify)
- **Conflicts** - Contradictions detected
- **Gaps** - Unconsumed segments

### 5. Export

Click any requirement → "Export" → Choose DOCX or Markdown

---

## Architecture

```
Browser (http://localhost)
    ↓
Nginx (Port 80) - Routes traffic
    ↓
    ├─→ Frontend (React) - UI
    └─→ Backend (FastAPI) - API
           ↓
        PostgreSQL - Data
```

---

## Common Commands

```bash
# View logs
docker compose logs -f

# Stop services
docker compose down

# Restart
docker compose restart

# Fresh start (removes data)
docker compose down -v
docker compose up -d

# Check resource usage
docker stats
```

---

## Configuration

All config in `.env` file:

```bash
GROQ_API_KEY=your_groq_api_key_here
ENVIRONMENT=production
```

**Action required:** open `.env` and replace `your_groq_api_key_here` with a real Groq API key from https://console.groq.com (free tier works).

---

## Troubleshooting

### Services won't start

```bash
# Check logs
docker compose logs backend

# Common fixes:
docker compose down
docker compose up -d --build
```

### Port already in use

```bash
# Windows
netstat -ano | findstr :80

# Mac/Linux
lsof -i :80

# Solution: Change port in docker-compose.yml
```

### Out of memory

Docker Desktop → Settings → Resources → Increase memory to 4GB

---

## File Structure

```
Anchor/
├── docker-compose.yml    # Orchestrates all services
├── .env                  # Configuration (API keys)
├── deploy.bat           # Windows deployment script
├── deploy.sh            # Mac/Linux deployment script
├── backend/             # Python/FastAPI backend
│   ├── Dockerfile       # Backend container config
│   ├── app/             # Application code
│   └── requirements.txt # Python dependencies
├── frontend/            # React frontend
│   ├── Dockerfile       # Frontend container config
│   ├── src/             # React components
│   └── package.json     # Node dependencies
└── nginx.conf           # Reverse proxy config
```

---

## Documentation

| File | Purpose |
|------|---------|
| **START_HERE.md** | You are here - Quick start |
| **DEPLOY_NOW.md** | All deployment options |
| **QUICKSTART_DEPLOY.md** | 5-minute local setup |
| **DEPLOYMENT.md** | Full deployment guide |
| **README.md** | System documentation |
| **ARCHITECTURE.md** | Technical details |

---

## Success Checklist

- ✅ Docker installed
- ✅ Services running (`docker compose ps`)
- ✅ Frontend loads (http://localhost)
- ✅ Backend responds (http://localhost:8000)
- ✅ Can upload file
- ✅ Requirements extract
- ✅ Can export results

**All done?** You're deployed! 🎉

---

## Next Steps

### Immediate
1. ✅ Run `deploy.bat`
2. ✅ Test with sample file
3. ✅ Explore Review Board
4. ✅ Try export feature

### Soon
- [ ] Set up automated backups
- [ ] Configure monitoring
- [ ] Add authentication
- [ ] Deploy to cloud (Railway, Render, or DigitalOcean)

### Production
- [ ] Change database password
- [ ] Enable HTTPS
- [ ] Set up CI/CD
- [ ] Configure auto-scaling

---

## Cloud Deployment (Optional)

**Easiest**: Railway.app
1. Sign up: https://railway.app
2. Upload Anchor folder
3. Deploy with one click
4. Get live URL

**Details**: See [DEPLOY_NOW.md](DEPLOY_NOW.md)

---

## Technical Stack

- **Backend**: Python 3.12, FastAPI, PostgreSQL
- **Frontend**: React 18, TypeScript, Vite, Tailwind
- **LLM**: Groq Cloud (Qwen 3.6-27B)
- **Grounding**: rapidfuzz (deterministic)
- **Deployment**: Docker Compose

---

## Key Features

### 1. Upload & Segment
- Supports TXT, MD, DOCX, VTT formats
- 200MB file size limit
- Automatic segmentation
- Stable IDs (reproducible)

### 2. LLM Extraction
- Groq Cloud API (fast, free tier)
- Extracts requirements with citations
- Few-shot learning from accepted requirements
- Workspace-isolated prompts

### 3. Deterministic Grounding
- Code verifies every citation
- Exact match or fuzzy match (95% threshold)
- No LLM self-assessment
- Character-perfect text preservation

### 4. Multi-Tenancy
- Workspace isolation
- Same content in different workspaces
- Row-level security

### 5. Review UI
- Four-lane board
- Drag-and-drop interface
- Audit trail for all actions
- Accept/Edit/Reject workflow

### 6. Export
- DOCX with evidence
- Markdown with traceability
- Full source references

---

## Core Principles

1. **LLM proposes** - AI suggests requirements
2. **Code verifies** - Deterministic grounding check
3. **Humans decide** - Final accept/reject

**Result**: Zero hallucinated requirements in production

---

## Performance

**Typical extraction:**
- 50 requirements: ~30 seconds
- 100 requirements: ~60 seconds
- 200 requirements: ~120 seconds

**System capacity:**
- Concurrent users: 5-10
- Database: ~1GB per 1000 sources
- LLM calls: Cached (24h TTL)

---

## Support

**Logs**: `docker compose logs -f`  
**Docs**: See documentation files above  
**Health**: http://localhost/health  

---

## You're Ready! 🚀

**Run this now:**

```cmd
cd c:\Users\kumar\Downloads\Anchor
deploy.bat
```

Then open: **http://localhost**

---

**Questions?** Check [DEPLOYMENT.md](DEPLOYMENT.md) or [README.md](README.md)

**Deploy to cloud?** See [DEPLOY_NOW.md](DEPLOY_NOW.md)

---

Made for teams who ship requirements they can trust. ✅
