# 🌐 Server Deployment Guide - IP: 193.162.129.58

## 📋 Server Information

**Server IP:** `193.162.129.58`  
**Hostname:** `vm-184320`  
**Access URL:** `http://193.162.129.58:3000`

---

## 🚀 Quick Deployment Steps

### Step 1: Fix Hostname Resolution

```bash
# Fix the hostname warning
echo "127.0.0.1 vm-184320" | sudo tee -a /etc/hosts
echo "193.162.129.58 vm-184320" | sudo tee -a /etc/hosts
```

### Step 2: Extract and Navigate to Package

**Option A: If using the quick fix on existing package:**
```bash
cd ~
mv pdss-linux-installer_* pdss
cd pdss
```

**Option B: If using new package (recommended):**
```bash
# Transfer pdss-linux-v1.0.0-202510191553.zip to server
unzip pdss-linux-v1.0.0-202510191553.zip
cd pdss-linux-v1.0.0
```

### Step 3: Configure for Public Access

Before installing, update the environment configuration:

```bash
# Create .env file from example
cp config/.env.example .env

# Edit the .env file
nano .env
```

**Update these values in `.env`:**
```bash
# Database (keep as is for Docker internal)
DATABASE_URL=postgresql://postgres:postgres@db:5432/procurement_dss
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=procurement_dss

# Security - IMPORTANT!
SECRET_KEY=change-this-to-a-long-random-string-in-production

# CORS - Allow access from your server IP
ALLOWED_ORIGINS=http://193.162.129.58:3000,http://localhost:3000
```

**To generate a secure SECRET_KEY:**
```bash
# Generate random secret key
openssl rand -hex 32
# Copy the output and paste it as SECRET_KEY value
```

### Step 4: Configure Firewall

Allow access to port 3000:

**Ubuntu/Debian (UFW):**
```bash
# Enable firewall if not already enabled
sudo ufw enable

# Allow SSH (IMPORTANT - do this first!)
sudo ufw allow ssh
sudo ufw allow 22/tcp

# Allow PDSS port
sudo ufw allow 3000/tcp

# Check firewall status
sudo ufw status
```

**CentOS/RHEL (firewalld):**
```bash
# Allow PDSS port
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --reload

# Check firewall rules
sudo firewall-cmd --list-all
```

### Step 5: Ensure Docker is Running

```bash
# Start Docker
sudo systemctl start docker

# Enable Docker to start on boot
sudo systemctl enable docker

# Verify Docker is running
sudo systemctl status docker
```

### Step 6: Run Installer

```bash
# Make installer executable
chmod +x install.sh

# Run installer
sudo ./install.sh
```

**Wait 5-10 minutes for installation to complete.**

### Step 7: Verify Installation

```bash
# Check running containers
docker ps

# You should see 3 containers:
# - postgres (database)
# - backend (API)
# - frontend (web UI)

# Check logs if needed
docker-compose logs -f
```

### Step 8: Access the System

**From your browser:**
```
http://193.162.129.58:3000
```

**Default Login:**
```
Username: admin
Password: admin123
```

**⚠️ IMPORTANT: Change all default passwords immediately!**

---

## 🔒 Security Configuration

### 1. Change Default Passwords

After first login:
1. Go to User Management
2. Change password for all users:
   - admin
   - finance1
   - pm1
   - proc1

### 2. Configure HTTPS (Recommended for Production)

For production use, you should use HTTPS. Here are your options:

#### Option A: Using Nginx Reverse Proxy with Let's Encrypt

```bash
# Install Nginx
sudo apt-get update
sudo apt-get install nginx certbot python3-certbot-nginx

# Install Let's Encrypt certificate (requires domain name)
# If you have a domain pointing to 193.162.129.58:
sudo certbot --nginx -d yourdomain.com
```

