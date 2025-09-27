#!/bin/bash

# Source the configuration file
source ../config.sh

# --- Functions ---

# Function to print log messages
log() {
    echo "[+] $1"
}

# Function to run nuclei for a specific category
run_nuclei() {
    local category=$1
    local templates_dir="/home/billi/Desktop/h1-automate/vulnScan/templates"
    local output_file="$OUTPUT_DIR/$TARGET_DOMAIN/nuclei_output_$category.txt"

    log "Running nuclei for category: $category"
    nuclei -l "$OUTPUT_DIR/$TARGET_DOMAIN/live_subdomains.txt" -t "$templates_dir/$category" -o "$output_file"
}

# --- Main Script ---

# Check if a category is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <category>"
    echo "Available categories:"
    echo "  - xss"
    echo "  - sqli"
    echo "  - command-injection"
    echo "  - path-traversal"
    echo "  - file-upload"
    echo "  - xxe"
    echo "  - broken-access-control"
    echo "  - cryptographic-failures"
    echo "  - injection"
    echo "  - insecure-design"
    echo "  - security-misconfiguration"
    echo "  - vulnerable-and-outdated-components"
    echo "  - identification-and-authentication-failures"
    echo "  - software-and-data-integrity-failures"
    echo "  - ssrf"
    exit 1
fi

# Run nuclei for the specified category
run_nuclei "$1"

log "Script finished."