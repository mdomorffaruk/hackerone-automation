#!/bin/bash
# start.sh

# Step 1: Setup virtual environment and install dependencies
python3 -m venv .venv
# Optional: Activate virtual environment (if you use one)
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Step 2: Ask if the user wants a fresh start by clearing previous results
read -p "Do you want a fresh start? (This will delete all previous results) (Y/N): " fresh_start
if [[ "$fresh_start" =~ ^[Yy]$ ]]; then
    echo "Clearing previous results..."
    rm -f all-domains.txt handles.txt all-subs.txt subdomainlist.txt
    rm -rf scopes subdomains
    echo "Previous results cleared."
fi

# Step 3: Check if scopes directory exists then ask user if they want to delete scopes and run the Python file for getting scope again
if [ -d "scopes" ]; then
    read -p "Scopes folder exists. Do you want to delete it and retrieve scopes again? (Y/N): " delete_scopes
    if [[ "$delete_scopes" =~ ^[Yy]$ ]]; then
        rm -rf scopes
        echo "Retrieving scopes again..."
        python3 get-h1-opportunity-list.py
    else
        echo "Skipping scope retrieval script."
    fi
else
    # Run the Python script if scopes directory does not exist
    echo "Running the Python script for generating HackerOne opportunity handles and getting their scopes..."
    python3 get-h1-opportunity-list.py
fi

# Step 4: Create or clear the all-domains.txt file
echo "Collecting all domains into all-domains.txt..."
> all-domains.txt  # Clear the file if it exists or create it if it doesn't

# Step 5: Extract valid domains from scopes files
for file in scopes/*_scopes.txt; do
    if [ -f "$file" ]; then
        # Extract valid domains excluding invalid entries
        grep -Eo '([a-zA-Z0-9-]+\.[a-zA-Z]{2,6}(\.[a-zA-Z]{2,6})?)' "$file" | sed 's/^\*\.//; s/^www\.//; s/https\?:\/\///; s/\/.*$//' | grep -v '^[a-zA-Z0-9-]*$' >> all-domains.txt
    fi
done

# Step 6: Remove duplicates in all-domains.txt
sort -u all-domains.txt -o all-domains.txt
echo "All valid domains collected in all-domains.txt."

# Step 7: Create a subdomains folder if it doesn't exist
mkdir -p subdomains

# Step 8: Create individual subdomains files for each domain
echo "Creating individual subdomains files..."
while read -r domain; do
    domain_file="subdomains/${domain//\//_}_subs.txt" # Replace slashes with underscores
    echo "$domain" > "$domain_file"  # Create the file and write the domain name to it
done < all-domains.txt

# Step 9: Run Subfinder for each domain and save to respective files
echo "Running Subfinder to gather subdomains for all domains..."
mkdir -p subdomains  # Create the subdomains directory if it doesn't exist

while read -r domain; do
    # Remove any existing output file for the domain
    output_file="subdomains/${domain}_subs.txt"
    
    # Run Subfinder for the current domain
    subfinder -d "$domain" -o "$output_file"
    
    echo "Subdomains for $domain saved to $output_file."
done < all-domains.txt

# # Combine all subdomain files into subdomainlist.txt
# echo "Combining all subdomain files into subdomainlist.txt..."
# cat subdomains/*_subs.txt > subdomainlist.txt
# echo "All subdomains saved to subdomainlist.txt."


# Step 10: Combine all subdomain files into subdomainlist.txt
echo "Combining all subdomain files into subdomainlist.txt..."
> subdomainlist.txt  # Clear the file if it exists or create it if it doesn't
for file in subdomains/*_subs.txt; do
    if [ -f "$file" ]; then
        cat "$file" >> subdomainlist.txt
    fi
done

# Step 11: Remove duplicates in subdomainlist.txt
sort -u subdomainlist.txt -o subdomainlist.txt
echo "All subdomains saved to subdomainlist.txt."

# Optional: Print the content of subdomainlist.txt
# cat subdomainlist.txt

# Step 12: Run Vuln Scans
sudo vulnScan/runAllScan.sh