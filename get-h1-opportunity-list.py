import requests
from requests.auth import HTTPBasicAuth
import os

# Your HackerOne credentials
username = "mdomorffaruk"
api_key = "KMM3hTpSiiocZbQ/etVHPDd1mxBTevvSzPvQQkX1QhU="

# Create 'scopes' directory if it doesn't exist
os.makedirs("scopes", exist_ok=True)

# File to store all program handles
handles_file = "handles.txt"

# Prompt user for the number of programs to fetch
try:
    num_programs = int(input("Enter the number of programs to retrieve (1-100): "))
    if num_programs < 1 or num_programs > 100:
        raise ValueError("Number out of range. Please enter a number between 1 and 100.")
except ValueError as e:
    print(e)
    exit(1)

# Step 1: Get Programs List with user-defined page size
url_programs = "https://api.hackerone.com/v1/hackers/programs"
response = requests.get(
    url_programs,
    params={"page[size]": num_programs},
    auth=HTTPBasicAuth(username, api_key),
    headers={"Accept": "application/json"}
)

# Check for successful response
if response.status_code == 200:
    programs = response.json().get("data", [])
    
    # Step 2: Open handles.txt for writing
    with open(handles_file, "w") as handles:
        # Step 3: Loop through each program handle to get structured scopes
        for program in programs:
            handle = program["attributes"]["handle"]
            print(f"Checking scopes for program: {handle}")
            
            # Write handle to handles.txt
            handles.write(f"{handle}\n")
            
            # Step 4: Fetch the structured scopes for each program
            url_scopes = f"https://api.hackerone.com/v1/hackers/programs/{handle}/structured_scopes"
            scopes_response = requests.get(
                url_scopes,
                auth=HTTPBasicAuth(username, api_key),
                headers={"Accept": "application/json"}
            )
            
            # File to store scopes for each handle
            handle_scope_file = f"scopes/{handle}_scopes.txt"
            
            # Step 5: Open the specific handle's scope file for writing
            with open(handle_scope_file, "w") as scope_file:
                # Check if the scopes were successfully retrieved
                if scopes_response.status_code == 200:
                    scopes = scopes_response.json().get("data", [])
                    for scope in scopes:
                        attributes = scope["attributes"]
                        if attributes.get("eligible_for_bounty"):
                            # Write eligible scope to the handle's scope file
                            scope_file.write(f"{attributes['asset_identifier']}\n")
                else:
                    print(f"Failed to fetch scopes for {handle}, Status Code: {scopes_response.status_code}")
else:
    print(f"Failed to fetch programs, Status Code: {response.status_code}")
