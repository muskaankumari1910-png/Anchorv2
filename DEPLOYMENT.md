# Anchor Deployment Guide

## 🚀 Easiest Way: Docker Compose (Recommended)

This is the simplest deployment method. Everything runs in containers with one command.

### Prerequisites

- **Docker** (20.10+) and **Docker Compose** (v2.0+)
- **Groq API Key** (already configured in `.env`)
- **2GB RAM** minimum, **4GB** recommended
- **5GB disk space**

### Quick Start (3 Steps)

```bash
# 1. Navigate to project directory
cd Anchor

# 2. Start all services
docker-compose up -d

# 3. Access the application
# Frontend: http://localhost
# Backend API: http://localhost/api
# Direct Backend: http://localhost:8000
```

That's it! 🎉

### What Gets Deployed

The `docker-compose up` command starts 4 services:

1. **PostgreSQL Database** (port 5432)
   - Persistent data storage
   - Automatic health checks
   - Data volume: `postgres_data`

2. **Backend API** (port 8000)
   - FastAPI server
   - Python 3.12
   - Auto-runs database migrations

3. **Frontend** (port 3001)
   - React app built with Vite
   - Nginx serving static files
   - Optimized production build

4. **Nginx Reverse Proxy** (port 80)
   - Routes traffic to frontend/backend
   - 200MB file upload limit
   - Rate limiting (30 API requests/minute)
   - Security headers

### Verify Deployment

```bash
# Check all containers are running
docker-compose ps

# Expected output:
# NAME                  STATUS    PORTS
# anchor-postgres       Up        5432/tcp
# anchor-backend        Up        8000/tcp
# anchor-frontend       Up        80/tcp
# anchor-nginx          Up        0.0.0.0:80->80/tcp

# Check logs
docker-compose logs -f

# Test API health
curl http://localhost/api/
# Should return: {"message":"Anchor API - Sprint 5: Export + Eval + Non-AI Fallback"}

# Test frontend
curl http://localhost/health
# Should return: healthy
```

### Usage

1. **Open browser**: http://localhost
2. **Upload a file**: Click "Upload & Extract" → drag/drop a transcript
3. **Extract requirements**: Click "Extract Requirements"
4. **Review results**: See four-lane review board
5. **Export**: Click "Export" button (DOCX or Markdown)

### Managing the Deployment

```bash
# Stop all services
docker-compose down

# Stop and remove all data (fresh start)
docker-compose down -v

# Restart a specific service
docker-compose restart backend

# View logs for specific service
docker-compose logs -f backend

# Update after code changes
docker-compose up -d --build

# Check resource usage
docker stats
```

---

## 🌐 Alternative: Cloud Platform Deployments

### Option 1: Railway (Easiest Cloud Deployment)

**Railway** provides one-click deployment with free tier.

1. **Sign up**: https://railway.app
2. **New Project** → "Deploy from GitHub"
3. **Connect repository**: Your Anchor repo
4. **Add services**:
   - PostgreSQL (add from marketplace)
   - Backend (from `/backend`)
   - Frontend (from `/frontend`)
5. **Set environment variables**:
   ```
   GROQ_API_KEY=your_key_here
   DATABASE_URL=<automatically set by Railway>
   ```
6. **Deploy**: Railway auto-deploys on git push

**Cost**: Free tier includes 500 hours/month

### Option 2: Render (Simple and Reliable)

**Render** offers zero-config deployment.

1. **Sign up**: https://render.com
2. **New** → "Blueprint"
3. **Connect repo** and use this `render.yaml`:

```yaml
services:
  - type: web
    name: anchor-backend
    env: python
    buildCommand: "cd backend && pip install -r requirements.txt"
    startCommand: "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: GROQ_API_KEY
        sync: false
      - key: DATABASE_URL
        fromDatabase:
          name: anchor-db
          property: connectionString

  - type: web
    name: anchor-frontend
    env: node
    buildCommand: "cd frontend && npm install && npm run build"
    staticPublishPath: frontend/dist

databases:
  - name: anchor-db
    plan: free
```

4. **Add environment variables** in dashboard
5. **Deploy**: Auto-deploys on push

**Cost**: Free tier available (limited hours)

### Option 3: AWS ECS (Production-Grade)

For production workloads with high availability.

```bash
# 1. Install AWS CLI
aws configure

# 2. Create ECR repositories
aws ecr create-repository --repository-name anchor-backend
aws ecr create-repository --repository-name anchor-frontend

# 3. Build and push images
docker build -t anchor-backend:latest ./backend
docker build -t anchor-frontend:latest ./frontend

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag anchor-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/anchor-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/anchor-backend:latest

docker tag anchor-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/anchor-frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/anchor-frontend:latest

# 4. Create ECS cluster and services (use AWS Console or Terraform)
```

**Cost**: ~$30-50/month for small instance (t3.small + RDS)

### Option 4: DigitalOcean App Platform

Simple managed platform with good pricing.

1. **Sign up**: https://www.digitalocean.com
2. **Apps** → "Create App"
3. **Connect GitHub repo**
4. **Configure services**:
   - Backend: Python app from `/backend`
   - Frontend: Static site from `/frontend/dist`
   - Database: PostgreSQL (managed)
5. **Set environment variables**
6. **Deploy**: Auto-deploys on push

