#!/bin/bash

# Check if Go is installed
if ! [ -x "$(command -v go)" ]; then
  echo "Error: Go is not installed. Please install Go and try again." >&2
  echo "Installation instructions: https://golang.org/doc/install" >&2
  exit 1
fi

# Check if the script is run as root
if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run as root to install nmap, whatweb, dirsearch, and gobuster." >&2
  exit 1
fi

echo "Installing tools..."

# Install tools with apt-get
apt-get update
apt-get install -y nmap whatweb dirsearch gobuster

# Install tools with go
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/tomnomnom/assetfinder@latest
go install -v github.com/owasp-amass/amass/v4/...@master
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install -v github.com/haccer/subjack@latest
go install -v github.com/lc/gau@latest
go install -v github.com/jaeles-project/gospider@latest
go install -v github.com/zricethezav/gitleaks/v8@latest
go install -v github.com/tomnomnom/waybackurls@latest

# Install tools with pip
pip3 install selenium browsermob-proxy paramspider

# Install tools from git
cd /opt
git clone https://github.com/GerbenJavado/LinkFinder.git
cd LinkFinder
pip3 install -r requirements.txt

cd /opt
git clone https://github.com/devanshbatham/FavFreak.git
cd FavFreak
pip3 install -r requirements.txt

echo "Installation complete."