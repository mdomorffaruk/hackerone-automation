from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader

from .utils import read_json, write_json


def build_summary(target: str, target_output: Path) -> Dict[str, Any]:
    recon_dir = target_output / "recon"
    scan_dir = target_output / "scan"

    subdomains = read_json(recon_dir / "subdomains.json", default=[])
    httpx_rows = read_json(recon_dir / "httpx.json", default=[])
    interesting_urls = read_json(recon_dir / "interesting_urls_merged.json", default=[])
    waf_rows = read_json(recon_dir / "waf.json", default=[])
    archived_urls = read_json(recon_dir / "archived_urls.json", default=[])

    naabu_rows = read_json(scan_dir / "naabu.json", default=[])
    nuclei_rows = read_json(scan_dir / "nuclei.json", default=[])
    ferox_rows = read_json(scan_dir / "ferox.json", default=[])
    js_rows = read_json(scan_dir / "js_analysis.json", default=[])
    takeover_rows = read_json(scan_dir / "takeover_candidates.json", default=[])
    reflection_rows = read_json(scan_dir / "reflection_candidates.json", default=[])
    param_clusters = read_json(scan_dir / "parameter_clusters.json", default=[])
    manual_queue = read_json(target_output / "manual_queue.json", default=[])

    summary = {
        "target": target,
        "counts": {
            "subdomains": len(subdomains),
            "live_urls": len(httpx_rows),
            "interesting_urls": len(interesting_urls),
            "archived_urls": len(archived_urls),
            "waf_detected": sum(1 for row in waf_rows if row.get("detected")),
            "open_ports": len(naabu_rows),
            "nuclei_findings": len(nuclei_rows),
            "content_hits": len(ferox_rows),
            "js_files_reviewed": len(js_rows),
            "takeover_candidates": len(takeover_rows),
            "reflection_candidates": sum(1 for row in reflection_rows if row.get("candidate")),
            "parameter_clusters": len(param_clusters),
            "manual_queue": len(manual_queue),
        },
        "top_manual_items": manual_queue[:25],
        "top_interesting_urls": interesting_urls[:25],
        "nuclei_by_severity": _count_by_key(nuclei_rows, "severity"),
        "js_secret_hits": [row for row in js_rows if row.get("secrets")],
        "top_takeover_candidates": takeover_rows[:15],
        "top_reflection_candidates": [row for row in reflection_rows if row.get("candidate")][:15],
        "top_parameter_clusters": param_clusters[:15],
    }
    return summary


def _count_by_key(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = row.get(key) or "unknown"
        counts[value] = counts.get(value, 0) + 1
    return counts


def generate_report(target: str, config: Dict[str, Any], target_output: Path) -> None:
    summary = build_summary(target, target_output)
    write_json(target_output / "summary.json", summary)

    env = Environment(loader=FileSystemLoader(str(Path(__file__).resolve().parent.parent / "templates")))
    template = env.get_template("report_template.html")
    html = template.render(summary=summary)
    with open(target_output / "report.html", "w", encoding="utf-8") as handle:
        handle.write(html)
