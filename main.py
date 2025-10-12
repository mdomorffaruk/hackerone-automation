import argparse
from app import AutomateApp

__version__ = "0.3.0"

def main():
    parser = argparse.ArgumentParser(description=f"Bug Bounty Automation Framework v{__version__}")
    parser.add_argument("-t", "--target", help="The target domain to scan")
    parser.add_argument("-c", "--config", default="config.yaml", help="Path to the configuration file")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbosity level (-v for info, -vv for live data)")
    parser.add_argument("--recon", action="store_true", help="Run the reconnaissance phase")
    parser.add_argument("--scan", action="store_true", help="Run the scanning phase")
    parser.add_argument("--report", action="store_true", help="Generate the report")
    parser.add_argument("--all", action="store_true", help="Run all phases")
    args = parser.parse_args()

    app = AutomateApp(args=args)
    app.run()

if __name__ == "__main__":
    main()