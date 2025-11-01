# Troubleshooting Docker Build Failures

## Problem

Docker build fails with:
```
ERROR [frontend internal] load metadata for docker.io/library/node:1  10.1s
ERROR [backend internal] load metadata for docker.io/library/python:  10.1s
```

## Immediate Solutions

### Option 1: Pre-pull Base Images (Recommended)

Before running `./install.sh`, manually pull the base images:

```bash
# Pull base images first
docker pull python:3.11-slim
docker pull node:18-alpine
docker pull postgres:15-alpine

# Then run installer
sudo ./install.sh
```

### Option 2: Check Network Connectivity

```bash
# Test Docker Hub connectivity
ping -c 3 registry-1.docker.io

# Test DNS resolution
nslookup registry-1.docker.io

# Try pulling a test image
docker pull hello-world
```

### Option 3: Configure Docker Proxy (If Behind Corporate Firewall)

Create `/etc/docker/daemon.json`:

```json
{
  "proxies": {
    "http-proxy": "http://proxy.example.com:8080",
    "https-proxy": "http://proxy.example.com:8080",
    "no-proxy": "localhost,127.0.0.1"
  }
}
```

Then restart Docker:
```bash
sudo systemctl restart docker
```

### Option 4: Use Mirror/Alternative Registry

If Docker Hub is blocked, use a mirror. Create `/etc/docker/daemon.json`:

```json
{
  "registry-mirrors": [
    "https://mirror.gcr.io",
    "https://dockerhub.azk8s.cn"
  ]
}
```

Restart Docker:
```bash
sudo systemctl restart docker
```

### Option 5: Increase Docker Build Timeout

Edit `docker-compose.yml` and add to each service:

```yaml
services:
  backend:
    build:
      context: ./backend
      args:
        DOCKER_BUILDKIT: 1
    # ... rest of config
```

Or build with increased timeout:

```bash
DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose build --no-cache
```

### Option 6: Build Without Cache

Sometimes cache causes issues:

```bash
docker-compose build --no-cache --pull
```

## Verification

After fixing network issues, verify:

```bash
# Check Docker can pull images
docker pull python:3.11-slim
docker pull node:18-alpine

# Verify Dockerfiles exist in package
ls -la backend/Dockerfile frontend/Dockerfile

# Check docker-compose.yml
cat docker-compose.yml | grep -A 2 "build:"
```

## Common Issues

### Issue: "No internet connection"
- Check: `ping 8.8.8.8`
- Solution: Fix network configuration

### Issue: "DNS resolution failed"
- Check: `/etc/resolv.conf`
- Solution: Add DNS servers (8.8.8.8, 1.1.1.1)

### Issue: "Proxy required"
- Check: Corporate firewall/proxy
- Solution: Configure Docker proxy settings

### Issue: "Docker Hub rate limiting"
- Check: Too many pulls from same IP
- Solution: Login to Docker Hub: `docker login`

