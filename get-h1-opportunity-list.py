import requests
import os
import argparse
from requests.auth import HTTPBasicAuth

def get_hackerone_opportunities(username, api_key, num_programs, output_dir):
    """
    Fetches HackerOne opportunities and their scopes.

    Args:
        username (str): Your HackerOne username.
        api_key (str): Your HackerOne API key.
        num_programs (int): The number of programs to retrieve.
        output_dir (str): The directory to save the output files.
    """

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Get the list of programs
    url_programs = "https://api.hackerone.com/v1/hackers/programs"
    try:
        response = requests.get(
            url_programs,
            params={"page[size]": num_programs},
            auth=HTTPBasicAuth(username, api_key),
            headers={"Accept": "application/json"}
        )
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"Error fetching programs: {e}")
        return

    programs = response.json().get("data", [])

    # Process each program
    for program in programs:
        handle = program["attributes"]["handle"]
        print(f"Checking scopes for program: {handle}")

        # Fetch the structured scopes for the program
        url_scopes = f"https://api.hackerone.com/v1/hackers/programs/{handle}/structured_scopes"
        try:
            scopes_response = requests.get(
                url_scopes,
                auth=HTTPBasicAuth(username, api_key),
                headers={"Accept": "application/json"}
            )
            scopes_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch scopes for {handle}: {e}")
            continue

        # Write the scopes to a file
        handle_scope_file = os.path.join(output_dir, f"{handle}_scopes.txt")
        with open(handle_scope_file, "w") as scope_file:
            scopes = scopes_response.json().get("data", [])
            for scope in scopes:
                attributes = scope["attributes"]
                if attributes.get("eligible_for_bounty"):
                    scope_file.write(f"{attributes['asset_identifier']}\n")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Fetch HackerOne opportunities and their scopes.")
    parser.add_argument("--num-programs", type=int, default=100, help="The number of programs to retrieve (1-100).")
    parser.add_argument("--output-dir", type=str, default="scopes", help="The directory to save the output files.")
    args = parser.parse_args()

    # Get credentials from environment variables
    username = os.environ.get("HACKERONE_USERNAME")
    api_key = os.environ.get("HACKERONE_API_KEY")

    if not username or not api_key:
        print("Error: HACKERONE_USERNAME and HACKERONE_API_KEY environment variables are not set.")
        exit(1)

    get_hackerone_opportunities(username, api_key, args.num_programs, args.output_dir)