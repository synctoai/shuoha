# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project currently follows a
simple `MAJOR.MINOR.PATCH` versioning scheme.

## [0.1.0] - 2026-04-06

### Added

- Bootstrapped a Python CLI based on `uv`, `Typer`, `Rich`, and `Pydantic`.
- Added deterministic A-share analysis pipeline with `AKShare` provider support.
- Added normalized company metadata, daily history fetching, cache layer, and provider fallback from Eastmoney to Tencent.
- Added pure Python technical indicators for `MA`, `MACD`, `RSI`, `volume ratio`, `volatility`, and `max drawdown`.
- Added deterministic `verdict / confidence / bias` rules.
- Added beginner-friendly Chinese Markdown reports and `evidence.json` artifacts.
- Added richer report sections including `锐评`, `证据判决书`, `接下来盯什么`, `新手最容易犯的错`, `这份报告最可能看错的地方`, and threshold-based watch points.
- Added CLI output modes:
  - default terminal summary card
  - `--full` terminal report view
  - `--brief` explicit summary mode
- Added optional `--agent` Markdown rewrite path.
- Added terminal-specific renderer for better scanability.
- Added user-facing `README.md` and developer-facing `CONTRIBUTING.md`.
- Added module entrypoint for packaged execution via `python -m shuoha`.
- Added one-line install and uninstall scripts for macOS and Windows.
- Added GitHub Actions release workflow for standalone binaries.
- Added distribution contract documentation for release assets and install paths.

### Changed

- Localized the CLI and report experience to Chinese.
- Improved report readability for beginners with sharper action guidance and bias explanations.
- Improved provider stability with graceful degradation and cache-backed repeated analysis.
- Changed the primary user install path from local Python tooling to prebuilt binaries plus installer scripts.

### Fixed

- Fixed provider failure handling so the CLI degrades to partial results instead of crashing.
- Fixed historical data fallback behavior when Eastmoney is unavailable.
- Fixed output flow so users always get saved artifacts even when terminal mode changes.
- Fixed packaged binary build by collecting `akshare` package data required at runtime.
- Fixed `--agent` path so missing LLM dependencies fall back to the local renderer instead of crashing.
