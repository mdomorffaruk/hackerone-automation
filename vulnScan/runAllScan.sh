#!/bin/bash

# Source the configuration file
source ../config.sh

# --- Main Script ---

# Run the scanner for each category
/home/billi/Desktop/h1-automate/vulnScan/scan.sh xss
/home/billi/Desktop/h1-automate/vulnScan/scan.sh sqli
/home/billi/Desktop/h1-automate/vulnScan/scan.sh command-injection
/home/billi/Desktop/h1-automate/vulnScan/scan.sh path-traversal
/home/billi/Desktop/h1-automate/vulnScan/scan.sh file-upload
/home/billi/Desktop/h1-automate/vulnScan/scan.sh xxe
/home/billi/Desktop/h1-automate/vulnScan/scan.sh broken-access-control
/home/billi/Desktop/h1-automate/vulnScan/scan.sh cryptographic-failures
/home/billi/Desktop/h1-automate/vulnScan/scan.sh injection
/home/billi/Desktop/h1-automate/vulnScan/scan.sh insecure-design
/home/billi/Desktop/h1-automate/vulnScan/scan.sh security-misconfiguration
/home/billi/Desktop/h1-automate/vulnScan/scan.sh vulnerable-and-outdated-components
/home/billi/Desktop/h1-automate/vulnScan/scan.sh identification-and-authentication-failures
/home/billi/Desktop/h1-automate/vulnScan/scan.sh software-and-data-integrity-failures
/home/billi/Desktop/h1-automate/vulnScan/scan.sh ssrf
