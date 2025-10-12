
from modules.utils import run_tool, create_dir
import os
import concurrent.futures

def enumerate_subdomains(target, config, output_dir, app, verbose=0):
    """
    Enumerates subdomains for a given target using threading.

    Args:
        target (str): The target domain.
        config (dict): The configuration dictionary.
        output_dir (str): The output directory.
        app (AutomateApp): The Textual app instance.
        verbose (int): The verbosity level.
    """
    recon_dir = os.path.join(output_dir, "recon")
    create_dir(recon_dir)

    all_subdomains_file = os.path.join(recon_dir, "all_subdomains.txt")
    subfinder_output_file = os.path.join(recon_dir, "subfinder.txt")
    assetfinder_output_file = os.path.join(recon_dir, "assetfinder.txt")
    amass_output_file = os.path.join(recon_dir, "amass.txt")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        if config["tools"]["subfinder"]["enabled"]:
            app.call_from_thread(app.add_tool_log, "subfinder")
            subfinder_flags = config["tools"]["subfinder"]["flags"]
            futures.append(executor.submit(run_tool, f"subfinder -d {target} {subfinder_flags}", subfinder_output_file, app, "subfinder", verbose))

        if config["tools"]["assetfinder"]["enabled"]:
            app.call_from_thread(app.add_tool_log, "assetfinder")
            assetfinder_flags = config["tools"]["assetfinder"]["flags"]
            futures.append(executor.submit(run_tool, f"assetfinder {assetfinder_flags} {target}", assetfinder_output_file, app, "assetfinder", verbose))

        if config["tools"]["amass"]["enabled"]:
            app.call_from_thread(app.add_tool_log, "amass")
            amass_flags = config["tools"]["amass"]["flags"]
            futures.append(executor.submit(run_tool, f"amass {amass_flags} -d {target} -o {amass_output_file}", app=app, tool_name="amass", verbose=verbose))

        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                app.call_from_thread(app.update_tool_log, "error", f"A tool failed to run: {e}")

    # Combine results
    all_subdomains = set()
    for f in [subfinder_output_file, assetfinder_output_file, amass_output_file]:
        if os.path.exists(f):
            with open(f, "r") as handle:
                all_subdomains.update(line.strip() for line in handle if line.strip())

    with open(all_subdomains_file, "w") as f:
        for subdomain in sorted(all_subdomains):
            f.write(subdomain + "\n")

def probe_subdomains(target, config, output_dir, app, verbose=0):
    """
    Probes subdomains to see which ones are live.

    Args:
        target (str): The target domain.
        config (dict): The configuration dictionary.
        output_dir (str): The output directory.
        app (AutomateApp): The Textual app instance.
        verbose (int): The verbosity level.
    """
    recon_dir = os.path.join(output_dir, "recon")
    all_subdomains_file = os.path.join(recon_dir, "all_subdomains.txt")
    live_subdomains_file = os.path.join(recon_dir, "live_subdomains.txt")

    if not os.path.exists(all_subdomains_file) or os.path.getsize(all_subdomains_file) == 0:
        return

    if config["tools"]["httpx"]["enabled"]:
        app.call_from_thread(app.add_tool_log, "httpx")
        httpx_flags = config["tools"]["httpx"]["flags"]
        run_tool(f"httpx -l {all_subdomains_file} {httpx_flags}", live_subdomains_file, app, "httpx", verbose)