**Nginx Configuration (`/etc/nginx/sites-available/pdss`):**
```nginx
server {
    listen 80;
    server_name 193.162.129.58;
    
    # Redirect to HTTPS (if using SSL)
    # return 301 https://$server_name$request_uri;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**Enable the configuration:**
```bash
sudo ln -s /etc/nginx/sites-available/pdss /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Allow HTTP/HTTPS through firewall
sudo ufw allow 'Nginx Full'
```

#### Option B: Using Caddy (Automatic HTTPS)

```bash
# Install Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy

# Create Caddyfile
sudo nano /etc/caddy/Caddyfile
```

**Caddyfile content:**
```
# Without domain (HTTP only)
http://193.162.129.58 {
    reverse_proxy localhost:3000
}

# With domain (automatic HTTPS)
# yourdomain.com {
#     reverse_proxy localhost:3000
# }
```

**Start Caddy:**
```bash
sudo systemctl restart caddy
sudo systemctl enable caddy
```

### 3. Database Security

**Change PostgreSQL password:**

```bash
# Access PostgreSQL container
docker-compose exec db psql -U postgres

# Change password
ALTER USER postgres WITH PASSWORD 'your-secure-password-here';
\q

# Update .env file with new password
nano .env
# Update: POSTGRES_PASSWORD=your-secure-password-here
# Update: DATABASE_URL=postgresql://postgres:your-secure-password-here@db:5432/procurement_dss

# Restart services
docker-compose restart
```

---

## 🔥 Firewall Configuration

### Required Ports

| Port | Service | Access |
|------|---------|--------|
| 22 | SSH | Admin only |
| 80 | HTTP | Public (if using reverse proxy) |
| 443 | HTTPS | Public (if using reverse proxy) |
| 3000 | PDSS Frontend | Public (or internal if using reverse proxy) |
| 8000 | PDSS Backend | Internal only (Docker network) |
| 5432 | PostgreSQL | Internal only (Docker network) |

### Recommended Firewall Rules

```bash
# Reset firewall (careful!)
# sudo ufw reset

# Allow SSH (CRITICAL - do this first!)
sudo ufw allow ssh
sudo ufw allow 22/tcp

# If using reverse proxy (Nginx/Caddy)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# If accessing PDSS directly (no reverse proxy)
sudo ufw allow 3000/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status numbered
```

### Block Direct Access to Backend/Database

Docker handles internal networking, but ensure these ports are NOT exposed externally:

```bash
# Check what ports are exposed
sudo netstat -tlnp | grep LISTEN

# Ports 8000 and 5432 should only listen on 127.0.0.1 or internal Docker network
```

---

## 📊 Monitoring & Maintenance

### System Status

```bash
# Check all containers
docker-compose ps

# View logs
docker-compose logs -f

# Check specific service logs
docker-compose logs backend -f
docker-compose logs frontend -f
docker-compose logs db -f
```

### Resource Monitoring

```bash
# Container resource usage
docker stats

# System resources
htop
# or
top

# Disk space
df -h

# Docker disk usage
docker system df
```

### Database Backup

**Create backup script:**

```bash
# Create backup directory
mkdir -p ~/pdss-backups

# Create backup script
nano ~/backup-pdss.sh
```

**Backup script content:**
```bash
#!/bin/bash
BACKUP_DIR=~/pdss-backups
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=30

# Navigate to PDSS directory
cd ~/pdss  # or ~/pdss-linux-v1.0.0

# Create backup
docker-compose exec -T db pg_dump -U postgres procurement_dss > "$BACKUP_DIR/pdss_backup_$DATE.sql"

# Compress backup
gzip "$BACKUP_DIR/pdss_backup_$DATE.sql"

# Remove old backups
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$KEEP_DAYS -delete

echo "Backup completed: pdss_backup_$DATE.sql.gz"
```

**Make executable and schedule:**
```bash
chmod +x ~/backup-pdss.sh

# Test backup
~/backup-pdss.sh

