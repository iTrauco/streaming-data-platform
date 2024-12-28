#!/bin/bash

# Configuration
DURATION=30  # Test duration in seconds
TEST_FILE="/tmp/test_stream.flv"
LB_IP=$(cd ../terraform && terraform output -raw lb_ip_address)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
BOLD='\033[1m'

# Function to check if required tools are installed
check_requirements() {
    local missing_tools=()
    
    if ! command -v ffmpeg &> /dev/null; then
        missing_tools+=("ffmpeg")
    fi
    
    if ! command -v terraform &> /dev/null; then
        missing_tools+=("terraform")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        echo -e "${RED}Error: Missing required tools: ${missing_tools[*]}${NC}"
        echo "Please install the missing tools and try again."
        exit 1
    fi
}

# Create test video stream
create_test_stream() {
    echo -e "${YELLOW}Creating test video stream...${NC}"
    ffmpeg -f lavfi -i "testsrc=duration=$DURATION:size=1920x1080:rate=30" \
           -f lavfi -i "sine=frequency=1000:duration=$DURATION" \
           -c:v libx264 -b:v 3000k -preset ultrafast \
           -c:a aac -b:a 128k \
           -f flv $TEST_FILE
}

# Function to test RTMP connection
test_rtmp() {
    local rtmp_url="rtmp://$LB_IP/live"
    
    echo -e "\n${BOLD}Testing RTMP Stream${NC}"
    echo -e "RTMP URL: ${YELLOW}$rtmp_url${NC}"
    echo -e "Duration: ${DURATION} seconds"
    echo -e "Resolution: 1920x1080"
    echo -e "Video Bitrate: 3000k"
    echo -e "Audio Bitrate: 128k"
    
    # Start streaming
    echo -e "\n${YELLOW}Starting test stream...${NC}"
    ffmpeg -re -i $TEST_FILE \
           -c copy \
           -f flv "$rtmp_url" \
           2> >(grep -v "deprecated" >&2)
           
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Stream test completed successfully!${NC}"
    else
        echo -e "${RED}Stream test failed!${NC}"
        return 1
    fi
}

# Clean up
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    rm -f $TEST_FILE
}

# Main execution
echo -e "${BOLD}RTMP Stream Test Script${NC}"
echo "----------------------------------------"

# Check requirements
check_requirements

# Create test stream
create_test_stream

# Run test
test_rtmp
result=$?

# Cleanup
cleanup

# Exit with test result
exit $result