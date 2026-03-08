from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

from .utils import (
    create_dir,
    extract_host,
    is_in_scope,
    limit_items,
    load_lines,
    log_message,
    read_json,
    replace_query_values,
    run_tool,
    sanitize_filename,
    save_lines,
    tool_exists,
    write_json,
)


SECRET_PATTERNS = {
    "aws_access_key": r"AKIA[0-9A-Z]{16}",
    "google_api_key": r"AIza[0-9A-Za-z\-_]{35}",
    "slack_token": r"xox[baprs]-[0-9A-Za-z-]{10,48}",
    "jwt": r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9._-]+\.[A-Za-z0-9._-]+",
    "private_key": r"-----BEGIN (?:RSA|DSA|EC|OPENSSH|PGP) PRIVATE KEY-----",
}

TAKEOVER_HINTS = {
    ".github.io": "GitHub Pages",
    ".herokudns.com": "Heroku",
    ".azurewebsites.net": "Azure App Service",
    ".cloudfront.net": "CloudFront",
    ".pantheonsite.io": "Pantheon",
    ".zendesk.com": "Zendesk",
    ".fastly.net": "Fastly",
}


def _tool_cfg(config: Dict[str, Any], name: str) -> Dict[str, Any]:
    return config.get("tools", {}).get(name, {})


def run_port_scan(config: Dict[str, Any], target_output: Path, app, args) -> List[Dict[str, Any]]:
    scan_dir = target_output / "scan"
    recon_dir = target_output / "recon"
    output_path = scan_dir / "naabu.json"
    if args.resume and output_path.exists():
        return read_json(output_path, default=[])

    cfg = _tool_cfg(config, "naabu")
    hosts_file = recon_dir / "alive_hosts.txt"
    hosts = load_lines(hosts_file)
    if not cfg.get("enabled", False) or not tool_exists("naabu") or not hosts:
        write_json(output_path, [])
        return []

    hosts = limit_items(hosts, args.max_hosts)
    save_lines(hosts_file, hosts)
    command = f"naabu -list {hosts_file} {cfg.get('flags', '')}"
    result = run_tool(command, app=app, tool_name="naabu", verbose=args.verbose, delay=config.get("global_delay", 0), acceptable_exit_codes=[0, 1])

    rows: List[Dict[str, Any]] = []
    for line in result.get("stdout", "").splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            host, port = line.rsplit(":", 1)
            if is_in_scope(host, config["scope"]) and port.isdigit():
                rows.append({"host": host, "port": int(port)})
    write_json(output_path, rows)
    return rows


