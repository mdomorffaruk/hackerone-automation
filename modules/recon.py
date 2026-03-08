from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .utils import (
    cluster_params,
    create_dir,
    extract_host,
    extract_url_parts,
    filter_in_scope,
    is_in_scope,
    limit_items,
    log_message,
    normalise_domain,
    read_json,
    read_jsonl,
    run_tool,
    save_lines,
    tool_exists,
    write_json,
)


RECON_KEYWORDS = {
    "admin": 10,
    "login": 9,
    "signin": 9,
    "auth": 8,
    "oauth": 8,
    "api": 8,
    "graphql": 9,
    "swagger": 9,
    "openapi": 9,
    "debug": 10,
    "staging": 10,
    "dev": 8,
    "test": 5,
    "internal": 9,
    "upload": 10,
    "import": 8,
    "redirect": 7,
    "callback": 7,
    "webhook": 8,
    ".js": 4,
}


def _tool_cfg(config: Dict[str, Any], name: str) -> Dict[str, Any]:
    return config.get("tools", {}).get(name, {})


def _write_command_meta(path: Path, data: Dict[str, Any]) -> None:
    existing = read_json(path, default=[])
    existing.append(data)
    write_json(path, existing)


def enumerate_subdomains(target: str, config: Dict[str, Any], recon_dir: Path, app, args) -> List[str]:
    output_path = recon_dir / "subdomains.json"
    if args.resume and output_path.exists():
        return [row["host"] for row in read_json(output_path, default=[])]

    collected: List[Dict[str, Any]] = []
    commands_path = recon_dir / "commands.json"
    delay = config.get("global_delay", 0)

    for tool_name in ["subfinder", "assetfinder", "amass", "dnsx"]:
        cfg = _tool_cfg(config, tool_name)
        if not cfg.get("enabled", False):
            continue
        if not tool_exists(tool_name):
            log_message(app, tool_name, "dependency not found, skipping\n")
            continue

        flags = cfg.get("flags", "")
        if tool_name == "subfinder":
            command = f"subfinder -d {target} {flags}"
        elif tool_name == "assetfinder":
            command = f"assetfinder {flags} {target}"
        elif tool_name == "amass":
            command = f"amass {flags} -d {target}"
        else:
            wordlist = config.get("wordlists", {}).get("subdomains")
            command = f"dnsx -d {target} -w {wordlist} {flags}" if wordlist else f"dnsx -d {target} {flags}"

        result = run_tool(command, app=app, tool_name=tool_name, verbose=args.verbose, delay=delay, acceptable_exit_codes=[0, 1])
        _write_command_meta(commands_path, {"phase": "enum", "tool": tool_name, "command": command, "ok": result.get("ok")})
        for line in result.get("stdout", "").splitlines():
            host = normalise_domain(line)
            if host and is_in_scope(host, config["scope"]):
                collected.append({"host": host, "source": tool_name})

    deduped: Dict[str, Dict[str, Any]] = {}
    for item in collected:
        host = item["host"]
        deduped.setdefault(host, {"host": host, "sources": []})
        deduped[host]["sources"].append(item["source"])

    rows = sorted(deduped.values(), key=lambda x: x["host"])
    write_json(output_path, rows)
    save_lines(recon_dir / "subdomains.txt", [row["host"] for row in rows])
    return [row["host"] for row in rows]


