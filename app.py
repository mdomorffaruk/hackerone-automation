from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Log
from textual.containers import Container
import yaml
import os
from modules.recon import enumerate_subdomains, probe_subdomains
from modules.scan import run_nuclei_scan
from modules.reporting import generate_report
from modules.utils import create_dir

class ToolOutput(Log):
    """A widget to display tool output."""
    pass

class AutomateApp(App):
    """A Textual app to manage the bug bounty automation framework."""

    CSS_PATH = "app.css"

    def __init__(self, args, **kwargs):
        super().__init__(**kwargs)
        self.args = args

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Container(id="tools")
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.run_worker(self.run_scan)

    def run_scan(self) -> None:
        """Runs the bug bounty scan."""
        # Load config
        with open(self.args.config, "r") as f:
            config = yaml.safe_load(f)

        # Get target
        target = self.args.target if self.args.target else config["scope"]["targets"][0]

        # Create output directory
        output_dir = os.path.join(config["output"]["directory"], target)
        create_dir(output_dir)

        if self.args.recon or self.args.all:
            self.call_from_thread(self.add_tool_log, "recon_tools")
            enumerate_subdomains(target, config, output_dir, self, self.args.verbose)
            probe_subdomains(target, config, output_dir, self, self.args.verbose)

        if self.args.scan or self.args.all:
            self.call_from_thread(self.add_tool_log, "scan_tools")
            run_nuclei_scan(target, config, output_dir, self, self.args.verbose)

        if self.args.report or self.args.all:
            generate_report(target, config, output_dir)

    def add_tool_log(self, tool_name: str) -> None:
        """Adds a new tool log to the UI."""
        new_log = ToolOutput(id=tool_name, classes="tool_output")
        self.query_one("#tools").mount(new_log)

    def update_tool_log(self, tool_name: str, content: str) -> None:
        """Updates the content of a tool log."""
        self.query_one(f"#{tool_name}").write(content)