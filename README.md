# HackerOne Automated bug bounty script


## Steps Overview

1. **Setup virtual environment and install dependencies**
2. **Ask if the user wants a fresh start by clearing previous results**
3. **Check if the scopes directory exists and ask the user if they want to delete it and retrieve scopes again**
4. **Create or clear the `all-domains.txt` file**
5. **Extract valid domains from scopes files**
6. **Remove duplicates in `all-domains.txt`**
7. **Check if `subdomainlist.txt` exists and ask for overwrite**
8. **Run Subfinder to gather subdomains**
9. **Store individual domain subdomains in their respective files**


**More steps will be added later**

## Usage

1. Clone the repository.
2. Navigate to the project directory.
3. Run the `start.sh` script:
   ```bash
   ./start.sh