def run_nuclei(config: Dict[str, Any], target_output: Path, app, args) -> List[Dict[str, Any]]:
    scan_dir = target_output / "scan"
    recon_dir = target_output / "recon"
    output_path = scan_dir / "nuclei.json"
    if args.resume and output_path.exists():
        return read_json(output_path, default=[])

    cfg = _tool_cfg(config, "nuclei")
    alive_urls = load_lines(recon_dir / "alive_urls.txt")
    interesting_urls = read_json(recon_dir / "interesting_urls_merged.json", default=[])
    if not cfg.get("enabled", False) or not tool_exists("nuclei") or not alive_urls:
        write_json(output_path, [])
        return []

    candidate_targets = list(alive_urls)
    high_value = [row["url"] for row in interesting_urls if row.get("score", 0) >= config.get("prioritization", {}).get("nuclei_min_score", 8)]
    if high_value:
        candidate_targets = sorted(set(candidate_targets + high_value))

    candidate_targets = limit_items(candidate_targets, args.max_urls or args.max_hosts)
    tmp_targets = scan_dir / "nuclei_targets.txt"
    save_lines(tmp_targets, candidate_targets)

    templates = cfg.get("templates", [])
    template_flags = " ".join(f"-t {template}" for template in templates)
    severities = ",".join(cfg.get("severity", ["medium", "high", "critical"]))
    command = f"nuclei -l {tmp_targets} {template_flags} -severity {severities} {cfg.get('flags', '')}"
    result = run_tool(command, app=app, tool_name="nuclei", verbose=args.verbose, delay=config.get("global_delay", 0), acceptable_exit_codes=[0, 1])

    rows: List[Dict[str, Any]] = []
    for line in result.get("stdout", "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            item = {"raw": line}
        matched = item.get("matched-at") or item.get("host") or item.get("url") or item.get("raw", "")
        rows.append({
            "template_id": item.get("template-id"),
            "severity": item.get("info", {}).get("severity") if isinstance(item.get("info"), dict) else item.get("severity"),
            "name": item.get("info", {}).get("name") if isinstance(item.get("info"), dict) else None,
            "matched_at": matched,
            "extracted_results": item.get("extracted-results", []),
            "raw": item,
        })
    write_json(output_path, rows)
    return rows


def run_content_discovery(config: Dict[str, Any], target_output: Path, app, args) -> List[Dict[str, Any]]:
    scan_dir = target_output / "scan"
    recon_dir = target_output / "recon"
    output_path = scan_dir / "ferox.json"
    if args.resume and output_path.exists():
        return read_json(output_path, default=[])

    cfg = _tool_cfg(config, "feroxbuster")
    alive_urls = load_lines(recon_dir / "alive_urls.txt")
    if not cfg.get("enabled", False) or not tool_exists("feroxbuster") or not alive_urls:
        write_json(output_path, [])
        return []

    targets = limit_items(alive_urls, args.max_hosts)
    rows: List[Dict[str, Any]] = []
    wordlist = config.get("wordlists", {}).get("content")
    for url in targets:
        command = f"feroxbuster -u {url} -w {wordlist} {cfg.get('flags', '')} --json"
        result = run_tool(command, app=app, tool_name="feroxbuster", verbose=args.verbose, delay=config.get("global_delay", 0), acceptable_exit_codes=[0, 1, 2])
        for line in result.get("stdout", "").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            result_url = item.get("url")
            if not result_url:
                continue
            rows.append({
                "parent": url,
                "url": result_url,
                "status": item.get("status"),
                "length": item.get("content_length"),
                "type": item.get("type"),
            })
    write_json(output_path, rows)
    return rows


def analyse_javascript(config: Dict[str, Any], target_output: Path, app, args) -> List[Dict[str, Any]]:
    scan_dir = target_output / "scan"
    recon_dir = target_output / "recon"
    output_path = scan_dir / "js_analysis.json"
    if args.resume and output_path.exists():
        return read_json(output_path, default=[])

    js_urls = load_lines(recon_dir / "javascript_files.txt")
    if not js_urls or not tool_exists("httpx"):
        write_json(output_path, [])
        return []

    rows: List[Dict[str, Any]] = []
    for url in limit_items(js_urls, args.max_urls):
        command = f"httpx -u {url} -silent -body-preview 120000 -json"
        result = run_tool(command, app=app, tool_name="js_fetch", verbose=args.verbose, delay=config.get("global_delay", 0), acceptable_exit_codes=[0, 1])
        body = ""
        for line in result.get("stdout", "").splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            body = item.get("body-preview") or item.get("body") or ""
            break
        findings = []
        endpoint_hits = sorted(set(re.findall(r"(?:/api|https?://)[A-Za-z0-9_./?=&%-]+", body)))[:50]
        for name, pattern in SECRET_PATTERNS.items():
            if re.search(pattern, body):
                findings.append(name)
        rows.append({
            "url": url,
            "secrets": findings,
            "endpoints": endpoint_hits,
        })
    write_json(output_path, rows)
    return rows


def build_takeover_candidates(target_output: Path) -> List[Dict[str, Any]]:
    recon_dir = target_output / "recon"
    output_path = target_output / "scan" / "takeover_candidates.json"
    httpx_rows = read_json(recon_dir / "httpx.json", default=[])
    rows: List[Dict[str, Any]] = []
    for row in httpx_rows:
        cnames = row.get("cname") or row.get("cnames") or []
        if isinstance(cnames, str):
            cnames = [cnames]
        for cname in cnames:
            cname = str(cname).lower()
            for suffix, provider in TAKEOVER_HINTS.items():
                if suffix in cname:
                    rows.append(
                        {
                            "host": row.get("host"),
                            "url": row.get("url"),
                            "cname": cname,
                            "provider_hint": provider,
                            "reason": "review dangling service / unclaimed application possibility",
                        }
                    )
                    break
    unique = {(r["host"], r["cname"]): r for r in rows}
    final_rows = sorted(unique.values(), key=lambda x: (x["provider_hint"], x["host"]))
    write_json(output_path, final_rows)
    return final_rows


def build_parameter_clusters(target_output: Path) -> List[Dict[str, Any]]:
    recon_dir = target_output / "recon"
    output_path = target_output / "scan" / "parameter_clusters.json"
    existing = read_json(recon_dir / "param_clusters.json", default=[])
    write_json(output_path, existing)
    return existing


def _fetch_url(url: str, timeout: int = 8) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; H1-Automation/0.5)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read(50000)
            return {
                "ok": True,
                "status": getattr(response, "status", None),
                "length": len(body),
                "body": body.decode("utf-8", errors="ignore"),
            }
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read(50000)
        except Exception:
            body = b""
        return {"ok": False, "status": exc.code, "length": len(body), "body": body.decode("utf-8", errors="ignore")}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "status": None, "length": 0, "body": ""}


