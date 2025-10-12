from modules.utils import run_tool, create_dir
import os

def enumerate_subdomains(target, config, output_dir):
    """
    Enumerates subdomains for a given target.

    Args:
        target (str): The target domain.
        config (dict): The configuration dictionary.
        output_dir (str): The output directory.
    """
    print(f"[*] Enumerating subdomains for {target}...")
    recon_dir = os.path.join(output_dir, "recon")
    create_dir(recon_dir)

    all_subdomains_file = os.path.join(recon_dir, "all_subdomains.txt")
    subfinder_output_file = os.path.join(recon_dir, "subfinder.txt")
    assetfinder_output_file = os.path.join(recon_dir, "assetfinder.txt")
    amass_output_file = os.path.join(recon_dir, "amass.txt")

    # Run subfinder
    if config["tools"]["subfinder"]["enabled"]:
        print("  [-] Running subfinder...")
        subfinder_flags = config["tools"]["subfinder"]["flags"]
        run_tool(f"subfinder -d {target} {subfinder_flags}", subfinder_output_file)

    # Run assetfinder
    if config["tools"]["assetfinder"]["enabled"]:
        print("  [-] Running assetfinder...")
        assetfinder_flags = config["tools"]["assetfinder"]["flags"]
        run_tool(f"assetfinder {assetfinder_flags} {target}", assetfinder_output_file)

    # Run amass
    if config["tools"]["amass"]["enabled"]:
        print("  [-] Running amass...")
        amass_flags = config["tools"]["amass"]["flags"]
        run_tool(f"amass {amass_flags} -d {target} -o {amass_output_file}")

    # Combine results
    print("  [-] Combining results...")
    all_subdomains = set()
    for f in [subfinder_output_file, assetfinder_output_file, amass_output_file]:
        if os.path.exists(f):
            with open(f, "r") as handle:
                all_subdomains.update(line.strip() for line in handle)

    with open(all_subdomains_file, "w") as f:
        for subdomain in sorted(all_subdomains):
            f.write(subdomain + "\n")

    print(f"[*] Subdomain enumeration complete. Results saved to {all_subdomains_file}")

def probe_subdomains(target, config, output_dir):
    """
    Probes subdomains to see which ones are live.

    Args:
        target (str): The target domain.
        config (dict): The configuration dictionary.
        output_dir (str): The output directory.
    """
    print(f"[*] Probing subdomains for {target}...")
    recon_dir = os.path.join(output_dir, "recon")
    all_subdomains_file = os.path.join(recon_dir, "all_subdomains.txt")
    live_subdomains_file = os.path.join(recon_dir, "live_subdomains.txt")

    if not os.path.exists(all_subdomains_file):
        print("  [!] No subdomains found. Skipping probing.")
        return

    if config["tools"]["httpx"]["enabled"]:
        print("  [-] Running httpx...")
        httpx_flags = config["tools"]["httpx"]["flags"]
        run_tool(f"httpx -l {all_subdomains_file} {httpx_flags}", live_subdomains_file)

    print(f"[*] Probing complete. Live subdomains saved to {live_subdomains_file}")
