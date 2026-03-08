from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

import yaml
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Log, Static
from textual.css.query import NoMatches
from textual._node_list import DuplicateIds

from modules.recon import run_recon_phase
from modules.scan import run_scan_phase
from modules.reporting import generate_report
from modules.utils import create_dir, ensure_json_file, expand_targets_from_config


class ToolOutput(Log):
    pass


class AutomateApp(App):
    CSS_PATH = "app.css"
    BINDINGS = [
        ("p", "toggle_pause", "Pause/Resume"),
        ("q", "request_quit", "Quit"),
    ]

    def __init__(self, args, **kwargs):
        super().__init__(**kwargs)
        self.args = args
        self.running_processes: Dict[str, List[Any]] = {}
        self.is_paused = False
        self.stop_requested = False
        self.status_widget: Static | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        self.status_widget = Static("Status: starting", id="status")
        yield self.status_widget
        yield Container(id="tools")
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self.run_pipeline, thread=True)

    def set_status(self, text: str) -> None:
        if self.status_widget:
            self.status_widget.update(text)

    def add_tool_log(self, tool_name: str) -> None:
        new_log = ToolOutput(id=tool_name, classes="tool_output")
        try:
            self.query_one("#tools").mount(new_log)
        except DuplicateIds:
            pass # Widget already exists, ignore

    def update_tool_log(self, tool_name: str, content: str) -> None:
        target = self.query_one(f"#{tool_name}", None)
        if target is None:
            self.add_tool_log(tool_name)
            target = self.query_one(f"#{tool_name}")
        if target:
            target.write(content)

    def action_toggle_pause(self) -> None:
        self.is_paused = not self.is_paused
        signal_name = "paused" if self.is_paused else "running"
        self.sub_title = signal_name.capitalize()
        self.set_status(f"Status: {signal_name}")

    def action_request_quit(self) -> None:
        self.request_graceful_shutdown("Quit requested from TUI")
        self.exit()

    def register_process(self, tool_name: str, process: Any) -> None:
        self.running_processes.setdefault(tool_name, []).append(process)

    def unregister_process(self, tool_name: str, process: Any) -> None:
        if tool_name not in self.running_processes:
            return
        self.running_processes[tool_name] = [p for p in self.running_processes[tool_name] if p is not process]
        if not self.running_processes[tool_name]:
            self.running_processes.pop(tool_name, None)

    def terminate_running_processes(self) -> None:
        for _, processes in list(self.running_processes.items()):
            for process in list(processes):
                try:
                    if process.poll() is None:
                        process.terminate()
                except Exception:
                    pass
        for _, processes in list(self.running_processes.items()):
            for process in list(processes):
                try:
                    if process.poll() is None:
                        process.kill()
                except Exception:
                    pass
        self.running_processes.clear()

    def request_graceful_shutdown(self, reason: str = "Stopping") -> None:
        self.stop_requested = True
        try:
            self.call_from_thread(self.add_tool_log, "lifecycle")
            self.call_from_thread(self.update_tool_log, "lifecycle", f"{reason}\n")
            self.call_from_thread(self.set_status, f"Status: stopping ({reason})")
        except Exception:
            pass
        self.terminate_running_processes()

    def _load_config(self) -> Dict[str, Any]:
        with open(self.args.config, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)

    def _initialise_target_state(self, output_dir: Path, target: str) -> None:
        create_dir(output_dir)
        ensure_json_file(
            output_dir / "run_metadata.json",
            {
                "target": target,
                "config_path": os.path.abspath(self.args.config),
                "resume": bool(self.args.resume),
                "verbose": self.args.verbose,
                "profile": self.args.profile,
            },
        )

    def run_pipeline(self) -> None:
        try:
            config = self._load_config()
            targets = [self.args.target] if self.args.target else expand_targets_from_config(config)
            if not targets:
                raise RuntimeError("No target found. Set --target or scope.targets in config.yaml")

            base_output = Path(config["output"]["directory"])
            for target in targets:
                if self.stop_requested:
                    break
                target_output = base_output / target
                self._initialise_target_state(target_output, target)
                self.call_from_thread(self.set_status, f"Status: working on {target}")

                if self.args.recon or self.args.all:
                    run_recon_phase(target, config, target_output, self, self.args)

                if self.stop_requested:
                    break

                if self.args.scan or self.args.all:
                    run_scan_phase(target, config, target_output, self, self.args)

                if self.stop_requested:
                    break

                if self.args.report or self.args.all:
                    generate_report(target, config, target_output)

            final_status = "stopped" if self.stop_requested else "finished"
            self.call_from_thread(self.set_status, f"Status: {final_status}")
        except Exception as exc:
            self.call_from_thread(self.add_tool_log, "error")
            self.call_from_thread(self.update_tool_log, "error", f"{exc}\n")
            self.call_from_thread(self.set_status, "Status: failed")
            raise
        finally:
            self.terminate_running_processes()
