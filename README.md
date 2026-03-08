# H1 Automation v0.6.0

This version is built to do the boring work well enough that you can spend your time on manual testing instead of data cleanup.

It does not pretend to fully replace a hunter.
It does try to finish with a short, structured, high-signal queue.

## What it now does better

- strict in-scope recon and scan flow
- JSON-first outputs for every meaningful artifact
- safer default rates for bug bounty work
- archive URL ingestion using `gau` and `waybackurls`
- parameter clustering for tampering and IDOR review
- takeover hint generation from discovered CNAMEs
- lightweight reflection / response-diff candidates for parameterized URLs
- merged live crawl plus archive view for better prioritisation
- graceful shutdown instead of ugly stack traces on `Ctrl+C`
- profile modes: `safe`, `normal`, `aggressive`

## Realistic thinking behind the design

A useful automation tool for bug bounty should do these jobs:

1. map target surface
2. enrich it with metadata
3. cut the noise down
4. generate test candidates
5. leave the final call to a human

That means this tool is not trying to auto-report nonsense.
It is trying to finish with:

- `interesting_urls_merged.json`
- `parameter_clusters.json`
- `reflection_candidates.json`
- `takeover_candidates.json`
- `manual_queue.json`

Those are the files you actually review.

## New execution profiles

### Safe
Use this for most public bounty programs.
Defaults are intentionally conservative.

### Normal
Faster, but still reasonable.

### Aggressive
Only use where the program explicitly allows heavier recon.

Run with:

```bash
python main.py --target example.com --all --profile safe
```

## Output layout

```text
output/<target>/
├── recon/
│   ├── subdomains.json
│   ├── subdomains.txt
│   ├── httpx.json
│   ├── alive_urls.txt
│   ├── alive_hosts.txt
│   ├── katana.jsonl
│   ├── archived_urls.json
│   ├── archived_interesting_urls.json
│   ├── interesting_urls.json
│   ├── interesting_urls_merged.json
│   ├── param_clusters.json
│   ├── javascript_files.txt
│   ├── waf.json
│   └── commands.json
├── scan/
│   ├── naabu.json
│   ├── nuclei.json
│   ├── ferox.json
│   ├── js_analysis.json
│   ├── takeover_candidates.json
│   ├── reflection_candidates.json
│   └── parameter_clusters.json
├── manual_queue.json
├── summary.json
└── report.html
```

## Installed tools expected in PATH

- subfinder
- assetfinder
- amass
- dnsx
- httpx
- katana
- wafw00f
- naabu
- nuclei
- gau
- waybackurls
- feroxbuster (optional)

## Usage examples

Run everything in safe mode:

```bash
python main.py --target example.com --all --profile safe
```

Run without TUI:

```bash
python main.py --target example.com --all --profile safe --no-tui -v
```

Console mode now prints phases, commands, and periodic heartbeat messages for long-running tools.

Resume from previous JSON outputs:

```bash
python main.py --target example.com --all --resume
```

Limit live surface and archive volume while tuning:

```bash
python main.py --target example.com --all --max-hosts 20 --max-urls 75 --max-archive-urls 1000
```

## Practical workflow

1. run recon + scan in `safe`
2. inspect `summary.json`
3. inspect top items in `manual_queue.json`
4. inspect `reflection_candidates.json`
5. inspect `takeover_candidates.json`
6. inspect `parameter_clusters.json`
7. manually test the highest-value items first

