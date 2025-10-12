
import argparse
import yaml
import os
from modules.recon import enumerate_subdomains, probe_subdomains
from modules.scan import run_nuclei_scan
from modules.reporting import generate_report
from modules.utils import create_dir

def main():
    parser = argparse.ArgumentParser(description="Bug Bounty Automation Framework")
    parser.add_argument("-t", "--target", help="The target domain to scan")
    parser.add_argument("-c", "--config", default="config.yaml", help="Path to the configuration file")
    parser.add_argument("--recon", action="store_true", help="Run the reconnaissance phase")
    parser.add_argument("--scan", action="store_true", help="Run the scanning phase")
    parser.add_argument("--report", action="store_true", help="Generate the report")
    parser.add_argument("--all", action="store_true", help="Run all phases")
    args = parser.parse_args()

    # Load config
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    # Get target
    target = args.target if args.target else config["scope"]["targets"][0]

    # Create output directory
    output_dir = os.path.join(config["output"]["directory"], target)
    create_dir(output_dir)

    if args.recon or args.all:
        enumerate_subdomains(target, config, output_dir)
        probe_subdomains(target, config, output_dir)

    if args.scan or args.all:
        run_nuclei_scan(target, config, output_dir)

    if args.report or args.all:
        generate_report(target, config, output_dir)

if __name__ == "__main__":
    main()