def run_reflection_tests(config: Dict[str, Any], target_output: Path, app, args) -> List[Dict[str, Any]]:
    recon_dir = target_output / "recon"
    output_path = target_output / "scan" / "reflection_candidates.json"
    if args.resume and output_path.exists():
        return read_json(output_path, default=[])

    interesting_urls = read_json(recon_dir / "interesting_urls_merged.json", default=[])
    param_urls = [row["url"] for row in interesting_urls if row.get("query")]
    targets = limit_items(param_urls, args.max_reflection_tests)
    marker = "h1reflectioncheck987654321"
    rows: List[Dict[str, Any]] = []

    for url in targets:
        baseline = _fetch_url(url)
        modified_url = replace_query_values(url, marker)
        changed = _fetch_url(modified_url)
        reflected = marker in changed.get("body", "")
        length_delta = abs((changed.get("length") or 0) - (baseline.get("length") or 0))
        status_changed = baseline.get("status") != changed.get("status")
        candidate = reflected or length_delta >= 100 or status_changed
        rows.append(
            {
                "url": url,
                "modified_url": modified_url,
                "baseline_status": baseline.get("status"),
                "changed_status": changed.get("status"),
                "baseline_length": baseline.get("length"),
                "changed_length": changed.get("length"),
                "length_delta": length_delta,
                "reflected": reflected,
                "candidate": candidate,
                "reason": [
                    reason
                    for reason, value in [
                        ("reflected_marker", reflected),
                        ("status_changed", status_changed),
                        ("content_length_shift", length_delta >= 100),
                    ]
                    if value
                ],
            }
        )
        if candidate:
            log_message(app, "reflection", f"candidate: {url}\n")

    rows.sort(key=lambda x: (not x["candidate"], -x["length_delta"], x["url"]))
    write_json(output_path, rows)
    return rows


