# Anchor - 5 Minute Quickstart

Get Anchor running in 5 minutes.

---

## Step 1: Prerequisites (2 min)

Check you have these installed:

```bash
python --version   # Need 3.10+
node --version     # Need 18+
docker --version   # Optional but recommended
```

Get an LLM API key (pick one):
- **Groq** (recommended): https://console.groq.com/keys - Free tier, very fast
- **OpenAI**: https://platform.openai.com/api-keys - Paid but reliable
- **Anthropic**: https://console.anthropic.com/ - Claude, very capable

---

## Step 2: Install Dependencies (2 min)

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

---

## Step 3: Configure (1 min)

```bash
cd backend
cp .env.example .env
```

Edit `.env` and add your API key:
```
HUGGINGFACE_API_KEY=your_api_key_here
```

(Yes, it says "HUGGINGFACE" but works with Groq/OpenAI/Anthropic - we'll rename it later!)

---

## Step 4: Start Database (1 min)

```bash
docker run --name anchor-db \
  -e POSTGRES_USER=anchor_user \
  -e POSTGRES_PASSWORD=anchor_pass \
  -e POSTGRES_DB=anchor_db \
  -p 5432:5432 -d postgres:15
```

Wait 10 seconds for Postgres to initialize.

---

## Step 5: Start Services (1 min)

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn app.main:app --reload
```

Wait for: `Application startup complete.`

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Wait for: `Local: http://localhost:3000/`

---

## Step 6: Test It! (2 min)

Open browser to **http://localhost:3000**

You should see the four-lane review board (empty for now).

### Upload a sample transcript:

**Option A - Via UI:**
1. Open http://localhost:3000
2. Upload `backend/test_fixtures/sample_transcript.txt`
3. Click "Extract Requirements"
4. Watch requirements appear in Lane 1!

**Option B - Via API:**
```bash
cd backend

# Upload
curl -X POST http://localhost:8000/api/ingest \
  -F "file=@test_fixtures/sample_transcript.txt"

# Copy the source_id from response, then:
curl -X POST http://localhost:8000/api/extract/{source_id}
```

Refresh browser - you should see 7 grounded requirements! ✅

---

## ✅ Success!

If you see requirements in the UI with evidence and quotes, **you're done!**

### Next Steps:

1. Click on a requirement to see its evidence
2. Try accepting/rejecting requirements
3. Export to DOCX: `GET http://localhost:8000/api/export/{source_id}/docx`
4. Upload your own interview transcripts!

---

## 🐛 Quick Troubleshooting

### Backend won't start
- Check Python 3.10+: `python --version`
- Reinstall: `pip install -r requirements.txt`
- Check `.env` exists in `backend/` folder

### Database error
- Check Docker: `docker ps | grep anchor-db`
- Restart: `docker restart anchor-db`
- Wait 10 seconds and try again

### Frontend blank
- Check backend running on port 8000
- Check browser console for errors
- Refresh page

### API key error
- Check `.env` has your actual API key
- Restart backend after changing `.env`
- Test key: `curl https://api.groq.com/openai/v1/models -H "Authorization: Bearer YOUR_KEY"`

---

## 📖 Learn More

- **Full Documentation:** See `README.md`
- **Architecture:** See `backend/ARCHITECTURE.md`
- **API Docs:** http://localhost:8000/docs (when backend running)

---

**That's it!** You now have a working requirements extraction system that verifies every requirement against the source. 🚀
