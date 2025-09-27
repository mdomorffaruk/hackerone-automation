# HackerOne Automated Bug Bounty Toolkit

This toolkit provides a set of scripts to automate the process of reconnaissance and vulnerability scanning for bug bounty hunters.

## Features

- **Automated Tool Installation:** A simple script to install all the necessary tools.
- **Centralized Configuration:** A single configuration file to manage your target and other settings.
- **Modular Scripts:** Scripts are broken down into smaller, reusable functions.
- **OWASP Top 10 Scanning:** The toolkit includes a script to scan for the OWASP Top 10 vulnerabilities using Nuclei.
- **HackerOne Integration:** A script to fetch scopes from HackerOne programs.

## Directory Structure

```
.
├── config.sh
├── get-h1-opportunity-list.py
├── install.sh
├── output
├── README.md
├── requirements.txt
├── start.sh
└── vulnScan
    ├── download-templates.sh
    ├── runAllScan.sh
    ├── scan.sh
    └── templates
```

## Usage

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/h1-automate.git
   cd h1-automate
   ```

2. **Install the required tools:**

   ```bash
   ./install.sh
   ```

3. **Configure your target:**

   Edit the `config.sh` file to set your target domain and other options.

4. **Set your HackerOne credentials:**

   ```bash
   export HACKERONE_USERNAME="your-username"
   export HACKERONE_API_KEY="your-api-key"
   ```

5. **Run the automation script:**

   The `start.sh` script provides several options to run the different stages of the process:

   ```bash
   # Run all stages
   ./start.sh --all

   # Run individual stages
   ./start.sh --setup
   ./start.sh --get-scope
   ./start.sh --enumerate
   ./start.sh --probe
   ./start.sh --scan
   ```

6. **Run the vulnerability scanner:**

   The `vulnScan/runAllScan.sh` script runs the vulnerability scanner for all the OWASP Top 10 categories.

   ```bash
   ./vulnScan/runAllScan.sh
   ```

   You can also run the scanner for a specific category:

   ```bash
   ./vulnScan/scan.sh <category>
   ```

## Disclaimer

This toolkit is for educational purposes only. Use it at your own risk. The author is not responsible for any misuse or damage caused by this toolkit.