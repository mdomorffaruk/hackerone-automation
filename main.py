import argparse
import sys
from pathlib import Path

from app import AutomateApp

__version__ = "0.5.0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"H1 Automation v{__version__} - realistic recon, enrichment, and manual test queue generation"
    )
    parser.add_argument("-t", "--target", help="Single target domain to run")
    parser.add_argument("-c", "--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="-v command logs, -vv live stdout")
    parser.add_argument("--recon", action="store_true", help="Run reconnaissance")
    parser.add_argument("--scan", action="store_true", help="Run scanning and enrichment")
    parser.add_argument("--report", action="store_true", help="Generate report from collected JSON")
    parser.add_argument("--all", action="store_true", help="Run recon + scan + report")
    parser.add_argument("--no-tui", action="store_true", help="Run without the Textual UI")
    parser.add_argument("--resume", action="store_true", help="Reuse existing JSON outputs when possible")
    parser.add_argument("--max-hosts", type=int, default=0, help="Optional limit for live hosts during active phases (0 = unlimited)")
    parser.add_argument("--max-urls", type=int, default=0, help="Optional limit for interesting URLs during active phases (0 = unlimited)")
    parser.add_argument("--max-archive-urls", type=int, default=2500, help="Limit archived URL ingestion per target")
    parser.add_argument("--max-reflection-tests", type=int, default=40, help="Limit lightweight reflection/diff tests")
    parser.add_argument(
        "--profile",
        choices=["safe", "normal", "aggressive"],
        default="safe",
        help="Execution profile. Safe is recommended for most bug bounty programs.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not any([args.recon, args.scan, args.report, args.all]):
        args.all = True

    config_path = Path(args.config)
    if not config_path.exists():
        parser.error(f"Config file not found: {config_path}")

    app = AutomateApp(args=args)
    try:
        app.run(headless=args.no_tui)
        return 0
    except KeyboardInterrupt:
        try:
            app.request_graceful_shutdown("Interrupted by user")
        except Exception:
            pass
        print("\n[!] Interrupted by user. Active child processes were asked to stop.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
