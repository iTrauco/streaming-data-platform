#!/bin/bash

# Configuration
PROJECT_ID=$(gcloud config get-value project)
SECRET_NAME="stream-keys"
BACKUP_DIR="../backups/keys"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Backup current keys
echo "Backing up current stream keys..."
gcloud secrets versions access latest --secret=$SECRET_NAME > "$BACKUP_DIR/keys_$TIMESTAMP.json"

# Load new keys from secrets.env
if [ ! -f "../secrets.env" ]; then
    echo "Error: secrets.env not found"
    exit 1
fi

source ../secrets.env

# Create JSON payload for new keys
PAYLOAD=$(cat <<EOF
{
    "youtube": "$YOUTUBE_STREAM_KEY",
    "facebook": "$FACEBOOK_STREAM_KEY",
    "linkedin": "$LINKEDIN_STREAM_KEY",
    "twitch": "$TWITCH_STREAM_KEY"
}
EOF
)

# Update Secret Manager
echo "Updating stream keys in Secret Manager..."
echo "$PAYLOAD" | gcloud secrets versions add $SECRET_NAME --data-file=-

# Trigger instance refresh in managed instance group
echo "Refreshing instances to pick up new keys..."
gcloud compute instance-groups managed rolling-action replace stream-relay-mig \
    --max-unavailable 0 \
    --zone=REDACTED_ZONE

echo "Stream keys rotated successfully!"