# Project Updates

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

### Reality check
- This still does not replace manual validation.
- This version is meant to reduce grunt work, not generate fake certainty.