def probe_hosts(target: str, config: Dict[str, Any], recon_dir: Path, app, args, hosts: List[str]) -> List[Dict[str, Any]]:
    output_path = recon_dir / "httpx.json"
    if args.resume and output_path.exists():
        return read_json(output_path, default=[])
    if not hosts:
        write_json(output_path, [])
        return []

    httpx_cfg = _tool_cfg(config, "httpx")
    if not httpx_cfg.get("enabled", False) or not tool_exists("httpx"):
        write_json(output_path, [])
        return []

    tmp_hosts = recon_dir / "subdomains.txt"
    save_lines(tmp_hosts, hosts)
    command = f"httpx -l {tmp_hosts} {httpx_cfg.get('flags', '')}"
    result = run_tool(command, app=app, tool_name="httpx", verbose=args.verbose, delay=config.get("global_delay", 0), acceptable_exit_codes=[0, 1])
    _write_command_meta(recon_dir / "commands.json", {"phase": "probe", "tool": "httpx", "command": command, "ok": result.get("ok")})

    rows: List[Dict[str, Any]] = []
    for line in result.get("stdout", "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        url = item.get("url") or item.get("input")
        if not url:
            continue
        host = extract_host(url)
        if not is_in_scope(host, config["scope"]):
            continue
        item["host"] = host
        rows.append(item)

    rows = sorted(rows, key=lambda x: x.get("url", ""))
    write_json(output_path, rows)
    save_lines(recon_dir / "alive_urls.txt", [row.get("url", "") for row in rows])
    save_lines(recon_dir / "alive_hosts.txt", [row.get("host", "") for row in rows])
    return rows


def crawl_targets(target: str, config: Dict[str, Any], recon_dir: Path, app, args, alive_urls: List[str]) -> List[Dict[str, Any]]:
    output_path = recon_dir / "katana.jsonl"
    if args.resume and output_path.exists():
        return read_jsonl(output_path)
    if not alive_urls:
        write_json(recon_dir / "interesting_urls.json", [])
        return []

    katana_cfg = _tool_cfg(config, "katana")
    if not katana_cfg.get("enabled", False) or not tool_exists("katana"):
        write_json(recon_dir / "interesting_urls.json", [])
        return []

    alive_urls = limit_items(alive_urls, args.max_hosts)
    save_lines(recon_dir / "alive_urls.txt", alive_urls)
    command = f"katana -list {recon_dir / 'alive_urls.txt'} {katana_cfg.get('flags', '')}"
    result = run_tool(command, app=app, tool_name="katana", verbose=args.verbose, delay=config.get("global_delay", 0), acceptable_exit_codes=[0, 1])
    _write_command_meta(recon_dir / "commands.json", {"phase": "crawl", "tool": "katana", "command": command, "ok": result.get("ok")})

    rows: List[Dict[str, Any]] = []
    for line in result.get("stdout", "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            row = {"url": line}
        url = row.get("request", {}).get("endpoint") or row.get("url")
        if not url:
            continue
        parts = extract_url_parts(url)
        if not is_in_scope(parts["host"], config["scope"]):
            continue
        row.update(parts)
        rows.append(row)

    with open(output_path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    interesting = prioritise_urls(rows)
    write_json(recon_dir / "interesting_urls.json", interesting)
    save_lines(recon_dir / "javascript_files.txt", [row["url"] for row in interesting if row.get("extension") == "js"])
    return rows


def ingest_archived_urls(target: str, config: Dict[str, Any], recon_dir: Path, app, args) -> List[Dict[str, Any]]:
    output_path = recon_dir / "archived_urls.json"
    param_clusters_path = recon_dir / "param_clusters.json"
    if args.resume and output_path.exists() and param_clusters_path.exists():
        return read_json(output_path, default=[])

    rows: List[Dict[str, Any]] = []
    raw_urls: List[str] = []
    commands_path = recon_dir / "commands.json"
    hosts_file = recon_dir / "subdomains.txt"
    hosts = [target]
    if hosts_file.exists():
        hosts = [line.strip() for line in hosts_file.read_text(encoding="utf-8").splitlines() if line.strip()]

    tmp_hosts = recon_dir / "archive_hosts.txt"
    save_lines(tmp_hosts, hosts)

    for tool_name in ["gau", "waybackurls"]:
        cfg = _tool_cfg(config, tool_name)
        if not cfg.get("enabled", False) or not tool_exists(tool_name):
            continue
        if tool_name == "gau":
            command = f"gau --subs --providers wayback,commoncrawl,otx -o - < {tmp_hosts}"
            result = run_tool(["bash", "-lc", command], app=app, tool_name="gau", verbose=args.verbose, delay=config.get("global_delay", 0), acceptable_exit_codes=[0, 1])
        else:
            command = f"cat {tmp_hosts} | waybackurls"
            result = run_tool(["bash", "-lc", command], app=app, tool_name="waybackurls", verbose=args.verbose, delay=config.get("global_delay", 0), acceptable_exit_codes=[0, 1])
        _write_command_meta(commands_path, {"phase": "archive", "tool": tool_name, "command": command, "ok": result.get("ok")})
        for line in result.get("stdout", "").splitlines():
            url = line.strip()
            if not url:
                continue
            host = extract_host(url)
            if not is_in_scope(host, config["scope"]):
                continue
            raw_urls.append(url)

    filtered_urls = limit_items(sorted(set(raw_urls)), args.max_archive_urls)
    for url in filtered_urls:
        parts = extract_url_parts(url)
        rows.append(parts)

    interesting = prioritise_urls(rows)
    write_json(output_path, rows)
    write_json(recon_dir / "archived_interesting_urls.json", interesting)
    write_json(param_clusters_path, cluster_params([row["url"] for row in rows]))
    return rows


def prioritise_urls(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    prioritised: List[Dict[str, Any]] = []
    seen = set()
    for row in rows:
        url = row.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        haystack = f"{row.get('url', '')} {row.get('path', '')} {row.get('query', '')}".lower()
        score = 0
        matched = []
        for keyword, value in RECON_KEYWORDS.items():
            if keyword in haystack:
                score += value
                matched.append(keyword)
        if row.get("extension") == "js":
            score += 3
        if "=" in row.get("query", ""):
            score += 4
        if score <= 0:
            continue
        prioritised.append({
            "url": url,
            "host": row.get("host"),
            "path": row.get("path"),
            "query": row.get("query"),
            "extension": row.get("extension"),
            "score": score,
            "matched_keywords": sorted(set(matched)),
        })
    prioritised.sort(key=lambda x: (-x["score"], x["url"]))
    return prioritised


def detect_waf(target: str, config: Dict[str, Any], recon_dir: Path, app, args, alive_urls: List[str]) -> List[Dict[str, Any]]:
    output_path = recon_dir / "waf.json"
    if args.resume and output_path.exists():
        return read_json(output_path, default=[])
    waf_cfg = _tool_cfg(config, "wafw00f")
    if not waf_cfg.get("enabled", False) or not tool_exists("wafw00f"):
        write_json(output_path, [])
        return []

    rows: List[Dict[str, Any]] = []
    for url in limit_items(alive_urls, args.max_hosts):
        command = f"wafw00f {url} {waf_cfg.get('flags', '')}"
        result = run_tool(command, app=app, tool_name="wafw00f", verbose=args.verbose, delay=config.get("global_delay", 0), acceptable_exit_codes=[0, 1])
        text = result.get("stdout", "")
        rows.append({
            "url": url,
            "detected": "is behind" in text.lower(),
            "raw": text.strip(),
        })
    write_json(output_path, rows)
    return rows


def merge_recon_views(recon_dir: Path) -> None:
    katana_interesting = read_json(recon_dir / "interesting_urls.json", default=[])
    archived_interesting = read_json(recon_dir / "archived_interesting_urls.json", default=[])
    merged: Dict[str, Dict[str, Any]] = {}
    for source, rows in [("crawl", katana_interesting), ("archive", archived_interesting)]:
        for row in rows:
            url = row["url"]
            entry = merged.setdefault(url, {**row, "sources": []})
            entry["score"] = max(entry.get("score", 0), row.get("score", 0))
            entry["matched_keywords"] = sorted(set(entry.get("matched_keywords", [])) | set(row.get("matched_keywords", [])))
            if source not in entry["sources"]:
                entry["sources"].append(source)
    rows = sorted(merged.values(), key=lambda x: (-x.get("score", 0), x["url"]))
    write_json(recon_dir / "interesting_urls_merged.json", rows)


def run_recon_phase(target: str, config: Dict[str, Any], target_output: Path, app, args) -> None:
    recon_dir = target_output / "recon"
    create_dir(recon_dir)

    log_message(app, "phase", f"[recon] target={target}\n")
    hosts = enumerate_subdomains(target, config, recon_dir, app, args)
    probed = probe_hosts(target, config, recon_dir, app, args, hosts)
    alive_urls = [row.get("url") for row in probed if row.get("url")]
    crawl_targets(target, config, recon_dir, app, args, alive_urls)
    ingest_archived_urls(target, config, recon_dir, app, args)
    detect_waf(target, config, recon_dir, app, args, alive_urls)
    merge_recon_views(recon_dir)
