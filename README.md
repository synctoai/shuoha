# shuoha

Beginner-friendly A-share stock analysis CLI.

## Setup

```bash
uv sync --extra dev
```

## Run

```bash
uv run shuoha analyze 600519
```

The command writes analysis artifacts to `out/600519/` by default.

## Agent mode

```bash
export OPENAI_API_KEY=...
uv run shuoha analyze 600519 --agent
```

Without `--agent`, Shuoha uses the deterministic local Markdown renderer.
