#!/bin/bash

python3 -m venv .venv
# Optional: Activate virtual environment (if you use one)
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if scopes directory exists
if [ -d "scopes" ]; then
    echo "Scopes folder exists. Skipping the scope retrieval script."

else
    # Run the Python script if scopes directory does not exist
    echo "Running the Python script for generating 100 hackerone opportunity handle and get thier scopes..."
    python3 get-h1-opportunity-list.py
fi


# Create or clear the all-domains.txt file
echo "Collecting all domains into all-domains.txt..."
> all-domains.txt  # Clear the file if it exists or create it if it doesn't

# Loop through each file in the scopes directory and extract valid domains
for file in scopes/*_scopes.txt; do
    if [ -f "$file" ]; then
        # Extract valid domains excluding invalid entries
        grep -Eo '([a-zA-Z0-9-]+\.[a-zA-Z]{2,6}(\.[a-zA-Z]{2,6})?)' "$file" | sed 's/^\*\.//; s/^www\.//; s/https\?:\/\///; s/\/.*$//' | grep -v '^[a-zA-Z0-9-]*$' >> all-domains.txt
    fi
done


# Remove duplicates by using sort and uniq
sort -u all-domains.txt -o all-domains.txt

echo "All valid domains collected in all-domains.txt."