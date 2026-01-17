#!/bin/bash
#
# DICES Database Backup Script
#
# This script performs automated backups of the DICES database.
# It should be run via cron or systemd timer.
#
# Usage: ./scripts/backup.sh
#

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backups"
LOG_FILE="/var/log/dices_backup.log"
KEEP_BACKUPS=30  # Keep last 30 backups

# Email notification (optional - set to your email)
NOTIFY_EMAIL=""

# Timestamp for logging
timestamp() {
    date "+%Y-%m-%d %H:%M:%S"
}

# Logging function
log() {
    echo "[$(timestamp)] $1" | tee -a "$LOG_FILE"
}

# Error handler
handle_error() {
    log "ERROR: Backup failed at line $1"
    if [ -n "$NOTIFY_EMAIL" ]; then
        echo "DICES backup failed. Check $LOG_FILE for details." | \
            mail -s "DICES Backup Failed" "$NOTIFY_EMAIL"
    fi
    exit 1
}

trap 'handle_error $LINENO' ERR

# Main backup process
log "Starting DICES database backup"

# Change to project directory
cd "$PROJECT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    log "Activating virtual environment"
    source venv/bin/activate
elif [ -d ".venv" ]; then
    log "Activating virtual environment"
    source .venv/bin/activate
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Run backup command
log "Running backup command"
python manage.py backup_db \
    --backup-dir="$BACKUP_DIR" \
    --format=pg_dump \
    --keep-last=$KEEP_BACKUPS

# Check if backup was created
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/dices_db_*.sql.gz 2>/dev/null | head -1)
if [ -n "$LATEST_BACKUP" ]; then
    BACKUP_SIZE=$(du -h "$LATEST_BACKUP" | cut -f1)
    log "Backup completed successfully: $(basename "$LATEST_BACKUP") ($BACKUP_SIZE)"

    # Verify backup integrity (quick check)
    if gunzip -t "$LATEST_BACKUP" 2>/dev/null; then
        log "Backup integrity verified"
    else
        log "WARNING: Backup integrity check failed!"
        if [ -n "$NOTIFY_EMAIL" ]; then
            echo "DICES backup integrity check failed for $LATEST_BACKUP" | \
                mail -s "DICES Backup Warning" "$NOTIFY_EMAIL"
        fi
    fi
else
    log "ERROR: No backup file created"
    exit 1
fi

# Optional: Copy to off-site storage
# Uncomment and configure for your storage solution

# AWS S3 example:
# aws s3 cp "$LATEST_BACKUP" s3://your-bucket/dices-backups/

# rsync to another server example:
# rsync -avz "$LATEST_BACKUP" user@backup-server:/backups/dices/

log "Backup process completed"

exit 0
