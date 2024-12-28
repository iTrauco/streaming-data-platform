#!/bin/bash

# Configuration
METRICS_DIR="../metrics"
INSTANCE_GROUP="stream-relay-mig"
ZONE="us-east1-b"

# Create metrics directory if it doesn't exist
mkdir -p $METRICS_DIR

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to collect instance metrics
collect_instance_metrics() {
    local instance=$1
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local output_file="$METRICS_DIR/${instance}_${timestamp}.json"
    
    echo -e "${BLUE}Collecting metrics for instance: ${instance}${NC}"
    
    # Get instance metrics
    gcloud compute instances describe $instance \
        --zone=$ZONE \
        --format="json(name,status,cpuPlatform,machineType,networkInterfaces[0].networkIP)" \
        > $output_file
        
    # Get NGINX metrics via SSH
    gcloud compute ssh $instance --zone=$ZONE --command="
        echo '=== NGINX Status ==='
        curl -s http://localhost/status
        echo '=== RTMP Statistics ==='
        curl -s http://localhost/rtmp_stat
        echo '=== System Resources ==='
        top -bn1 | head -n 5
        echo '=== Memory Usage ==='
        free -m
        echo '=== Disk Usage ==='
        df -h
        echo '=== Network Connections ==='
        netstat -an | grep :1935 | wc -l
    " >> ${output_file}.txt 2>/dev/null
}

# Function to collect load balancer metrics
collect_lb_metrics() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local output_file="$METRICS_DIR/lb_metrics_${timestamp}.json"
    
    echo -e "${BLUE}Collecting load balancer metrics${NC}"
    
    # Get load balancer health status
    gcloud compute backend-services get-health stream-backend \
        --global \
        --format=json > $output_file
}

# Function to analyze metrics
analyze_metrics() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local report_file="$METRICS_DIR/analysis_${timestamp}.txt"
    
    echo -e "${YELLOW}Analyzing metrics...${NC}"
    
    echo "Stream Infrastructure Analysis Report" > $report_file
    echo "Generated at: $(date)" >> $report_file
    echo "----------------------------------------" >> $report_file
    
    # Analyze instance metrics
    echo "Instance Status:" >> $report_file
    for instance in $(gcloud compute instance-groups managed list-instances $INSTANCE_GROUP \
        --zone=$ZONE --format="value(instance)"); do
        
        local status=$(gcloud compute instances describe $instance \
            --zone=$ZONE --format="value(status)")
        echo "- $instance: $status" >> $report_file
        
        # Check NGINX status
        local nginx_status=$(gcloud compute ssh $instance --zone=$ZONE \
            --command="systemctl is-active nginx" 2>/dev/null)
        echo "  NGINX: $nginx_status" >> $report_file
        
        # Get active connections
        local connections=$(gcloud compute ssh $instance --zone=$ZONE \
            --command="netstat -an | grep :1935 | wc -l" 2>/dev/null)
        echo "  Active RTMP Connections: $connections" >> $report_file
    done
    
    # Display the report
    cat $report_file
}

# Main execution
echo -e "${YELLOW}Starting metrics collection...${NC}"

# Get all instances in the managed instance group
instances=$(gcloud compute instance-groups managed list-instances $INSTANCE_GROUP \
    --zone=$ZONE --format="value(instance)")

# Collect metrics for each instance
for instance in $instances; do
    collect_instance_metrics $instance
done

# Collect load balancer metrics
collect_lb_metrics

# Analyze metrics
analyze_metrics

echo -e "${GREEN}Metrics collection complete!${NC}"
echo -e "Metrics stored in: ${BLUE}$METRICS_DIR${NC}"