# Schedule daily backup at 2 AM
crontab -e
# Add this line:
0 2 * * * /root/backup-pdss.sh >> /var/log/pdss-backup.log 2>&1
```

### System Updates

```bash
# Update system packages
sudo apt update
sudo apt upgrade

# Update Docker images
cd ~/pdss  # or ~/pdss-linux-v1.0.0
docker-compose pull
docker-compose up -d --build

# Clean up old Docker images
docker system prune -a
```

---

## 🌐 Access Configuration

### Local Network Access

If accessing from local network (e.g., 192.168.x.x):
```
http://193.162.129.58:3000
```

### Internet Access

If accessing from internet:
```
http://193.162.129.58:3000
```

**Ensure your network/firewall allows incoming connections on port 3000.**

### Domain Name (Optional)

If you have a domain name pointing to 193.162.129.58:

1. **Set up DNS A record:**
   ```
   pdss.yourdomain.com → 193.162.129.58
   ```

2. **Update ALLOWED_ORIGINS in .env:**
   ```bash
   ALLOWED_ORIGINS=http://pdss.yourdomain.com,http://193.162.129.58:3000
   ```

3. **Configure reverse proxy (Nginx/Caddy) as shown above**

4. **Access at:**
   ```
   http://pdss.yourdomain.com
   ```

---

## 🛠️ Troubleshooting

### Cannot Access from Browser

**Check 1: Firewall**
```bash
sudo ufw status
# Ensure port 3000 is allowed
sudo ufw allow 3000/tcp
```

**Check 2: Containers Running**
```bash
docker-compose ps
# All 3 containers should be Up
```

**Check 3: Port Binding**
```bash
sudo netstat -tlnp | grep 3000
# Should show docker-proxy listening on 0.0.0.0:3000
```

**Check 4: Cloud Provider Firewall**
- Check your cloud provider's security groups/firewall rules
- Ensure port 3000 is allowed from your IP or 0.0.0.0/0

### CORS Errors

If you see CORS errors in browser console:

```bash
# Update .env file
nano .env

# Add your access URL to ALLOWED_ORIGINS
ALLOWED_ORIGINS=http://193.162.129.58:3000,http://localhost:3000,http://your-domain.com

# Restart backend
docker-compose restart backend
```

### Performance Issues

```bash
# Check resources
docker stats

# Increase resources if needed (in docker-compose.yml)
# Add under services > backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

# Restart
docker-compose down
docker-compose up -d
```

---

## 📋 Post-Deployment Checklist

After successful deployment:

- [ ] System accessible at http://193.162.129.58:3000
- [ ] All 3 containers running (postgres, backend, frontend)
- [ ] Default passwords changed
- [ ] SECRET_KEY updated in .env
- [ ] Firewall configured
- [ ] HTTPS configured (for production)
- [ ] Automated backups scheduled
- [ ] Database password changed
- [ ] System monitored and healthy
- [ ] Documentation provided to users

---

## 🎯 Quick Command Reference

```bash
# Start system
cd ~/pdss && docker-compose up -d

# Stop system
cd ~/pdss && docker-compose down

# Restart system
cd ~/pdss && docker-compose restart

# View logs
cd ~/pdss && docker-compose logs -f

# Check status
cd ~/pdss && docker-compose ps

# Backup database
cd ~/pdss && docker-compose exec -T db pg_dump -U postgres procurement_dss > backup.sql

# Update system
cd ~/pdss && docker-compose pull && docker-compose up -d --build
```

---

## 🆘 Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Check firewall: `sudo ufw status`
3. Check containers: `docker-compose ps`
4. Review documentation in `docs/` folder

---

**Deployment Server:** `193.162.129.58`  
**Access URL:** `http://193.162.129.58:3000`  
**Status:** Ready for deployment  
**Date:** October 19, 2025

---

**Your PDSS system is ready for production deployment!** 🚀

