
# Bug Bounty Automation Framework

This is a Python-based framework for automating bug bounty hunting tasks. It is designed to be modular, configurable, and extensible.

## Directory Structure

```
.
├── config.yaml
├── main.py
├── modules/
│   ├── recon.py
│   ├── scan.py
│   ├── reporting.py
│   └── utils.py
├── templates/
│   └── report_template.html
├── wordlists/
│   ├── subdomains.txt
│   └── content.txt
├── output/
└── requirements.txt
```

## Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Python dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Install external tools:**

    The framework uses several external tools. You need to install them and make sure they are in your PATH.

    *   [subfinder](https://github.com/projectdiscovery/subfinder)
    *   [assetfinder](https://github.com/tomnomnom/assetfinder)
    *   [amass](https://github.com/owasp-amass/amass)
    *   [httpx](https://github.com/projectdiscovery/httpx)
    *   [nuclei](https://github.com/projectdiscovery/nuclei)
    *   [nmap](https://nmap.org/)
    *   [whatweb](https://github.com/urbanadventurer/WhatWeb)
    *   [dirsearch](https://github.com/maurosoria/dirsearch)
    *   [gobuster](https://github.com/OJ/gobuster)

## Configuration

Configuration is done through the `config.yaml` file.

*   **`scope`**: Define your target domains and any out-of-scope domains.
*   **`wordlists`**: Set the paths to your wordlists.
*   **`tools`**: Enable or disable tools and customize their flags.
*   **`api_keys`**: Add any API keys you want to use.

## Usage

Make sure you have activated the virtual environment:

```bash
source .venv/bin/activate
```

Then, you can run the `main.py` script with the following options:

*   **Run all phases for a target:**

    ```bash
    python main.py --target example.com --all
    ```

*   **Run only the reconnaissance phase:**

    ```bash
    python main.py --target example.com --recon
    ```

*   **Run only the scanning phase:**

    ```bash
    python main.py --target example.com --scan
    ```

*   **Generate a report:**

    ```bash
    python main.py --target example.com --report
    ```

The output of the scans will be saved in the `output/` directory, organized by target.

## Disclaimer

This toolkit is for educational purposes only. Use it at your own risk. The author is not responsible for any misuse or damage caused by this toolkit.
