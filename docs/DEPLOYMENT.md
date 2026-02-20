# Pigeon Deployment Guide

This guide covers deploying Pigeon in production environments with proper error handling, logging, and monitoring.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Systemd Service Deployment](#systemd-service-deployment)
- [Docker Deployment](#docker-deployment)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Upgrades](#upgrades)
- [Security](#security)

## Prerequisites

### System Requirements

- Python 3.10 or higher
- Linux system with systemd (or Docker for containerized deployment)
- 500MB disk space minimum
- Network access to Google Drive and (optionally) Slack APIs
- Google Drive API credentials (from google-personal-mcp setup)

### Dependencies

```bash
# Install system packages (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    git \
    curl \
    jq

# Optional: for Docker deployment
sudo apt-get install -y docker.io
```

## Installation

### Step 1: Create System User

```bash
# Create pigeon user for running the service
sudo useradd -r -s /bin/false pigeon

# Create directories
sudo mkdir -p /opt/pigeon
sudo mkdir -p /var/lib/pigeon/{inbox,inbox-archive}
sudo mkdir -p /var/log/pigeon
sudo mkdir -p /etc/pigeon

# Set permissions
sudo chown pigeon:pigeon /opt/pigeon
sudo chown pigeon:pigeon /var/lib/pigeon
sudo chown pigeon:pigeon /var/log/pigeon
sudo chown pigeon:pigeon /etc/pigeon
```

### Step 2: Install Pigeon Package

```bash
# Clone or copy pigeon module to /opt/pigeon
sudo cp -r modules/pigeon /opt/pigeon

# Set permissions
sudo chown -R pigeon:pigeon /opt/pigeon

# Install in virtual environment
cd /opt/pigeon
sudo -u pigeon python3.10 -m venv venv
sudo -u pigeon venv/bin/pip install -e .
```

### Step 3: Configure Credentials

```bash
# Copy Google credentials to pigeon user
sudo -u pigeon mkdir -p /home/pigeon/.config/google-personal-mcp/profiles/default
sudo cp ~/.config/google-personal-mcp/profiles/default/* \
    /home/pigeon/.config/google-personal-mcp/profiles/default/

# Fix permissions
sudo chown -R pigeon:pigeon /home/pigeon/.config
```

### Step 4: Configure Environment

```bash
# Copy environment template
sudo cp /opt/pigeon/config/systemd/pigeon.env.example /etc/pigeon/pigeon.env

# Edit configuration
sudo nano /etc/pigeon/pigeon.env

# Set permissions
sudo chmod 640 /etc/pigeon/pigeon.env
sudo chown pigeon:pigeon /etc/pigeon/pigeon.env
```

## Systemd Service Deployment

### Install Service

```bash
# Copy systemd files
sudo cp /opt/pigeon/config/systemd/pigeon.service /etc/systemd/system/
sudo cp /opt/pigeon/config/systemd/pigeon-restart.timer /etc/systemd/system/
sudo cp /opt/pigeon/config/systemd/pigeon-restart.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable pigeon
sudo systemctl enable pigeon-restart.timer
```

### Start Service

```bash
# Start the service
sudo systemctl start pigeon

# Check status
sudo systemctl status pigeon

# View logs
sudo journalctl -u pigeon -f
```

### Service Management

```bash
# Stop the service
sudo systemctl stop pigeon

# Restart the service
sudo systemctl restart pigeon

# Check service status
sudo systemctl status pigeon

# View recent logs (last 50 lines)
sudo journalctl -u pigeon -n 50

# View logs since service started
sudo journalctl -u pigeon --since today

# Follow logs in real-time
sudo journalctl -u pigeon -f
```

## Docker Deployment

### Build Docker Image

Create `Dockerfile` in pigeon root:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY . /app/
RUN pip install -e .

# Create app user
RUN useradd -m -u 1000 pigeon && \
    mkdir -p /app/inbox /app/inbox-archive && \
    chown -R pigeon:pigeon /app

USER pigeon

CMD ["pigeon", "start"]
```

### Build and Run

```bash
# Build image
docker build -t pigeon:latest .

# Run container
docker run -d \
  --name pigeon \
  --restart unless-stopped \
  -v ~/.config/google-personal-mcp:/home/pigeon/.config/google-personal-mcp \
  -e PIGEON_DRIVE_FOLDER="/Voice Recordings" \
  -e PIGEON_POLL_INTERVAL=60 \
  pigeon:latest

# View logs
docker logs -f pigeon

# Stop container
docker stop pigeon
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PIGEON_DRIVE_FOLDER` | `/Voice Recordings` | Google Drive folder to poll |
| `PIGEON_POLL_INTERVAL` | `60` | Polling interval in seconds |
| `PIGEON_GOOGLE_PROFILE` | `default` | Google auth profile name |
| `PIGEON_ENABLE_STT` | `true` | Enable speech-to-text processing |
| `PIGEON_ENABLE_PROFESSIONALIZE` | `true` | Enable text professionalization |
| `PIGEON_MELLONA_PROFILE` | `worker` | Mellona profile for LLM calls |
| `PIGEON_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `PIGEON_DEBUG` | `false` | Enable debug mode |
| `PIGEON_DRY_RUN` | `false` | Don't actually delete files |

### YAML Configuration

For advanced configuration, create `/etc/pigeon/config.yaml`:

```yaml
google:
  drive_folder: /Voice Recordings
  auth_profile: default

processing:
  enable_stt: true
  enable_professionalize: true
  mellona_profile: worker

polling:
  interval: 60
  timeout: 300

inbox:
  directory: /var/lib/pigeon/inbox
  archive_directory: /var/lib/pigeon/inbox-archive

logging:
  level: INFO
  file: /var/log/pigeon/pigeon.log
  max_size_mb: 100

debug:
  enabled: false
  dry_run: false
```

## Monitoring

### Health Check

```bash
# Check if service is running
sudo systemctl is-active pigeon

# Get detailed status
sudo systemctl status pigeon

# Check recent activity
sudo journalctl -u pigeon --since "1 hour ago"
```

### Log Analysis

```bash
# Count processed files
sudo journalctl -u pigeon | grep "Successfully downloaded" | wc -l

# View errors
sudo journalctl -u pigeon | grep ERROR

# Check polling activity
sudo journalctl -u pigeon | grep "poll"
```

### Metrics

Monitor these metrics in production:

1. **Files processed per day**: `journalctl -u pigeon | grep "downloaded" | wc -l`
2. **Error rate**: `journalctl -u pigeon | grep ERROR | wc -l`
3. **Disk usage**: `du -sh /var/lib/pigeon/inbox`
4. **Service uptime**: `systemctl show pigeon --property=ExecMainStartTimestamp`

### Alerts

Set up monitoring for:

- Service crashes (automatic restart via systemd)
- High error rates (check logs)
- Disk space issues (configure log rotation)
- Stuck processes (restart timer handles this)

## Troubleshooting

### Service Won't Start

```bash
# Check systemd status
sudo systemctl status pigeon

# View detailed logs
sudo journalctl -u pigeon -n 100

# Check permissions
ls -la /opt/pigeon
ls -la /var/lib/pigeon

# Verify user exists
id pigeon
```

### No Files Being Downloaded

```bash
# Check if service is running
sudo systemctl is-active pigeon

# Verify Google Drive folder
sudo -u pigeon pigeon status

# Check logs for errors
sudo journalctl -u pigeon -f

# Test authentication
cd /opt/pigeon && sudo -u pigeon pigeon start --verbose
```

### High Memory Usage

```bash
# Check current memory
ps aux | grep pigeon

# Restart service
sudo systemctl restart pigeon

# Increase memory limit in systemd
# Edit /etc/systemd/system/pigeon.service
# Change: MemoryLimit=512M to MemoryLimit=1G
sudo systemctl daemon-reload
sudo systemctl restart pigeon
```

### Disk Space Issues

```bash
# Check disk usage
du -sh /var/lib/pigeon/*

# Archive old files
find /var/lib/pigeon/inbox-archive -mtime +30 -type f -delete

# Set up log rotation
# Create /etc/logrotate.d/pigeon:
```

/var/log/pigeon/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 0640 pigeon pigeon
}
```

## Upgrades

### Update Pigeon

```bash
# Backup current configuration
sudo cp -r /etc/pigeon /etc/pigeon.backup

# Stop service
sudo systemctl stop pigeon

# Update code
cd /opt/pigeon
sudo git pull

# Reinstall package
sudo -u pigeon venv/bin/pip install -e .

# Start service
sudo systemctl start pigeon

# Verify update
sudo systemctl status pigeon
```

## Security

### File Permissions

```bash
# Correct permissions
sudo chown pigeon:pigeon /etc/pigeon/pigeon.env
sudo chmod 640 /etc/pigeon/pigeon.env

sudo chown pigeon:pigeon /var/log/pigeon/*.log
sudo chmod 640 /var/log/pigeon/*.log
```

### Credential Security

1. **Never commit credentials** to git
2. **Use environment variables** or secure config files
3. **Restrict permissions** on credential files
4. **Rotate credentials** regularly
5. **Use service accounts** rather than personal accounts when possible

### Network Security

1. Only allow outbound HTTPS connections
2. Use VPN if running on untrusted network
3. Monitor API quotas for abuse
4. Set up rate limiting

### SELinux (if enabled)

```bash
# Set SELinux context for pigeon directory
sudo semanage fcontext -a -t bin_t /opt/pigeon/venv/bin/pigeon
sudo restorecon -R /opt/pigeon

# Allow pigeon to access logs
sudo semanage fcontext -a -t admin_home_t "/home/pigeon(/.*)?"
sudo restorecon -R /home/pigeon
```

## Production Checklist

Before deploying to production:

- [ ] All credentials secured and not in git
- [ ] Systemd service file tested and working
- [ ] Logging configured and rotating
- [ ] Monitoring/alerting set up
- [ ] Backup procedure documented
- [ ] Disaster recovery plan in place
- [ ] Documentation updated
- [ ] Performance tested under expected load
- [ ] Error handling tested with API failures
- [ ] Team trained on operations

## Support

For issues:

1. Check logs: `sudo journalctl -u pigeon -f`
2. Review troubleshooting section above
3. Check README.md for usage documentation
4. Test in foreground mode: `sudo -u pigeon /opt/pigeon/venv/bin/pigeon start --verbose`

---

**Last Updated:** 2026-02-20
