
from modules.utils import run_tool, create_dir
import os

def run_nuclei_scan(target, config, output_dir):
    """
    Runs a Nuclei scan on the live subdomains.

    Args:
        target (str): The target domain.
        config (dict): The configuration dictionary.
        output_dir (str): The output directory.
    """
    print(f"[*] Running Nuclei scan for {target}...")
    recon_dir = os.path.join(output_dir, "recon")
    scan_dir = os.path.join(output_dir, "scan")
    create_dir(scan_dir)

    live_subdomains_file = os.path.join(recon_dir, "live_subdomains.txt")
    nuclei_output_file = os.path.join(scan_dir, "nuclei_output.txt")

    if not os.path.exists(live_subdomains_file):
        print("  [!] No live subdomains found. Skipping Nuclei scan.")
        return

    if config["tools"]["nuclei"]["enabled"]:
        print("  [-] Running Nuclei...")
        nuclei_flags = config["tools"]["nuclei"]["flags"]
        templates = " -t " + " -t ".join(config["tools"]["nuclei"]["templates"])
        run_tool(f"nuclei -l {live_subdomains_file} {templates} {nuclei_flags}", nuclei_output_file)

    print(f"[*] Nuclei scan complete. Results saved to {nuclei_output_file}")