def build_manual_queue(config: Dict[str, Any], target_output: Path) -> List[Dict[str, Any]]:
    recon_dir = target_output / "recon"
    scan_dir = target_output / "scan"
    output_path = target_output / "manual_queue.json"

    interesting_urls = read_json(recon_dir / "interesting_urls_merged.json", default=[])
    nuclei_rows = read_json(scan_dir / "nuclei.json", default=[])
    ferox_rows = read_json(scan_dir / "ferox.json", default=[])
    js_rows = read_json(scan_dir / "js_analysis.json", default=[])
    port_rows = read_json(scan_dir / "naabu.json", default=[])
    takeover_rows = read_json(scan_dir / "takeover_candidates.json", default=[])
    reflection_rows = read_json(scan_dir / "reflection_candidates.json", default=[])
    param_clusters = read_json(scan_dir / "parameter_clusters.json", default=[])

    queue: List[Dict[str, Any]] = []

    for row in interesting_urls[:150]:
        reasons = list(row.get("matched_keywords", []))
        if row.get("query"):
            reasons.append("has_parameters")
        queue.append({
            "type": "interesting_url",
            "priority": row.get("score", 0),
            "target": row.get("url"),
            "reasons": sorted(set(reasons)),
            "recommended_tests": [
                "access control / IDOR",
                "parameter tampering",
                "redirect / SSRF sink review",
                "workflow and business logic",
            ],
        })

    for row in nuclei_rows:
        sev = row.get("severity") or "info"
        priority = {"critical": 100, "high": 80, "medium": 60, "low": 30, "info": 10}.get(sev, 10)
        queue.append({
            "type": "nuclei_candidate",
            "priority": priority,
            "target": row.get("matched_at"),
            "reasons": [row.get("template_id") or "nuclei_match", sev],
            "recommended_tests": ["manual validation", "proof of impact", "false positive elimination"],
        })

    for row in js_rows:
        priority = 75 if row.get("secrets") else 45
        reasons = list(row.get("secrets", [])) + (["js_endpoints"] if row.get("endpoints") else [])
        queue.append({
            "type": "javascript_review",
            "priority": priority,
            "target": row.get("url"),
            "reasons": reasons,
            "recommended_tests": ["secret validation", "hidden API testing", "auth bypass mapping"],
        })

    for row in ferox_rows[:150]:
        path = row.get("url", "")
        priority = 15
        if any(keyword in path.lower() for keyword in ["admin", "backup", "swagger", "internal", "debug", "config"]):
            priority = 65
        queue.append({
            "type": "content_discovery",
            "priority": priority,
            "target": path,
            "reasons": [str(row.get("status")), row.get("type") or "content"],
            "recommended_tests": ["sensitive file review", "auth check", "information disclosure"],
        })

    for row in port_rows:
        port = row.get("port")
        priority = 50 if port not in [80, 443] else 15
        queue.append({
            "type": "open_port",
            "priority": priority,
            "target": f"{row.get('host')}:{port}",
            "reasons": ["non_http_service" if port not in [80, 443] else "web_port"],
            "recommended_tests": ["service fingerprinting", "exposed admin surface", "default auth review"],
        })

    for row in takeover_rows:
        queue.append(
            {
                "type": "takeover_candidate",
                "priority": 70,
                "target": row.get("host"),
                "reasons": [row.get("provider_hint"), "cname_review"],
                "recommended_tests": ["dangling DNS validation", "unclaimed service verification"],
            }
        )

    for row in reflection_rows:
        if not row.get("candidate"):
            continue
        queue.append(
            {
                "type": "reflection_candidate",
                "priority": 68 if row.get("reflected") else 52,
                "target": row.get("url"),
                "reasons": row.get("reason", []),
                "recommended_tests": ["reflection/XSS check", "parameter handling diffing", "cache poisoning review"],
            }
        )

    for row in param_clusters[:100]:
        priority = min(65, 20 + (row.get("param_count", 0) * 5))
        queue.append(
            {
                "type": "parameter_cluster",
                "priority": priority,
                "target": row.get("route"),
                "reasons": row.get("param_names", []),
                "recommended_tests": ["parameter tampering", "mass assignment", "IDOR / object reference review"],
            }
        )

    queue.sort(key=lambda x: (-x["priority"], x["target"] or ""))
    deduped = []
    seen = set()
    for item in queue:
        key = (item["type"], item["target"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    write_json(output_path, deduped)
    return deduped


def run_scan_phase(target: str, config: Dict[str, Any], target_output: Path, app, args) -> None:
    scan_dir = target_output / "scan"
    create_dir(scan_dir)
    log_message(app, "phase", f"[scan] target={target}\n")
    run_port_scan(config, target_output, app, args)
    run_content_discovery(config, target_output, app, args)
    run_nuclei(config, target_output, app, args)
    analyse_javascript(config, target_output, app, args)
    build_takeover_candidates(target_output)
    build_parameter_clusters(target_output)
    run_reflection_tests(config, target_output, app, args)
    build_manual_queue(config, target_output)