**Cost**: ~$12/month (basic tier)

---

## 🔒 Production Checklist

Before going to production, ensure:

### Security

- [ ] Change default PostgreSQL password in `docker-compose.yml`
- [ ] Use HTTPS with SSL certificate (Let's Encrypt)
- [ ] Set strong `SECRET_KEY` for backend
- [ ] Enable CORS only for your domain
- [ ] Add authentication middleware
- [ ] Set up firewall rules
- [ ] Keep `.env` files out of version control

### Performance

- [ ] Enable PostgreSQL connection pooling
- [ ] Set up Redis for caching (replace in-memory cache)
- [ ] Add CDN for static assets
- [ ] Monitor resource usage
- [ ] Set up log aggregation (e.g., ELK stack)

### Reliability

- [ ] Set up automated backups (database)
- [ ] Configure health checks
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure auto-restart policies
- [ ] Set up error tracking (Sentry)
- [ ] Document incident response procedures

### Monitoring

```bash
# Add to docker-compose.yml for monitoring
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

---

## 📊 Scaling Considerations

### Vertical Scaling (Easier)

Increase container resources:

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Horizontal Scaling (More Complex)

Run multiple backend instances:

```yaml
services:
  backend:
    deploy:
      replicas: 3
    # Add load balancer (nginx or HAProxy)
```

**Requirements for horizontal scaling**:
- Replace in-memory cache with Redis
- Use managed database (not container)
- Shared file storage (S3 or NFS)
- Session management (Redis or database)

---

## 🐛 Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Port already in use
docker-compose down
netstat -ano | findstr :8000  # Windows
lsof -i :8000                # Mac/Linux

# 2. Database not ready
docker-compose restart backend  # Backend waits for DB health check

# 3. Build failed
docker-compose build --no-cache
```

### Database connection errors

```bash
# Check database is running
docker-compose ps postgres

# Connect to database
docker-compose exec postgres psql -U anchor_user -d anchor_db

# Reset database
docker-compose down -v
docker-compose up -d
```

### High memory usage

```bash
# Check memory usage
docker stats

# Limit container memory
# Add to docker-compose.yml:
mem_limit: 1g
mem_reservation: 512m
```

### Slow performance

```bash
# Check disk I/O
docker stats

# Use named volumes instead of bind mounts
# Already configured in docker-compose.yml

# Enable PostgreSQL tuning
# Add to docker-compose.yml postgres service:
command: postgres -c shared_buffers=256MB -c max_connections=200
```

---

## 🔄 Updates and Maintenance

### Update Application Code

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up -d --build

# Check migrations ran
docker-compose logs backend | grep "migration"
```

### Backup Database

```bash
# Create backup
docker-compose exec postgres pg_dump -U anchor_user anchor_db > backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose exec -T postgres psql -U anchor_user anchor_db < backup_20240812.sql
```

### Monitor Logs

```bash
# Tail all logs
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Save logs to file
docker-compose logs > anchor_logs.txt
```

---

## 💰 Cost Estimates

### Self-Hosted (VPS)

| Provider | Specs | Cost/Month |
|----------|-------|------------|
| DigitalOcean | 2 vCPU, 4GB RAM, 80GB SSD | $24 |
| Linode | 2 vCPU, 4GB RAM, 80GB SSD | $24 |
| Vultr | 2 vCPU, 4GB RAM, 80GB SSD | $24 |
| AWS EC2 | t3.medium (2 vCPU, 4GB) | ~$30 |

### Managed Platforms

| Platform | Plan | Cost/Month |
|----------|------|------------|
| Railway | Hobby | $5-20 (usage-based) |
| Render | Starter | Free tier available |
| Heroku | Hobby | $7 (each service) |
| DigitalOcean App Platform | Basic | $12 |

**Plus database costs**: $7-15/month for managed PostgreSQL

---

## 📝 Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GROQ_API_KEY` | Groq Cloud API key | Yes | - |
| `DATABASE_URL` | PostgreSQL connection string | Yes | Auto-set in Docker |
| `ENVIRONMENT` | `development` or `production` | No | `production` |
| `SECRET_KEY` | Session encryption key | No | Auto-generated |
| `CORS_ORIGINS` | Allowed CORS origins | No | `*` |
| `MAX_UPLOAD_SIZE` | Max file size in MB | No | `200` |

---

## 🎯 Success Criteria

Your deployment is successful when:

✅ All 4 containers show "Up" status  
✅ Frontend loads at http://localhost  
✅ Can upload a file successfully  
✅ Requirements extract without errors  
✅ Database persists after restart  
✅ API responds within 5 seconds  
✅ No errors in `docker-compose logs`  

---

## 📚 Additional Resources

- **Docker Compose Docs**: https://docs.docker.com/compose/
- **Nginx Configuration**: https://nginx.org/en/docs/
- **PostgreSQL Tuning**: https://pgtune.leopard.in.ua/
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/
- **React Production Build**: https://vitejs.dev/guide/build.html

---

**Need Help?**

1. Check logs: `docker-compose logs -f`
2. Review troubleshooting section above
3. Verify all environment variables are set
4. Ensure Docker has enough resources (4GB RAM minimum)

**Status Check Command**:
```bash
docker-compose ps && \
curl http://localhost/api/ && \
echo "✅ Deployment successful!"
```
