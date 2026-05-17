# CLI Codex Analysis Design

## Goal

Support deep multi-stock analysis through an external CLI backend:

```bash
shuoha analyze 000657 600105 300260 --cli codex
```

The first supported backends are:

- `local`: existing deterministic shuoha analysis.
- `codex`: external Codex CLI research and report generation.

Future CLI backends such as Claude can be added later through the same boundary, but they are out of scope for this change.

## User Experience

`--cli local` preserves the current behavior for one stock:

```bash
shuoha analyze 600519
shuoha analyze 600519 --cli local
```

`--cli codex` accepts one or more 6-digit stock codes and produces a dashboard-style Markdown report:

```bash
shuoha analyze 000657 600105 300260 --cli codex
```

The report should follow the requested decision-dashboard style:

- Date and generation time.
- Total stocks analyzed.
- Buy / watch / sell counts.
- Per-stock summary with verdict, score, and directional bias.
- News and sentiment summary.
- Performance or fundamental expectations when reliable data is available.
- Risk alerts.
- Positive catalysts.
- Latest dynamics.

## Architecture

The local deterministic pipeline remains the default and remains unchanged in purpose.

For `--cli codex`, shuoha prepares structured context before invoking Codex:

1. Validate all stock codes.
2. Reuse `AKShareProvider` to fetch company profile and market history.
3. Reuse `summarize_signals()` to compute existing technical and risk evidence.
4. Convert each `AnalysisResult` plus provider metadata into a prompt context.
5. Invoke `codex exec` non-interactively.
6. Read Codex's final Markdown response.
7. Write the report to an output directory.

Codex should not reimplement the existing AKShare data pipeline. It receives shuoha's structured context and uses its own available tools for external research such as recent news, announcements, market sentiment, and industry catalysts.

## Components

### CLI

`analyze` gains a `--cli` option with values:

- `local`
- `codex`

Default is `local`.

For `local`, multiple stock codes are rejected initially because the current terminal and output contract are single-stock.

For `codex`, one or more stock codes are accepted.

### External CLI Runner

Add a small runner module responsible for:

- Checking that the requested executable exists.
- Running `codex exec`.
- Passing the generated prompt through stdin.
- Capturing the final report through `--output-last-message`.
- Returning clear errors when Codex is missing, exits non-zero, or produces an empty report.

The initial implementation only supports Codex, but the boundary should avoid hard-coding Codex-specific behavior into the main `engine.py`.

### Prompt Builder

Add a testable prompt builder that receives structured stock contexts and returns one prompt string.

The prompt must require:

- Chinese Markdown output.
- Dashboard report format.
- Recent news and market context research.
- Explicit "未查到可靠来源" wording when a claim cannot be verified.
- No fabricated numbers, announcements, or sources.
- A final generation time.

The prompt may provide the deterministic verdict as a reference, but Codex is allowed to form a broader final decision because this mode is intended as deeper research rather than simple rewriting.

## Data Flow

```text
CLI stock codes
  -> validate
  -> AKShareProvider.fetch(code)
  -> summarize_signals(...)
  -> Codex prompt context
  -> codex exec
  -> Markdown dashboard report
  -> report.md
```

If AKShare fails for one stock, the prompt context should include a partial entry with warnings instead of aborting the entire multi-stock run. Codex can still research that stock externally, but the report must disclose that local market data was unavailable.

## Output

`local` keeps the existing output behavior.

`codex` writes a single combined report, initially under:

```text
out/codex/YYYY-MM-DD/report.md
```

The terminal prints the report or a concise success message, matching the existing `--full/--brief` spirit where practical.

## Error Handling

- Invalid stock code: reject before any data fetch or CLI call.
- `--cli local` with multiple stock codes: reject with a message explaining that multi-stock is currently supported by `--cli codex`.
- Missing `codex` executable: fail with installation/configuration guidance.
- Codex non-zero exit: surface stderr and avoid writing a misleading report.
- Empty Codex output: fail clearly.
- Per-stock AKShare fetch failure in `codex` mode: continue with partial context and data warning.

## Tests

Add focused tests for:

- `--cli local` remains the default.
- `--cli local` rejects multiple stock codes.
- `--cli codex` accepts multiple stock codes.
- Codex prompt includes all stock codes and dashboard requirements.
- Codex runner invokes `codex exec` with stdin and `--output-last-message`.
- Missing Codex executable and non-zero exit produce clear errors.
- Partial AKShare failures are included in prompt context without aborting the whole batch.

## Out Of Scope

- Claude or other CLI backends.
- A JSON output schema for Codex reports.
- Automatic source citation validation.
- Changing existing deterministic verdict rules.
- Replacing the local renderer.
