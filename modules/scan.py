
from modules.utils import run_tool, create_dir
import os

def run_nuclei_scan(target, config, output_dir, app, verbose=0):
    """
    Runs a Nuclei scan on the live subdomains.

    Args:
        target (str): The target domain.
        config (dict): The configuration dictionary.
        output_dir (str): The output directory.
        app (AutomateApp): The Textual app instance.
        verbose (int): The verbosity level.
    """
    scan_dir = os.path.join(output_dir, "scan")
    create_dir(scan_dir)

    live_subdomains_file = os.path.join(output_dir, "recon", "live_subdomains.txt")
    nuclei_output_file = os.path.join(scan_dir, "nuclei_output.txt")

    if not os.path.exists(live_subdomains_file) or os.path.getsize(live_subdomains_file) == 0:
        return

    if config["tools"]["nuclei"]["enabled"]:
        app.call_from_thread(app.add_tool_log, "nuclei")
        nuclei_flags = config["tools"]["nuclei"]["flags"]
        templates = " -t " + " -t ".join(config["tools"]["nuclei"]["templates"])
        run_tool(f"nuclei -l {live_subdomains_file} {templates} {nuclei_flags}", nuclei_output_file, app, "nuclei", verbose)
