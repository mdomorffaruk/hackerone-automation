#!/bin/bash

python3 -m venv .venv
# Optional: Activate virtual environment (if you use one)
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the Python script
echo "Running the Python script..."
python3 get-h1-hactivity-list.py