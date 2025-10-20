# 🎮 Server Management Commands

## 🚀 Quick Reference

### Start Server
```bash
cd ~/pdss  # or cd ~/pdss-linux-v1.0.0
docker-compose up -d
```

### Stop Server
```bash
cd ~/pdss  # or cd ~/pdss-linux-v1.0.0
docker-compose down
```

### Restart Server
```bash
cd ~/pdss  # or cd ~/pdss-linux-v1.0.0
docker-compose restart
```

### Check Status
```bash
cd ~/pdss  # or cd ~/pdss-linux-v1.0.0
docker-compose ps
```

### View Logs
```bash
cd ~/pdss  # or cd ~/pdss-linux-v1.0.0
docker-compose logs -f
```

---

## 📖 Detailed Commands

### 1. Start the Server

**Start all services:**
```bash
cd ~/pdss
docker-compose up -d
```

**What happens:**
- `-d` = detached mode (runs in background)
- Starts 3 containers: database, backend, frontend
- Takes 30-60 seconds to fully start
- Server accessible at: http://193.162.129.58:3000

**Verify it started:**
```bash
docker-compose ps

# Should show:
# NAME                    STATUS
# pdss-db-1              Up
# pdss-backend-1         Up
# pdss-frontend-1        Up
```

**Check logs:**
```bash
docker-compose logs -f
# Press Ctrl+C to exit logs
```

---

### 2. Stop the Server

**Stop all services:**
```bash
cd ~/pdss
docker-compose down
```

**What happens:**
- Stops all 3 containers
- Removes containers
- **Data is preserved** in Docker volumes
- Network connections are closed

**Verify it stopped:**
```bash
docker-compose ps

# Should show:
# (empty - no containers running)
```

**Note:** Your data is safe! The database volume persists even after stopping.

---

### 3. Restart the Server

**Method 1: Soft Restart (Faster)**
```bash
cd ~/pdss
docker-compose restart
```

**Method 2: Full Restart (Clean)**
```bash
cd ~/pdss
docker-compose down
docker-compose up -d
```

**When to restart:**
- After changing .env file
- After system updates
- When server is slow or unresponsive
- After changing configuration

---

### 4. Check Server Status

**View running containers:**
```bash
cd ~/pdss
docker-compose ps
```

**View detailed status:**
```bash
docker ps
```

**Check resource usage:**
```bash
docker stats
# Press Ctrl+C to exit
```

**Check if accessible:**
```bash
curl http://localhost:3000
# Should return HTML
```

---

### 5. View Logs

**All services:**
```bash
cd ~/pdss
docker-compose logs -f
```

**Specific service:**
```bash
cd ~/pdss

# Backend logs
docker-compose logs backend -f

# Frontend logs
docker-compose logs frontend -f

# Database logs
docker-compose logs db -f
```

**Last 100 lines:**
```bash
docker-compose logs --tail=100
```

**Press `Ctrl+C` to exit log view**

---

## 🔧 Advanced Management

### Update Server

**Pull latest code and rebuild:**
```bash
cd ~/pdss
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Clean Restart (Reset Everything)

**⚠️ WARNING: This will delete all data!**
```bash
cd ~/pdss
docker-compose down -v  # -v removes volumes (deletes data!)
docker-compose up -d
```

### Rebuild Single Service

```bash
cd ~/pdss

# Rebuild backend
docker-compose up -d --build backend

# Rebuild frontend
docker-compose up -d --build frontend
```

### Access Database

**PostgreSQL command line:**
```bash
cd ~/pdss
docker-compose exec db psql -U postgres procurement_dss
```

**Inside PostgreSQL:**
```sql
-- List tables
\dt

-- View users
SELECT * FROM users;

-- Exit
\q
```

---

## 📊 Monitoring

### Check System Health

```bash
# Container status
docker-compose ps

# Resource usage
docker stats --no-stream

# Disk usage
df -h

# Docker disk usage
docker system df
```

### Check Connectivity

```bash
# Check if frontend is accessible
curl http://localhost:3000

# Check if backend is accessible
curl http://localhost:8000/api/health
```

### Monitor Logs in Real-Time

```bash
# All services
docker-compose logs -f

# Follow specific service
docker-compose logs backend -f
```

---

## 🎯 Common Scenarios

### Scenario 1: Server Not Responding

```bash
# Check status
docker-compose ps

# View logs for errors
docker-compose logs

# Restart
docker-compose restart

# If still not working, full restart
docker-compose down
docker-compose up -d
```

### Scenario 2: After Changing .env File

```bash
# Restart backend to load new environment
docker-compose restart backend
```

### Scenario 3: After System Reboot

```bash
# Start Docker service
sudo systemctl start docker

# Start PDSS
cd ~/pdss
docker-compose up -d
```

### Scenario 4: Memory Issues

```bash
# Check memory usage
docker stats --no-stream

# Restart to free memory
docker-compose restart
```

### Scenario 5: Database Issues

```bash
# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db

# If corrupt, backup and recreate
docker-compose exec -T db pg_dump -U postgres procurement_dss > backup.sql
docker-compose down -v
docker-compose up -d
# Then restore from backup if needed
```

---

## 🤖 Automated Management

### Auto-Start on System Boot

**Enable Docker to start on boot:**
```bash
sudo systemctl enable docker
```

**Create systemd service for PDSS:**
```bash
sudo nano /etc/systemd/system/pdss.service
```

**Add this content:**
```ini
[Unit]
Description=PDSS - Procurement Decision Support System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/root/pdss
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable pdss
sudo systemctl start pdss
```

**Manage with systemd:**
```bash
# Start
sudo systemctl start pdss

