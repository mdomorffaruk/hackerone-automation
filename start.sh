#!/bin/bash

# Source the configuration file
source config.sh

# --- Functions ---

# Function to print log messages
log() {
    echo "[+] $1"
}

# Function to check if a tool is installed
check_tool() {
    if ! [ -x "$(command -v $1)" ]; then
        echo "Error: $1 is not installed. Please run install.sh and try again." >&2
        exit 1
    fi
}

# Function to set up the environment
setup_environment() {
    log "Setting up virtual environment and installing dependencies..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
}

# Function to get the scope from HackerOne
get_scope() {
    log "Getting scope from HackerOne..."
    python3 get-h1-opportunity-list.py --h1-handle "$H1_PROGRAM_HANDLE"
}

# Function to enumerate subdomains
enumerate_subdomains() {
    log "Enumerating subdomains..."
    # Create a directory for the target domain
    for domain in "${TARGET_DOMAINS[@]}"; do
        mkdir -p "$OUTPUT_DIR/$domain"
        subfinder -d "$domain" -o "$OUTPUT_DIR/$domain/subfinder.txt"
        assetfinder --subs-only "$domain" | tee "$OUTPUT_DIR/$domain/assetfinder.txt"
        amass enum -d "$domain" -o "$OUTPUT_DIR/$domain/amass.txt"
        cat "$OUTPUT_DIR/$domain/subfinder.txt" "$OUTPUT_DIR/$domain/assetfinder.txt" "$OUTPUT_DIR/$domain/amass.txt" | sort -u > "$OUTPUT_DIR/$domain/all_subdomains.txt"
    done
}

# Function to probe subdomains
probe_subdomains() {
    log "Probing subdomains..."
    for domain in "${TARGET_DOMAINS[@]}"; do
        httpx -l "$OUTPUT_DIR/$domain/all_subdomains.txt" -o "$OUTPUT_DIR/$domain/live_subdomains.txt" -silent -no-color -follow-redirects -title -status-code -web-server
    done
}

# Function to perform a port scan
port_scan() {
    log "Performing port scan..."
    for domain in "${TARGET_DOMAINS[@]}"; do
        nmap -iL "$OUTPUT_DIR/$domain/live_subdomains.txt" -oN "$OUTPUT_DIR/$domain/nmap_scan.txt"
    done
}

# Function to identify the technology stack
tech_stack() {
    log "Identifying technology stack..."
    for domain in "${TARGET_DOMAINS[@]}"; do
        whatweb -i "$OUTPUT_DIR/$domain/live_subdomains.txt" --log-verbose "$OUTPUT_DIR/$domain/whatweb_output.txt"
    done
}

# Function to discover content
content_discovery() {
    log "Discovering content..."
    for domain in "${TARGET_DOMAINS[@]}"; do
        dirsearch -l "$OUTPUT_DIR/$domain/live_subdomains.txt" -o "$OUTPUT_DIR/$domain/dirsearch_output.txt" $DIRSEARCH_FLAGS
        gobuster dir -u "https://www.$domain" -w "$CONTENT_WORDLIST" -o "$OUTPUT_DIR/$domain/gobuster_output.txt" $GOBUSTER_FLAGS
    done
}

# Function to discover parameters
parameter_discovery() {
    log "Discovering parameters..."
    for domain in "${TARGET_DOMAINS[@]}"; do
        paramspider -d "$domain" -o "$OUTPUT_DIR/$domain/paramspider_output.txt"
    done
}

# Function for visual reconnaissance
visual_recon() {
    log "Performing visual reconnaissance..."
    for domain in "${TARGET_DOMAINS[@]}"; do
        gitleaks --repo-path="https://github.com/$domain" --report="$OUTPUT_DIR/$domain/gitleaks_report.json"
    done
}

# Function for JavaScript analysis
js_analysis() {
    log "Performing JavaScript analysis..."
    for domain in "${TARGET_DOMAINS[@]}"; do
        python3 /opt/LinkFinder/linkfinder.py -i "https://$domain" -o "$OUTPUT_DIR/$domain/linkfinder_output.html"
    done
}

# Function for Wayback Machine analysis
wayback_analysis() {
    log "Performing Wayback Machine analysis..."
    for domain in "${TARGET_DOMAINS[@]}"; do
        waybackurls "$domain" > "$OUTPUT_DIR/$domain/waybackurls.txt"
    done
}

# Function for favicon analysis
favicon_analysis() {
    log "Performing favicon analysis..."
    for domain in "${TARGET_DOMAINS[@]}"; do
        python3 /opt/FavFreak/favfreak.py -d "$domain" -o "$OUTPUT_DIR/$domain/favfreak_output.txt"
    done
}

# Function for dynamic analysis
dynamic_scan() {
    log "Performing dynamic analysis..."
    if [ "$SELENIUM_ENABLED" = true ]; then
        for domain in "${TARGET_DOMAINS[@]}"; do
            python3 dynamic_scan.py "https://$domain" --output-dir "$OUTPUT_DIR/$domain"
        done
    fi
}

# Function to run vulnerability scan
vulnerability_scan() {
    log "Running vulnerability scan..."
    for domain in "${TARGET_DOMAINS[@]}"; do
        nuclei -l "$OUTPUT_DIR/$domain/live_subdomains.txt" -o "$OUTPUT_DIR/$domain/nuclei_output.txt" $NUCLEI_FLAGS
    done
}

# --- Main Script ---

# Check if the required tools are installed
check_tool subfinder
check_tool assetfinder
check_tool amass
check_tool httpx
check_tool nuclei
check_tool nmap
check_tool whatweb
check_tool dirsearch
check_tool gobuster
check_tool paramspider
check_tool gitleaks
check_tool waybackurls

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --setup)
            setup_environment
            shift
            ;;
        --get-scope)
            get_scope
            shift
            ;;
        --enumerate)
            enumerate_subdomains
            shift
            ;;
        --probe)
            probe_subdomains
            shift
            ;;
        --portscan)
            port_scan
            shift
            ;;
        --tech-stack)
            tech_stack
            shift
            ;;
        --content-discovery)
            content_discovery
            shift
            ;;
        --parameter-discovery)
            parameter_discovery
            shift
            ;;
        --visual-recon)
            visual_recon
            shift
            ;;
        --js-analysis)
            js_analysis
            shift
            ;;
        --wayback-analysis)
            wayback_analysis
            shift
            ;;
        --favicon-analysis)
            favicon_analysis
            shift
            ;;
        --dynamic-scan)
            dynamic_scan
            shift
            ;;
        --scan)
            vulnerability_scan
            shift
            ;;
        --all)
            setup_environment
            get_scope
            enumerate_subdomains
            probe_subdomains
            port_scan
            tech_stack
            content_discovery
            parameter_discovery
            visual_recon
            js_analysis
            wayback_analysis
            favicon_analysis
            dynamic_scan
            vulnerability_scan
            shift
            ;;
        *)
            echo "Invalid option: $1" >&2
            exit 1
            ;;
    esac
done

log "Script finished."