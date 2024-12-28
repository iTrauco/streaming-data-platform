#!/bin/bash

# Configuration
PROJECT_ID=$(gcloud config get-value project)
REGION="us-east1"
ZONE="${REGION}-b"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to log with timestamp
log() {
    local level=$1
    local message=$2
    local color=$3
    echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] ${message}${NC}"
}

# Function to confirm action
confirm() {
    read -p "Are you sure you want to proceed with cleanup? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "INFO" "Cleanup cancelled" "$YELLOW"
        exit 1
    fi
}

# Check if running in terraform directory
if [ ! -f "../terraform/main.tf" ]; then
    log "ERROR" "Please run this script from the scripts directory" "$RED"
    exit 1
fi

# Confirmation
log "WARNING" "This script will destroy all resources created for the streaming infrastructure" "$YELLOW"
log "WARNING" "Including: Load Balancer, Instance Groups, Network, and Secrets" "$YELLOW"
confirm

# Cleanup steps
log "INFO" "Starting cleanup process..." "$YELLOW"

# 1. Terraform destroy
log "INFO" "Running terraform destroy..." "$YELLOW"
(cd ../terraform && terraform destroy -auto-approve)
if [ $? -ne 0 ]; then
    log "ERROR" "Terraform destroy failed" "$RED"
    exit 1
fi

# 2. Delete container images
log "INFO" "Deleting container images from GCR..." "$YELLOW"
for digest in $(gcloud container images list-tags gcr.io/${PROJECT_ID}/stream-relay --format='get(digest)'); do
    gcloud container images delete "gcr.io/${PROJECT_ID}/stream-relay@${digest}" --quiet
done

# 3. Clean local files
log "INFO" "Cleaning local files..." "$YELLOW"
rm -rf \
    ../logs/* \
    ../metrics/* \
    ../terraform/.terraform \
    ../terraform/.terraform.lock.hcl \
    ../terraform/terraform.tfstate* \
    /tmp/test_stream.flv

# 4. Remove service account keys if any
log "INFO" "Removing service account keys..." "$YELLOW"
if [ -f "../terraform/credentials.json" ]; then
    rm ../terraform/credentials.json
fi

# 5. Check for any remaining resources
log "INFO" "Checking for any remaining resources..." "$YELLOW"

# Check for instances
INSTANCES=$(gcloud compute instances list --filter="name~stream-relay" --format="value(name)")
if [ ! -z "$INSTANCES" ]; then
    log "WARNING" "Found remaining instances, attempting to delete..." "$YELLOW"
    echo "$INSTANCES" | while read instance; do
        gcloud compute instances delete $instance --zone=$ZONE --quiet
    done
fi

# Check for firewall rules
FW_RULES=$(gcloud compute firewall-rules list --filter="name~stream" --format="value(name)")
if [ ! -z "$FW_RULES" ]; then
    log "WARNING" "Found remaining firewall rules, attempting to delete..." "$YELLOW"
    echo "$FW_RULES" | while read rule; do
        gcloud compute firewall-rules delete $rule --quiet
    done
fi

# Final status
if [ $? -eq 0 ]; then
    log "SUCCESS" "Cleanup completed successfully" "$GREEN"
    echo -e "\n${GREEN}All resources have been cleaned up successfully!${NC}"
else
    log "ERROR" "Cleanup completed with some errors" "$RED"
    echo -e "\n${RED}Some resources may need manual cleanup. Please check the logs.${NC}"
fi