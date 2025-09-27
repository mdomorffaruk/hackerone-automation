#!/bin/bash

# Source the configuration file
source config.sh

# --- Functions ---

# Function to print log messages
log() {
    echo "[+] $1"
}

# --- Main Script ---

log "Starting the hunt..."

# Run the start.sh script in the background
./start.sh --all > /dev/null 2>&1 &

# Get the process ID of the start.sh script
pid=$!

# Wait for the start.sh script to finish and show a progress indicator
while kill -0 $pid 2> /dev/null; do
    echo -n "."
    sleep 5
done

echo ""
log "Hunt finished."

# Generate the HTML report
log "Generating HTML report..."

# Create the reporting directory if it doesn't exist
mkdir -p reporting

# Create the HTML report
cat <<EOF > reporting/report.html
<html>
<head>
<title>Bug Bounty Report</title>
</head>
<body>
<h1>Bug Bounty Report</h1>
EOF

for domain in "${TARGET_DOMAINS[@]}"; do
    echo "<h2>$domain</h2>" >> reporting/report.html
    echo "<h3>Subdomains</h3>" >> reporting/report.html
    echo "<pre>" >> reporting/report.html
    cat "$OUTPUT_DIR/$domain/all_subdomains.txt" >> reporting/report.html
    echo "</pre>" >> reporting/report.html

    echo "<h3>Live Subdomains</h3>" >> reporting/report.html
    echo "<pre>" >> reporting/report.html
    cat "$OUTPUT_DIR/$domain/live_subdomains.txt" >> reporting/report.html
    echo "</pre>" >> reporting/report.html

    echo "<h3>Nmap Scan</h3>" >> reporting/report.html
    echo "<pre>" >> reporting/report.html
    cat "$OUTPUT_DIR/$domain/nmap_scan.txt" >> reporting/report.html
    echo "</pre>" >> reporting/report.html

    echo "<h3>WhatWeb Output</h3>" >> reporting/report.html
    echo "<pre>" >> reporting/report.html
    cat "$OUTPUT_DIR/$domain/whatweb_output.txt" >> reporting/report.html
    echo "</pre>" >> reporting/report.html

    echo "<h3>Dirsearch Output</h3>" >> reporting/report.html
    echo "<pre>" >> reporting/report.html
    cat "$OUTPUT_DIR/$domain/dirsearch_output.txt" >> reporting/report.html
    echo "</pre>" >> reporting/report.html

    echo "<h3>Gobuster Output</h3>" >> reporting/report.html
    echo "<pre>" >> reporting/report.html
    cat "$OUTPUT_DIR/$domain/gobuster_output.txt" >> reporting/report.html
    echo "</pre>" >> reporting/report.html

    echo "<h3>Paramspider Output</h3>" >> reporting/report.html
    echo "<pre>" >> reporting/report.html
    cat "$OUTPUT_DIR/$domain/paramspider_output.txt" >> reporting/report.html
    echo "</pre>" >> reporting/report.html

    echo "<h3>Gitleaks Report</h3>" >> reporting/report.html
    echo "<pre>" >> reporting/report.html
    cat "$OUTPUT_DIR/$domain/gitleaks_report.json" >> reporting/report.html
    echo "</pre>" >> reporting/report.html

    echo "<h3>LinkFinder Output</h3>" >> reporting/report.html
    echo "<pre>" >> reporting/report.html
    cat "$OUTPUT_DIR/$domain/linkfinder_output.html" >> reporting/report.html
    echo "</pre>" >> reporting/report.html

    echo "<h3>Waybackurls</h3>" >> reporting/report.html
    echo "<pre>" >> reporting/report.html
    cat "$OUTPUT_DIR/$domain/waybackurls.txt" >> reporting/report.html
    echo "</pre>" >> reporting/report.html

    echo "<h3>FavFreak Output</h3>" >> reporting/report.html
    echo "<pre>" >> reporting/report.html
    cat "$OUTPUT_DIR/$domain/favfreak_output.txt" >> reporting/report.html
    echo "</pre>" >> reporting/report.html

    echo "<h3>Nuclei Output</h3>" >> reporting/report.html
    echo "<pre>" >> reporting/report.html
    cat "$OUTPUT_DIR/$domain/nuclei_output.txt" >> reporting/report.html
    echo "</pre>" >> reporting/report.html

done

cat <<EOF >> reporting/report.html
</body>
</html>
EOF

log "HTML report generated: reporting/report.html"
