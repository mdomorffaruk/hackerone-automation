from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def create_dir(directory: str | Path) -> None:
    Path(directory).mkdir(parents=True, exist_ok=True)


def ensure_json_file(path: str | Path, default: Any) -> None:
    path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(default, handle, indent=2)


def read_json(path: str | Path, default: Any = None) -> Any:
    path = Path(path)
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def append_jsonl(path: str | Path, rows: Iterable[Dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def tool_exists(name: str) -> bool:
    return shutil.which(name) is not None


def log_message(app, tool_name: str, message: str) -> None:
    if app and hasattr(app, "call_from_thread"):
        app.call_from_thread(app.add_tool_log, tool_name)
        app.call_from_thread(app.update_tool_log, tool_name, message)
        return

    prefix = f"[{tool_name}] " if tool_name else ""
    for line in str(message).splitlines(True):
        print(prefix + line, end="")


def wait_if_paused(app) -> None:
    while app and getattr(app, "is_paused", False) and not getattr(app, "stop_requested", False):
        time.sleep(0.25)


def apply_profile(config: Dict[str, Any], profile_name: str) -> Dict[str, Any]:
    profiles = config.get("profiles", {})
    profile = profiles.get(profile_name, {})
    if not profile:
        return config

    merged = json.loads(json.dumps(config))
    merged["global_delay"] = profile.get("global_delay", merged.get("global_delay", 0))
    merged["threads"] = profile.get("threads", merged.get("threads", 4))
    for tool_name, values in profile.get("tools", {}).items():
        if tool_name not in merged.get("tools", {}):
            continue
        merged["tools"][tool_name].update(values)
    return merged


def _merge_env(env: Optional[Dict[str, str]]) -> Dict[str, str]:
    merged = os.environ.copy()
    merged.setdefault("PYTHONUNBUFFERED", "1")
    merged.setdefault("COLUMNS", "160")
    if env:
        merged.update(env)
    return merged


def run_tool(
    command: str | List[str],
    *,
    output_file: str | Path | None = None,
    json_output: bool = False,
    app=None,
    tool_name: str | None = None,
    verbose: int = 0,
    delay: float = 0,
    cwd: str | Path | None = None,
    env: Optional[Dict[str, str]] = None,
    acceptable_exit_codes: Optional[List[int]] = None,
) -> Dict[str, Any]:
    if acceptable_exit_codes is None:
        acceptable_exit_codes = [0]

    if delay > 0:
        time.sleep(delay)

    wait_if_paused(app)

    if app and getattr(app, "stop_requested", False):
        return {"ok": False, "stopped": True, "stdout": "", "lines": []}

    args = shlex.split(command) if isinstance(command, str) else command

    if verbose >= 1:
        log_message(app, tool_name or "tool", f"$ {' '.join(args)}\n")

    started = time.time()
    stdout_lines: List[str] = []

    try:
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(cwd) if cwd else None,
            env=_merge_env(env),
            bufsize=1,
        )
    except FileNotFoundError:
        msg = f"Missing dependency: {args[0]}\n"
        log_message(app, tool_name or "tool", msg)
        return {"ok": False, "missing_dependency": args[0], "stdout": "", "lines": []}

    if app and tool_name and hasattr(app, "register_process"):
        app.register_process(tool_name, process)

    last_activity = time.time()
    heartbeat_every = 15

    try:
        while True:
            if app and getattr(app, "stop_requested", False):
                try:
                    process.terminate()
                except Exception:
                    pass
                break

            wait_if_paused(app)

            if process.stdout is None:
                break

            line = process.stdout.readline()
            if line:
                last_activity = time.time()
                stdout_lines.append(line)
                if verbose >= 2:
                    log_message(app, tool_name or "tool", line)
                continue

            if process.poll() is not None:
                break

            if verbose >= 1 and (time.time() - last_activity) >= heartbeat_every:
                elapsed = round(time.time() - started, 1)
                log_message(app, tool_name or "tool", f"[still running after {elapsed}s]\n")
                last_activity = time.time()

            time.sleep(0.1)
    finally:
        try:
            return_code = process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except Exception:
                pass
            return_code = process.wait()
        if app and tool_name and hasattr(app, "unregister_process"):
            app.unregister_process(tool_name, process)

    duration = round(time.time() - started, 2)

    if return_code not in acceptable_exit_codes and not (app and getattr(app, "stop_requested", False)):
        log_message(app, tool_name or "tool", f"[exit={return_code}] command finished with non-zero status\n")

    content = "".join(stdout_lines)
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if json_output:
            lines: List[Dict[str, Any]] = []
            for raw in stdout_lines:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    lines.append(json.loads(raw))
                except json.JSONDecodeError:
                    pass
            write_json(output_path, lines)
        else:
            with open(output_path, "w", encoding="utf-8") as handle:
                handle.write(content)

    return {
        "ok": return_code in acceptable_exit_codes,
        "return_code": return_code,
        "duration": duration,
        "stdout": content,
        "lines": stdout_lines,
        "stderr": "",
        "stopped": bool(app and getattr(app, "stop_requested", False)),
    }


def load_lines(path: str | Path) -> List[str]:
    path = Path(path)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def save_lines(path: str | Path, values: Iterable[str]) -> None:
    unique = sorted({value.strip() for value in values if value and value.strip()})
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for value in unique:
            handle.write(value + "\n")


def sanitize_filename(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("_") or "item"


def normalise_domain(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"^https?://", "", value)
    value = value.split("/")[0]
    return value.split(":")[0]


def extract_host(value: str) -> str:
    if "://" not in value:
        value = f"https://{value}"
    parsed = urlparse(value)
    return (parsed.hostname or "").lower()


def is_in_scope(candidate: str, scope: Dict[str, Any]) -> bool:
    candidate = normalise_domain(candidate)
    targets = [normalise_domain(t) for t in scope.get("targets", [])]
    out_of_scope = [normalise_domain(t) for t in scope.get("out_of_scope", [])]

    if any(candidate == denied or candidate.endswith(f".{denied}") for denied in out_of_scope if denied):
        return False

    if not targets:
        return True

    for allowed in targets:
        if candidate == allowed or candidate.endswith(f".{allowed}"):
            return True
    return False


def filter_in_scope(values: Iterable[str], scope: Dict[str, Any]) -> List[str]:
    return sorted({normalise_domain(value) for value in values if is_in_scope(value, scope)})


def expand_targets_from_config(config: Dict[str, Any]) -> List[str]:
    targets = list(config.get("scope", {}).get("targets", []))
    scope_file = config.get("scope", {}).get("scope_file")
    if scope_file and Path(scope_file).exists():
        targets.extend(load_lines(scope_file))
    return filter_in_scope(targets, config.get("scope", {}))


def limit_items(items: List[Any], limit: int) -> List[Any]:
    if limit and limit > 0:
        return items[:limit]
    return items


def extract_url_parts(url: str) -> Dict[str, Any]:
    if "://" not in url:
        url = f"https://{url}"
    parsed = urlparse(url)
    path = parsed.path or "/"
    query = parsed.query or ""
    ext = path.rsplit(".", 1)[-1].lower() if "." in path.rsplit("/", 1)[-1] else ""
    return {
        "url": url,
        "host": (parsed.hostname or "").lower(),
        "scheme": parsed.scheme,
        "port": parsed.port,
        "path": path,
        "query": query,
        "extension": ext,
    }


def cluster_params(urls: Iterable[str]) -> List[Dict[str, Any]]:
    clusters: Dict[str, Dict[str, Any]] = {}
    for url in urls:
        if "://" not in url:
            url = f"https://{url}"
        parsed = urlparse(url)
        params = [key for key, _ in parse_qsl(parsed.query, keep_blank_values=True)]
        if not params:
            continue
        route_key = f"{parsed.netloc}{parsed.path}"
        cluster = clusters.setdefault(
            route_key,
            {"route": route_key, "host": parsed.hostname, "path": parsed.path, "param_names": set(), "sample_urls": []},
        )
        cluster["param_names"].update(params)
        if len(cluster["sample_urls"]) < 5:
            cluster["sample_urls"].append(url)

    rows = []
    for row in clusters.values():
        rows.append(
            {
                "route": row["route"],
                "host": row["host"],
                "path": row["path"],
                "param_names": sorted(row["param_names"]),
                "sample_urls": row["sample_urls"],
                "param_count": len(row["param_names"]),
            }
        )
    rows.sort(key=lambda x: (-x["param_count"], x["route"]))
    return rows


def replace_query_values(url: str, replacement: str) -> str:
    parsed = urlparse(url)
    pairs = [(key, replacement) for key, _ in parse_qsl(parsed.query, keep_blank_values=True)]
    new_query = urlencode(pairs, doseq=True)
    return urlunparse(parsed._replace(query=new_query))
