from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

import yaml

try:
    from textual.app import App, ComposeResult
    from textual.containers import Container
    from textual.widgets import Footer, Header, Log, Static
    from textual._node_list import DuplicateIds
    from textual.css.query import NoMatches
    TEXTUAL_AVAILABLE = True
except ModuleNotFoundError:
    App = object  # type: ignore
    ComposeResult = object  # type: ignore
    Container = object  # type: ignore
    Footer = object  # type: ignore
    Header = object  # type: ignore
    Log = object  # type: ignore
    Static = object  # type: ignore
    DuplicateIds = Exception  # type: ignore
    NoMatches = Exception  # type: ignore
    TEXTUAL_AVAILABLE = False

from modules.recon import run_recon_phase
from modules.reporting import generate_report
from modules.scan import run_scan_phase
from modules.utils import apply_profile, create_dir, ensure_json_file, expand_targets_from_config, log_message


class ToolOutput(Log):
    pass


class ConsoleApp:
    def __init__(self, args):
        self.args = args
        self.running_processes: Dict[str, List[Any]] = {}
        self.is_paused = False
        self.stop_requested = False

    def add_tool_log(self, tool_name: str) -> None:
        return None

    def update_tool_log(self, tool_name: str, content: str) -> None:
        log_message(None, tool_name, content)

    def call_from_thread(self, fn, *args, **kwargs):
        return fn(*args, **kwargs)

    def set_status(self, text: str) -> None:
        print(text)

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
        print(f"[lifecycle] {reason}")
        self.terminate_running_processes()


if TEXTUAL_AVAILABLE:
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
                pass

        def update_tool_log(self, tool_name: str, content: str) -> None:
            try:
                target = self.query_one(f"#{tool_name}")
            except NoMatches:
                self.add_tool_log(tool_name)
                target = self.query_one(f"#{tool_name}")
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

        def run_pipeline(self) -> None:
            run_pipeline(self, self.args)
else:
    class AutomateApp:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Textual is not installed. Use --no-tui or install requirements.txt")


def run_pipeline(app, args) -> None:
    try:
        with open(args.config, "r", encoding="utf-8") as handle:
            raw_config = yaml.safe_load(handle)
        config = apply_profile(raw_config, args.profile)
        targets = [args.target] if args.target else expand_targets_from_config(config)
        if not targets:
            raise RuntimeError("No target found. Set --target or scope.targets in config.yaml")

        base_output = Path(config["output"]["directory"])
        for target in targets:
            if app.stop_requested:
                break

            target_output = base_output / target
            create_dir(target_output)
            ensure_json_file(
                target_output / "run_metadata.json",
                {
                    "target": target,
                    "config_path": os.path.abspath(args.config),
                    "resume": bool(args.resume),
                    "verbose": args.verbose,
                    "profile": args.profile,
                },
            )

            app.call_from_thread(app.set_status, f"Status: working on {target}")

            if args.recon or args.all:
                app.call_from_thread(app.set_status, f"Status: recon on {target}")
                run_recon_phase(target, config, target_output, app, args)

            if app.stop_requested:
                break

            if args.scan or args.all:
                app.call_from_thread(app.set_status, f"Status: scan on {target}")
                run_scan_phase(target, config, target_output, app, args)

            if app.stop_requested:
                break

            if args.report or args.all:
                app.call_from_thread(app.set_status, f"Status: report on {target}")
                generate_report(target, config, target_output)

        final_status = "stopped" if app.stop_requested else "finished"
        app.call_from_thread(app.set_status, f"Status: {final_status}")
    except Exception as exc:
        app.call_from_thread(app.add_tool_log, "error")
        app.call_from_thread(app.update_tool_log, "error", f"{exc}\n")
        app.call_from_thread(app.set_status, "Status: failed")
        raise
    finally:
        app.terminate_running_processes()


def run_headless(args) -> int:
    app = ConsoleApp(args)
    try:
        run_pipeline(app, args)
        return 0 if not app.stop_requested else 130
    except KeyboardInterrupt:
        app.request_graceful_shutdown("Interrupted by user")
        print("\n[!] Interrupted by user. Active child processes were asked to stop.")
        return 130
