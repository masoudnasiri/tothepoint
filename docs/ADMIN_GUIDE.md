# 👨‍💼 PDSS Administrator Guide

## Table of Contents

1. [Administrator Responsibilities](#administrator-responsibilities)
2. [Initial Setup](#initial-setup)
3. [User Management](#user-management)
4. [System Configuration](#system-configuration)
5. [Database Management](#database-management)
6. [Security & Access Control](#security--access-control)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Backup & Recovery](#backup--recovery)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Configuration](#advanced-configuration)

---

## Administrator Responsibilities

As a system administrator, you are responsible for:

✅ User account management
✅ Role assignments and permissions
✅ System configuration and settings
✅ Data integrity and backups
✅ Security and access control
✅ Performance monitoring
✅ System updates and maintenance
✅ User support and training

---

## Initial Setup

### First Time System Setup

#### 1. Initial Login

Default admin credentials (⚠️ **CHANGE IMMEDIATELY!**):
- Username: `admin`
- Password: [Set during first login]

#### 2. Change Admin Password

1. Login with default credentials
2. Navigate to **Users** module
3. Find admin user
4. Click **Edit**
5. Set a strong password (min 12 characters, mix of uppercase, lowercase, numbers, symbols)
6. Click **Save**

#### 3. Create Additional Users

Create users for each team member:

1. Navigate to **Users** module
2. Click **Add User**
3. Fill in details:
   - **Username** (required, unique)
   - **Password** (required, min 6 chars)
   - **Role** (required - see roles below)
   - **Active Status** (default: active)
4. Click **Create**

### User Roles Explained

| Role | Use Case | Typical Users |
|------|----------|---------------|
| **admin** | Full system access, configuration | System administrators, IT team |
| **pmo** | Project oversight, item finalization | PMO directors, project coordinators |
| **pm** | Project management, item creation | Project managers, team leads |
| **procurement** | Supplier management, options | Procurement officers, buyers |
| **finance** | Financial tracking, optimization | Finance team, controllers |

#### 4. Configure Decision Weights

Set the importance of each optimization criterion:

1. Navigate to **Decision Weights** module
2. Adjust weights (must sum to 1.0):
   - **Cost Weight** - How important is price? (0.0 - 1.0)
   - **Lead Time Weight** - How important is delivery speed?
   - **Quality Weight** - How important is quality/reliability?
   - **Payment Terms Weight** - How important are favorable payment terms?
3. Click **Save**

**Example Weight Sets:**

**Cost-Focused Organization:**
```
Cost: 0.50
Lead Time: 0.20
Quality: 0.20
Payment Terms: 0.10
```

**Quality-Focused Organization:**
```
Cost: 0.20
Lead Time: 0.20
Quality: 0.50
Payment Terms: 0.10
```

**Balanced Approach:**
```
Cost: 0.30
Lead Time: 0.30
Quality: 0.25
Payment Terms: 0.15
```

#### 5. Setup Currencies

Add currencies used by your organization:

1. Navigate to **Procurement** module
2. Access **Currency Management**
3. Add currencies:
   - **Code** (e.g., USD, EUR, GBP)
   - **Name** (e.g., US Dollar)
   - **Symbol** (e.g., $, €, £)
   - **Decimal Places** (usually 2)
   - **Is Base Currency** (select primary currency)
   - **Exchange Rate** (rate to base currency)
4. Click **Save**

**Important:** Set one currency as base currency for all conversions.

#### 6. Populate Items Master

Create your organization's item catalog:

1. Navigate to **Items Master** module
2. Click **Add Item**
3. Fill in item details:
   - **Company** (manufacturer/brand)
   - **Item Name**
   - **Model** (optional)
   - **Specifications** (JSON format for detailed specs)
   - **Category** (for grouping)
   - **Unit** (piece, kg, meter, etc.)
   - **Description**
4. Click **Create**

**Item Code Format:** Auto-generated as `COMPANY-###`

---

## User Management

### Creating Users

See [Initial Setup](#initial-setup) section above.

### Editing Users

1. Navigate to **Users** module
2. Find the user in the list
3. Click **Edit** icon
4. Modify fields:
   - Username (⚠️ affects login)
   - Password (leave blank to keep current)
   - Role (affects permissions)
   - Active status (inactive users cannot login)
5. Click **Save**

### Deactivating Users

**Best Practice:** Deactivate instead of delete to preserve audit trail

1. Navigate to **Users** module
2. Find the user
3. Click **Edit**
4. Uncheck **Is Active**
5. Click **Save**

User will be immediately logged out and cannot log back in.

### Reactivating Users

1. Navigate to **Users** module
2. Filter/search for inactive users
3. Find the user
4. Click **Edit**
5. Check **Is Active**
6. Optionally reset password
7. Click **Save**

### Deleting Users

⚠️ **Warning:** Deletion is permanent and may cause data integrity issues!

**Only delete users who:**
- Have never logged in
- Have no associated data
- Were created by mistake

1. Navigate to **Users** module
2. Find the user
3. Click **Delete** icon
4. Confirm deletion

### Password Reset

**For users who forgot their password:**

1. Navigate to **Users** module
2. Find the user
3. Click **Edit**
4. Enter a temporary password
5. Click **Save**
6. Inform the user of their temporary password
7. Instruct them to change it on first login

---

## System Configuration

### Environment Variables

Key configuration is stored in `.env` file:

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/procurement_dss

# Security
SECRET_KEY=<your-secret-key>  # Change this!
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (adjust for your domain)
CORS_ORIGINS=["http://localhost:3000"]

# Application Settings
APP_NAME=Procurement DSS
VERSION=1.0.0
DEBUG=False  # Set to False in production
```

**⚠️ Security Warning:**
- Never commit `.env` to version control
- Use strong, unique SECRET_KEY
- Rotate keys periodically
- Restrict CORS_ORIGINS in production

### Docker Configuration

Located in `docker-compose.yml`:

```yaml
# Adjust resource limits for production
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G

# Adjust port mappings if needed
ports:
  - "3000:3000"  # Frontend
  - "8000:8000"  # Backend
  - "5432:5432"  # Database
```

### Application Settings

**Backend Configuration** (`backend/app/config.py`):
- Pagination limits
- File upload limits
- Session timeouts
- Rate limiting

**Frontend Configuration** (`frontend/src/config.ts`):
- API base URL
- Polling intervals
- UI preferences

---

## Database Management

### Database Access

**Using pgAdmin:**
```
Host: localhost
Port: 5432
Database: procurement_dss
Username: postgres
Password: [from .env file]
```

**Using Docker exec:**
```bash
docker-compose exec postgres psql -U postgres -d procurement_dss
```

### Common Database Operations

#### View All Tables
```sql
\dt
```

#### Count Records
```sql
SELECT 
    'projects' as table_name, COUNT(*) as count FROM projects
UNION
SELECT 'project_items', COUNT(*) FROM project_items
UNION
SELECT 'procurement_options', COUNT(*) FROM procurement_options
UNION
SELECT 'users', COUNT(*) FROM users;
```

#### Check Database Size
```sql
SELECT pg_size_pretty(pg_database_size('procurement_dss'));
```

#### View Active Connections
```sql
SELECT 
    pid, 
    usename, 
    application_name, 
    client_addr, 
    state 
FROM pg_stat_activity 
WHERE datname = 'procurement_dss';
```

### Database Maintenance

#### Vacuum (Cleanup)
```sql
VACUUM ANALYZE;
```

#### Reindex
```sql
REINDEX DATABASE procurement_dss;
```

#### Update Statistics
```sql
ANALYZE;
```

### Database Migrations

When schema changes are needed:

1. Create migration SQL file in `backend/migrations/`
2. Apply migration:
```bash
docker-compose exec postgres psql -U postgres -d procurement_dss -f /path/to/migration.sql
```

3. Verify migration:
```sql
\d table_name  -- Check table structure
```

---

## Security & Access Control

### Security Best Practices

✅ **DO:**
- Use strong passwords (min 12 chars)
- Enable HTTPS in production
- Rotate SECRET_KEY periodically
- Keep Docker images updated
- Monitor login attempts
- Regular security audits
- Backup encryption keys
- Restrict database access
- Use firewall rules
- Enable audit logging

❌ **DON'T:**
- Share admin credentials
- Use default passwords
- Expose database ports publicly
- Commit secrets to git
- Run as root in production
- Skip security updates
- Disable authentication
- Allow weak passwords

### Access Control Matrix

Review the permissions matrix in [PLATFORM_OVERVIEW.md](./PLATFORM_OVERVIEW.md)

### Audit Logging

**View User Activity:**

```sql
-- Recent user logins
SELECT u.username, u.role, u.created_at 
FROM users u 
ORDER BY u.created_at DESC 
LIMIT 10;

-- Recent project changes
SELECT p.name, p.updated_at 
FROM projects p 
ORDER BY p.updated_at DESC 
LIMIT 10;
```

### Security Incident Response

If you suspect a security breach:

1. **Immediate Actions:**
   - Change all passwords
   - Rotate SECRET_KEY
   - Review recent user activity
   - Check database for anomalies
   - Review system logs

2. **Investigation:**
   - Identify affected accounts
   - Check data integrity
   - Review access logs
   - Document findings

3. **Remediation:**
   - Patch vulnerabilities
   - Update security policies
   - Train users
   - Enhance monitoring

---

## Monitoring & Maintenance

### System Health Checks

#### Backend Health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","version":"1.0.0"}
```

#### Database Health
```bash
docker-compose exec postgres pg_isready -U postgres
```

#### Container Status
```bash
docker-compose ps
```

All containers should show "Up" status.

### Performance Monitoring

#### Check Container Resources
```bash
docker stats
```

#### Database Performance
```sql
-- Slow queries
SELECT 
    query, 
    calls, 
    total_time, 
    mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Table sizes
SELECT 
    schemaname, 
    tablename, 
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Log Management

#### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# Follow logs
docker-compose logs -f backend

# Last N lines
docker-compose logs --tail=100 backend
```

#### Log Rotation

Configure in `docker-compose.yml`:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Routine Maintenance

**Daily:**
- ✅ Check system health
- ✅ Review error logs
- ✅ Monitor disk space

**Weekly:**
- ✅ Review user activity
- ✅ Check database performance
- ✅ Test backup restoration
- ✅ Update documentation

**Monthly:**
- ✅ Security audit
- ✅ Performance optimization
- ✅ Clean old data
- ✅ System updates
- ✅ User access review

---

## Backup & Recovery

### Automated Backup Script

Create `backup.sh`:

```bash
#!/bin/bash

# Configuration
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="pdss_backup_${DATE}.sql.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T postgres pg_dump -U postgres procurement_dss | gzip > "$BACKUP_DIR/$BACKUP_FILE"

# Keep only last 30 days
find $BACKUP_DIR -name "pdss_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

Make executable and schedule:
```bash
chmod +x backup.sh

# Add to crontab (daily at 2 AM)
0 2 * * * /path/to/backup.sh
```

### Manual Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres procurement_dss > backup.sql

# Compress
gzip backup.sql

# Backup files
tar -czf files_backup.tar.gz backend/uploads/
```

### Restoration

```bash
# Stop application
docker-compose down

# Restore database
gunzip < backup.sql.gz | docker-compose exec -T postgres psql -U postgres procurement_dss

# Restore files
tar -xzf files_backup.tar.gz

# Start application
docker-compose up -d
```

### Disaster Recovery Plan

1. **Regular backups** stored off-site
2. **Documented restore procedures**
3. **Test restores monthly**
4. **Emergency contact list**
5. **Rollback procedures**

---

## Troubleshooting

### Common Issues

#### 1. Containers Won't Start

**Symptoms:** `docker-compose up` fails

**Solutions:**
```bash
# Check logs
docker-compose logs

# Clean and rebuild
docker-compose down
docker system prune -f
docker-compose up --build -d
```

#### 2. Database Connection Error

**Symptoms:** "Connection refused" errors

**Solutions:**
```bash
# Check database container
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Verify credentials in .env

# Test connection
docker-compose exec postgres psql -U postgres -c "SELECT 1;"
```

#### 3. Frontend Can't Reach Backend

**Symptoms:** API calls failing

**Solutions:**
```bash
# Check backend health
curl http://localhost:8000/health

# Check backend logs
docker-compose logs backend

# Verify CORS settings in backend/.env

# Check frontend proxy in package.json
```

#### 4. Slow Performance

**Solutions:**
```sql
-- Check for missing indexes
SELECT schemaname, tablename, indexname 
FROM pg_indexes 
WHERE schemaname = 'public';

-- Vacuum database
VACUUM ANALYZE;

-- Update statistics
ANALYZE;
```

#### 5. Out of Disk Space

**Solutions:**
```bash
# Check disk usage
df -h

# Clean Docker
docker system prune -a

# Clean old logs
docker-compose logs --tail=0

# Remove old backups
find /backups -mtime +30 -delete
```

### Getting Support

1. Check logs: `docker-compose logs`
2. Review this guide
3. Check GitHub issues
4. Contact support with:
   - Error messages
   - Log excerpts
   - Steps to reproduce
   - System information

---

## Advanced Configuration

### HTTPS Setup (Production)

Use nginx reverse proxy:

1. Install nginx
2. Configure SSL certificates
3. Setup reverse proxy
4. Update CORS settings

Example nginx config:
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Load Balancing

For high-traffic deployments:

1. Deploy multiple backend instances
2. Setup load balancer (nginx/HAProxy)
3. Configure session persistence
4. Database connection pooling

### Monitoring Integration

Integrate with monitoring tools:

**Prometheus + Grafana:**
- Add metrics endpoints
- Configure Prometheus scraping
- Create Grafana dashboards

**ELK Stack:**
- Configure log shipping
- Setup Elasticsearch
- Create Kibana visualizations

### Custom Development

For custom features:

1. Fork repository
2. Create feature branch
3. Follow coding standards
4. Write tests
5. Submit pull request

---

## Appendix

### Useful Commands

```bash
# View all containers
docker ps -a

# Remove all stopped containers
docker container prune

# View images
docker images

# Remove unused images
docker image prune -a

# View volumes
docker volume ls

# Backup volume
docker run --rm -v volume_name:/data -v $(pwd):/backup ubuntu tar czf /backup/backup.tar.gz /data

# View networks
docker network ls

# Inspect network
docker network inspect network_name
```

### SQL Queries for Administration

```sql
-- Find largest tables
SELECT 
    relname as table_name,
    pg_size_pretty(pg_total_relation_size(relid)) as total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- Find duplicate records (example)
SELECT item_code, COUNT(*) 
FROM project_items 
GROUP BY item_code 
HAVING COUNT(*) > 1;

-- Reset user password
UPDATE users 
SET password_hash = '$2b$12$...' -- Generate new hash
WHERE username = 'user_name';
```

---

**For more information:**
- [User Guide](./USER_GUIDE.md)
- [API Documentation](./API_DOCUMENTATION.md)
- [Platform Overview](./PLATFORM_OVERVIEW.md)

---

*Last Updated: October 20, 2025*

