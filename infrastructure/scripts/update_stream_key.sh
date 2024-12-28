#!/bin/bash

# Check if secrets.env exists
if [ ! -f "../secrets.env" ]; then
    echo "Error: secrets.env file not found"
    echo "Please create a secrets.env file with your stream keys in the format:"
    echo "YOUTUBE_STREAM_KEY=your_key"
    # echo "FACEBOOK_STREAM_KEY=your_key"
    # echo "LINKEDIN_STREAM_KEY=your_key"
    # echo "TWITCH_STREAM_KEY=your_key"
    exit 1
fi

# Source the secrets
source ../secrets.env

# Check if all required variables are set
REQUIRED_VARS=("YOUTUBE_STREAM_KEY")
# REQUIRED_VARS=("YOUTUBE_STREAM_KEY" "FACEBOOK_STREAM_KEY" "LINKEDIN_STREAM_KEY" "TWITCH_STREAM_KEY")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: $var is not set in secrets.env"
        exit 1
    fi
done

# Create JSON payload
PAYLOAD=$(cat <<EOF
{
    "youtube": "$YOUTUBE_STREAM_KEY"
}
EOF
)

# Update secret in Secret Manager
echo "Updating stream keys in Secret Manager..."
echo "$PAYLOAD" | gcloud secrets versions add stream-keys --data-file=-

if [ $? -eq 0 ]; then
    echo "Stream keys updated successfully!"
    echo "New instances will automatically pick up the new keys"
    echo "Existing instances will need to be refreshed"
else
    echo "Error: Failed to update stream keys"
    exit 1
fi