
import os
from jinja2 import Environment, FileSystemLoader

def generate_report(target, config, output_dir):
    """
    Generates an HTML report of the findings.

    Args:
        target (str): The target domain.
        config (dict): The configuration dictionary.
        output_dir (str): The output directory.
    """
    print(f"[*] Generating report for {target}...")
    recon_dir = os.path.join(output_dir, "recon")
    scan_dir = os.path.join(output_dir, "scan")
    report_file = os.path.join(output_dir, "report.html")

    # Load data from files
    live_subdomains = []
    live_subdomains_file = os.path.join(recon_dir, "live_subdomains.txt")
    if os.path.exists(live_subdomains_file):
        with open(live_subdomains_file, "r") as f:
            live_subdomains = f.read().splitlines()

    nuclei_results = ""
    nuclei_output_file = os.path.join(scan_dir, "nuclei_output.txt")
    if os.path.exists(nuclei_output_file):
        with open(nuclei_output_file, "r") as f:
            nuclei_results = f.read()

    # Render the report
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("report_template.html")
    html = template.render(
        target=target,
        live_subdomains=live_subdomains,
        nuclei_results=nuclei_results
    )

    with open(report_file, "w") as f:
        f.write(html)

    print(f"[*] Report generated: {report_file}")