# Stop
sudo systemctl stop pdss

# Restart
sudo systemctl restart pdss

# Status
sudo systemctl status pdss
```

---

## 📁 Management Scripts

### Create Quick Access Scripts

**Create start script:**
```bash
cat > ~/start-pdss.sh << 'EOF'
#!/bin/bash
cd ~/pdss
echo "Starting PDSS..."
docker-compose up -d
sleep 5
echo ""
echo "PDSS Status:"
docker-compose ps
echo ""
echo "Access at: http://193.162.129.58:3000"
EOF
chmod +x ~/start-pdss.sh
```

**Create stop script:**
```bash
cat > ~/stop-pdss.sh << 'EOF'
#!/bin/bash
cd ~/pdss
echo "Stopping PDSS..."
docker-compose down
echo "PDSS stopped."
EOF
chmod +x ~/stop-pdss.sh
```

**Create status script:**
```bash
cat > ~/status-pdss.sh << 'EOF'
#!/bin/bash
cd ~/pdss
echo "========================================="
echo "  PDSS System Status"
echo "========================================="
echo ""
echo "Containers:"
docker-compose ps
echo ""
echo "Resource Usage:"
docker stats --no-stream
echo ""
echo "Access URL: http://193.162.129.58:3000"
echo "========================================="
EOF
chmod +x ~/status-pdss.sh
```

**Create logs script:**
```bash
cat > ~/logs-pdss.sh << 'EOF'
#!/bin/bash
cd ~/pdss
docker-compose logs -f
EOF
chmod +x ~/logs-pdss.sh
```

**Use the scripts:**
```bash
# Start server
~/start-pdss.sh

# Stop server
~/stop-pdss.sh

# Check status
~/status-pdss.sh

# View logs
~/logs-pdss.sh
```

---

## 🔄 Update Workflow

### Regular Updates

```bash
# 1. Backup data
cd ~/pdss
docker-compose exec -T db pg_dump -U postgres procurement_dss > backup_$(date +%Y%m%d).sql

# 2. Stop server
docker-compose down

# 3. Update code (if you have git repo)
git pull

# 4. Rebuild
docker-compose build --no-cache

# 5. Start server
docker-compose up -d

# 6. Verify
docker-compose ps
docker-compose logs
```

---

## 🛡️ Backup & Restore

### Backup Database

```bash
cd ~/pdss

# Backup
docker-compose exec -T db pg_dump -U postgres procurement_dss > backup.sql

# Backup with date
docker-compose exec -T db pg_dump -U postgres procurement_dss > backup_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database

```bash
cd ~/pdss

# Stop backend and frontend
docker-compose stop backend frontend

# Restore
cat backup.sql | docker-compose exec -T db psql -U postgres procurement_dss

# Restart
docker-compose start backend frontend
```

---

## 📞 Troubleshooting Commands

### Service Won't Start

```bash
# Check logs for errors
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db

# Check Docker is running
sudo systemctl status docker

# Check port availability
sudo netstat -tlnp | grep 3000
sudo netstat -tlnp | grep 8000
sudo netstat -tlnp | grep 5432
```

### Clear Everything and Start Fresh

**⚠️ WARNING: Deletes all data!**
```bash
cd ~/pdss

# Stop and remove everything
docker-compose down -v

# Remove images
docker-compose rm -f

# Rebuild and start
docker-compose build --no-cache
docker-compose up -d
```

### Check Disk Space

```bash
# System disk space
df -h

# Docker disk usage
docker system df

# Clean up unused Docker data
docker system prune -a
```

---

## ⚡ Quick Command Cheat Sheet

```bash
# START
cd ~/pdss && docker-compose up -d

# STOP
cd ~/pdss && docker-compose down

# RESTART
cd ~/pdss && docker-compose restart

# STATUS
cd ~/pdss && docker-compose ps

# LOGS
cd ~/pdss && docker-compose logs -f

# BACKEND LOGS
cd ~/pdss && docker-compose logs backend -f

# FRONTEND LOGS
cd ~/pdss && docker-compose logs frontend -f

# DATABASE LOGS
cd ~/pdss && docker-compose logs db -f

# BACKUP
cd ~/pdss && docker-compose exec -T db pg_dump -U postgres procurement_dss > backup.sql

# UPDATE
cd ~/pdss && docker-compose down && docker-compose up -d --build

# CLEAN RESTART
cd ~/pdss && docker-compose down && docker-compose up -d
```

---

## 🎯 Most Common Commands

**99% of the time, you'll use these:**

```bash
# Start server
cd ~/pdss
docker-compose up -d

# Stop server
cd ~/pdss
docker-compose down

# Check if running
cd ~/pdss
docker-compose ps

# View logs if something is wrong
cd ~/pdss
docker-compose logs -f
```

---

## 📱 Access Information

**After starting the server:**

**URL:** http://193.162.129.58:3000

**Login:**
- Username: `admin`
- Password: `admin123`

**To check if accessible:**
```bash
curl http://193.162.129.58:3000
```

---

**That's it! Server management made simple!** 🚀

**Most used commands:**
1. Start: `cd ~/pdss && docker-compose up -d`
2. Stop: `cd ~/pdss && docker-compose down`
3. Status: `cd ~/pdss && docker-compose ps`
4. Logs: `cd ~/pdss && docker-compose logs -f`

