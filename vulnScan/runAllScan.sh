#!/bin/bash
# runAllScan.sh

# Step 1: Run OWASP Top 10 Vulnerability Scans
echo "Running OWASP Top 10 Vulnerability Scans..."
for script in owasp_top_10/*.sh; do
    if [ -f "$script" ]; then
        echo "Executing $script..."
        bash "$script"
    else
        echo "No OWASP Top 10 scripts found."
    fi
done

# Step 2: Run Low Hanging Fruit Scan
echo "Running Low Hanging Fruit Vulnerability Scans..."
bash low_hanging_fruit_scan.sh

# Optional: Indicate completion
echo "All vulnerability scans completed."
