# Project Updates

## v0.6.0

### Fixed
- `--no-tui` now runs a real console pipeline instead of relying on the Textual headless path.
- Applied execution profiles correctly. Before this, `--profile` existed but did not actually modify runtime config.
- Added heartbeat logging for long-running tools so the run no longer looks dead when a subprocess is quiet.
- Improved widget lookup in the TUI log panes to avoid brittle query behavior.
- Enabled `feroxbuster` by default for better automatic content discovery.

### Changed
- Console mode now prints phase status and tool commands directly.
- Subprocess environment is merged more safely and defaults to unbuffered Python output where applicable.

### Reality check
- This is still a candidate generator, not a guaranteed vuln finder.
- It can reduce dead time and produce a stronger manual queue, but it cannot replace validation and exploit development.

## v0.5.0

### Added
- Archive URL ingestion using `gau` and `waybackurls`.
- `interesting_urls_merged.json` to combine crawl plus archive signal.
- `param_clusters.json` and `scan/parameter_clusters.json` for grouped parameter review.
- `takeover_candidates.json` using CNAME provider hints from httpx data.
- `reflection_candidates.json` for lightweight parameter reflection and diff checks.
- Execution profiles: `safe`, `normal`, `aggressive`.
- Graceful shutdown path for TUI quit and `Ctrl+C`.

### Changed
- Shifted default rates to safer bug bounty settings.
- Added `-cname` to httpx for takeover enrichment.
- Expanded the manual queue with takeover, reflection, and parameter cluster items.
- Improved reporting and summary coverage.

### Fixed
- Ugly `KeyboardInterrupt` shutdown path from the TUI runner.
- Process tracking when multiple commands of the same tool are active.
- Better stop handling for long-running subprocesses.
