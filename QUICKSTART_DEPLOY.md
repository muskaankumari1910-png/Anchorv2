# 🚀 Anchor - Quick Deployment Guide

Deploy Anchor in **5 minutes** using Docker Compose.

## Prerequisites

- **Docker Desktop** installed and running
- **4GB RAM** available
- **5GB disk space**

Don't have Docker? [Install Docker Desktop](https://www.docker.com/products/docker-desktop)

---

## 3-Step Deployment

### **Step 1: Get the Code**

```bash
cd Anchor
```

### **Step 2: Run Deployment Script**

**Windows:**
```cmd
deploy.bat
```

**Mac/Linux:**
```bash
chmod +x deploy.sh
./deploy.sh
```

### **Step 3: Open Browser**

```
http://localhost
```

**That's it!** 🎉

---

## What Just Happened?

The deployment script:
1. ✅ Checked Docker is installed
2. ✅ Built 3 Docker images (database, backend, frontend)
3. ✅ Started 4 containers
4. ✅ Configured networking
5. ✅ Ran database migrations
6. ✅ Made everything available at http://localhost

---

## Quick Test

### 1. Check Services

```bash
docker compose ps
```

Expected output:
```
NAME                  STATUS
anchor-postgres       Up
anchor-backend        Up
anchor-frontend       Up
anchor-nginx          Up
```

### 2. Test API

```bash
curl http://localhost/api/
```

Should return:
```json
{"message":"Anchor API - Sprint 5: Export + Eval + Non-AI Fallback"}
```

### 3. Upload a Test File

1. Open http://localhost
2. Click "Upload & Extract"
3. Drop a text file
4. Click "Extract Requirements"
5. See results in Review Board

---

## Common Commands

```bash
# View logs (all services)
docker compose logs -f

# View logs (specific service)
docker compose logs -f backend

# Stop all services
docker compose down

# Restart a service
docker compose restart backend

# Check resource usage
docker stats

# Update after code changes
docker compose up -d --build

# Fresh start (removes data)
docker compose down -v
docker compose up -d
```

---

## Troubleshooting

### "Port already in use"

```bash
# Stop services using ports 80, 8000, or 5432
docker compose down

# On Windows, check what's using port 80:
netstat -ano | findstr :80

# On Mac/Linux:
lsof -i :80
```

### "Backend not responding"

```bash
# Check backend logs
docker compose logs backend

# Common issue: Database not ready yet
# Wait 30 seconds, then check again
```

### "Docker not found"

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Start Docker Desktop
3. Wait for "Docker Desktop is running" status
4. Run deployment script again

### "Out of memory"

```bash
# Check Docker Desktop settings
# Increase memory to at least 4GB

# Windows/Mac: Docker Desktop → Settings → Resources → Memory
# Increase to 4GB or more
```

---

## Environment Configuration

The `.env` file contains your configuration:

```bash
# Your Groq API Key (already configured)
GROQ_API_KEY=your_groq_api_key_here

# Environment
ENVIRONMENT=production
```

**Don't share your `.env` file** - it contains your API key!

---

## Accessing Services

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost | Main application UI |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Interactive API docs |
| **Database** | localhost:5432 | PostgreSQL (internal) |
| **Health Check** | http://localhost/health | Service health |

---

## Production Deployment

For production deployment (AWS, DigitalOcean, etc.), see:
- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment guide
- [README.md](README.md) - System documentation

Quick production checklist:
- [ ] Change database password in `docker-compose.yml`
- [ ] Set up HTTPS with SSL certificate
- [ ] Configure backups
- [ ] Set up monitoring
- [ ] Enable rate limiting
- [ ] Add authentication

---

## Stopping the Application

```bash
# Stop services (keeps data)
docker compose down

# Stop and remove all data
docker compose down -v
```

---

## Next Steps

1. **Upload a file**: Try the upload feature
2. **Extract requirements**: See the LLM in action
3. **Review board**: Explore the four-lane UI
4. **Export**: Download requirements as DOCX or Markdown
5. **Read docs**: Check [README.md](README.md) for details

---

## Getting Help

**Check logs first:**
```bash
docker compose logs -f
```

**Common issues:**
- Port conflicts → Stop other services
- Memory errors → Increase Docker memory
- Database errors → Check logs with `docker compose logs postgres`
- API errors → Check logs with `docker compose logs backend`

**Still stuck?**
Review [DEPLOYMENT.md](DEPLOYMENT.md) for detailed troubleshooting.

---

## Success Checklist

Your deployment is successful when:

- ✅ All containers show "Up" status
- ✅ Frontend loads at http://localhost
- ✅ API responds at http://localhost/api/
- ✅ Can upload a file
- ✅ Requirements extract successfully
- ✅ No errors in logs

Run this to verify everything:
```bash
docker compose ps && curl http://localhost/api/ && echo "\n✅ All systems operational!"
```

---

## Architecture

```
┌─────────────┐
│   Browser   │ → http://localhost
└──────┬──────┘
       │
┌──────▼──────┐
│    Nginx    │ (Port 80)
│   Proxy     │
└──┬───────┬──┘
   │       │
   │       └──────────┐
   │                  │
┌──▼────────┐  ┌─────▼──────┐
│  Frontend │  │  Backend   │
│  (React)  │  │  (FastAPI) │
│  Port 80  │  │  Port 8000 │
└───────────┘  └─────┬──────┘
                     │
              ┌──────▼────────┐
              │   PostgreSQL  │
              │   Port 5432   │
              └───────────────┘
```

---

**Questions?** Check [README.md](README.md) or [DEPLOYMENT.md](DEPLOYMENT.md)

**Ready to deploy?** Run `deploy.bat` (Windows) or `./deploy.sh` (Mac/Linux)

---

Made with ❤️ for teams who ship requirements they can trust.
