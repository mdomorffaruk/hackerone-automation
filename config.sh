#!/bin/bash

# --- Target Scope ---

# Target domains (space-separated)
TARGET_DOMAINS=("example.com" "another-example.com")

# Out-of-scope domains (space-separated)
OUT_OF_SCOPE_DOMAINS=("*.example.com" "private.another-example.com")

# HackerOne program handle (optional)
H1_PROGRAM_HANDLE=""

# --- Wordlists ---

# Subdomain brute-forcing wordlist
SUBDOMAIN_WORDLIST="/usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt"

# Content discovery wordlist
CONTENT_WORDLIST="/usr/share/wordlists/seclists/Discovery/Web-Content/common.txt"

# --- Tool Flags ---

# Nuclei flags
NUCLEI_FLAGS="-silent -c 50"

# Dirsearch flags
DIRSEARCH_FLAGS="-e php,html,js,asp,aspx,jsp,txt,bak,old,zip,rar,7z,sql,db,sqlite,git,svn,hg,DS_Store -t 50"

# Gobuster flags
GOBUSTER_FLAGS="-t 50"

# --- Selenium ---

# Enable/disable Selenium-based crawling
SELENIUM_ENABLED=false

# Path to the browsermob-proxy binary
BROWSERMOB_PROXY_PATH="/path/to/browsermob-proxy-2.1.4/bin/browsermob-proxy"

# --- Output ---

# Output directory
OUTPUT_DIR="/home/billi/Desktop/h1-automate/output"

# --- Threads ---

# Number of threads to use
THREADS=10
