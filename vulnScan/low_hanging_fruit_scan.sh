#!/bin/bash
# low_hanging_fruit_scan.sh

# Check if subdomainlist.txt exists
if [ ! -f "subdomainlist.txt" ]; then
    echo "subdomainlist.txt not found! Please run the previous steps to generate it."
    exit 1
fi

# Step 1: Check for subdomain takeover vulnerabilities
echo "Checking for subdomain takeover vulnerabilities..."
nuclei -t /home/billi/nuclei-templates/http/takeovers/ -l subdomainlist.txt

echo "Subdomain takeover scan completed."
#!/bin/bash
# low_hanging_fruit_scan.sh

