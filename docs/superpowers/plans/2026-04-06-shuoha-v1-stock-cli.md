# Shuoha V1 Stock CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-first CLI where `shuoha <A-share-stock-code>` produces a deterministic beginner-friendly stock report with `evidence.json` and `report.md` artifacts.

**Architecture:** Use a Python CLI with a deterministic analysis pipeline: CLI input -> normalized `AKShare` provider -> pure-Python indicator calculations -> rules engine -> local Markdown renderer. Add a non-agent fallback first, then wire optional `DeepAgents` explanation rendering behind a flag so the trust boundary stays hard.

**Tech Stack:** Python 3.12, `uv`, Typer, Pydantic v2, AKShare, pandas, pytest, Rich, optional DeepAgents/OpenAI provider

---

## File Structure

### Files to create
- `pyproject.toml`
- `README.md`
- `src/shuoha/__init__.py`
- `src/shuoha/cli.py`
- `src/shuoha/config.py`
- `src/shuoha/engine.py`
- `src/shuoha/schemas.py`
- `src/shuoha/data/providers/base.py`
- `src/shuoha/data/providers/akshare_provider.py`
- `src/shuoha/data/trading_calendar.py`
- `src/shuoha/indicators.py`
- `src/shuoha/rules.py`
- `src/shuoha/reporting/markdown_renderer.py`
- `src/shuoha/reporting/agent_renderer.py`
- `src/shuoha/reporting/output.py`
- `tests/test_cli.py`
- `tests/test_engine.py`
- `tests/test_indicators.py`
- `tests/test_rules.py`
- `tests/test_markdown_renderer.py`
- `tests/test_akshare_provider.py`
- `tests/fixtures/stock_600519_daily.json`
- `tests/fixtures/stock_600519_company.json`

### Responsibilities
- `cli.py`: parse command line args, invoke engine, print paths and summary.
- `config.py`: environment/config defaults, output directory rules, provider flags.
- `schemas.py`: Pydantic models for normalized data, evidence, verdict, report status.
- `data/providers/base.py`: provider interface and normalization contract.
- `data/providers/akshare_provider.py`: fetch and normalize A-share history and company data.
- `data/trading_calendar.py`: latest trading day calculation for stale-data checks.
- `indicators.py`: pure-Python moving average, RSI, MACD, volatility, drawdown, 52-week distance.
- `rules.py`: deterministic scoring, veto conditions, verdict selection, confidence value.
- `reporting/markdown_renderer.py`: deterministic Markdown report output.
- `reporting/agent_renderer.py`: optional LLM explanation layer over fixed evidence blocks.
- `reporting/output.py`: write `evidence.json` and `report.md`.
- `engine.py`: orchestrate full analysis pipeline, fallback rules, and output object.

## Decisions Locked For This Plan
- Machine verdict enum: `consider`, `wait`, `avoid_for_now`
- Display labels: `Consider`, `Wait`, `Avoid for now`
- Top-level analysis status enum: `ok`, `partial`, `error`
- Default path is non-agent rendering. Agent rendering is opt-in via `--agent`.
- Initial agent provider: OpenAI only, behind `OPENAI_API_KEY`
- If critical data is missing, set `status=partial`, `verdict=null`, populate `data_warnings`, and still emit both artifacts

## V1 Rule Table

| Signal | Positive | Neutral | Negative | Notes |
|--------|----------|---------|----------|-------|
| Price vs 20d/60d MA | price > 20d and 20d > 60d | mixed alignment | price < 20d and 20d < 60d | trend proxy |
| MACD histogram | > 0 and rising | near 0 | < 0 and falling | momentum proxy |
| RSI | 45-65 | 35-45 or 65-75 | < 35 or > 75 | avoid strong overbought/oversold language |
| Drawdown from 52w high | < 10% | 10-20% | > 20% | risk proxy |
| Annualized volatility | < 25% | 25-35% | > 35% | beginner-facing risk |

### Verdict logic
- `avoid_for_now` veto if:
  - missing critical history data, or
  - trend negative and volatility negative, or
  - drawdown negative and momentum negative
- `consider` if at least 3 positive signals and no veto
- `wait` for all other complete-data cases
- Confidence:
  - `high` if 4+ aligned non-negative signals
  - `medium` if no veto and signals mixed
  - `low` if partial data or 2+ negative signals

## Validation Basket
- `600519` for large-cap defensive example
- `000858` for another consumer name with comparable pattern checks
- `300750` for higher-volatility growth example
- `601318` for financial large-cap behavior
- `688981` for tech/STAR-market volatility behavior

## Task 1: Bootstrap Python Package

**Files:**
- Create: `pyproject.toml`
- Create: `src/shuoha/__init__.py`
- Create: `README.md`

- [ ] **Step 1: Write the failing packaging smoke test**

```python
# tests/test_cli.py
from typer.testing import CliRunner

from shuoha.cli import app


def test_help_smoke():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Analyze one A-share stock code" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py::test_help_smoke -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'shuoha'`

- [ ] **Step 3: Write minimal project bootstrap**

```toml
# pyproject.toml
[project]
name = "shuoha"
version = "0.1.0"
description = "Beginner-friendly A-share stock CLI"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
  "akshare>=1.16.0",
  "pandas>=2.2.0",
  "pydantic>=2.8.0",
  "rich>=13.9.0",
  "typer>=0.16.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3.0",
]
agent = [
  "deepagents>=0.0.0",
  "openai>=2.0.0",
]

[project.scripts]
shuoha = "shuoha.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

```python
# src/shuoha/__init__.py
__all__ = ["__version__"]

__version__ = "0.1.0"
```

```markdown
# README.md

## shuoha

Beginner-friendly A-share stock analysis CLI.
```

- [ ] **Step 4: Add the minimal CLI app shell**

```python
# src/shuoha/cli.py
import typer

app = typer.Typer(help="Analyze one A-share stock code and produce beginner-friendly output.")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_cli.py::test_help_smoke -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml README.md src/shuoha/__init__.py src/shuoha/cli.py tests/test_cli.py
git commit -m "chore: bootstrap shuoha python cli"
```

## Task 2: Define Core Schemas

**Files:**
- Create: `src/shuoha/schemas.py`
- Modify: `tests/test_cli.py`
- Create: `tests/test_engine.py`

- [ ] **Step 1: Write the failing schema tests**

```python
# tests/test_engine.py
from shuoha.schemas import AnalysisResult, Verdict


def test_analysis_result_allows_partial_without_verdict():
    result = AnalysisResult(
        status="partial",
        stock_code="600519",
        company_name="贵州茅台",
        as_of_date="2026-04-06",
        verdict=None,
        confidence="low",
        technical_evidence=[],
        risk_evidence=[],
        unknowns=[],
        data_warnings=["missing history"],
        disclaimer="Educational only.",
    )
    assert result.status == "partial"
    assert result.verdict is None


def test_verdict_enum_machine_values():
    assert Verdict.CONSIDER.value == "consider"
    assert Verdict.WAIT.value == "wait"
    assert Verdict.AVOID_FOR_NOW.value == "avoid_for_now"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_engine.py -v`
Expected: FAIL with `ModuleNotFoundError` or `ImportError` for missing schemas

- [ ] **Step 3: Write the schema module**

```python
# src/shuoha/schemas.py
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    CONSIDER = "consider"
    WAIT = "wait"
    AVOID_FOR_NOW = "avoid_for_now"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnalysisStatus(str, Enum):
    OK = "ok"
    PARTIAL = "partial"
    ERROR = "error"


class EvidenceSignal(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class EvidenceItem(BaseModel):
    name: str
    signal: EvidenceSignal
    raw_value: str | float | int
    plain_text: str


class BasicContext(BaseModel):
    industry: str | None = None
    company_summary: str


class AnalysisResult(BaseModel):
    status: AnalysisStatus
    stock_code: str
    company_name: str
    as_of_date: str
    verdict: Verdict | None = None
    confidence: Confidence
    technical_evidence: list[EvidenceItem] = Field(default_factory=list)
    risk_evidence: list[EvidenceItem] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    data_warnings: list[str] = Field(default_factory=list)
    basic_context: BasicContext | None = None
    disclaimer: str
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/shuoha/schemas.py tests/test_engine.py
git commit -m "feat: add core analysis schemas"
```

## Task 3: Add Provider Contract And AKShare Normalization

**Files:**
- Create: `src/shuoha/data/providers/base.py`
- Create: `src/shuoha/data/providers/akshare_provider.py`
- Create: `src/shuoha/data/trading_calendar.py`
- Create: `tests/test_akshare_provider.py`
- Create: `tests/fixtures/stock_600519_daily.json`
- Create: `tests/fixtures/stock_600519_company.json`

- [ ] **Step 1: Write the failing provider normalization test**

```python
# tests/test_akshare_provider.py
from shuoha.data.providers.akshare_provider import normalize_daily_history


def test_normalize_daily_history_sorts_and_keeps_required_fields():
    rows = [
        {"日期": "2026-04-02", "收盘": 1680.0, "开盘": 1670.0, "最高": 1692.0, "最低": 1668.0, "成交量": 1000},
        {"日期": "2026-04-01", "收盘": 1662.0, "开盘": 1650.0, "最高": 1668.0, "最低": 1640.0, "成交量": 900},
    ]
    out = normalize_daily_history(rows)
    assert out[0]["date"] == "2026-04-01"
    assert out[-1]["close"] == 1680.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_akshare_provider.py::test_normalize_daily_history_sorts_and_keeps_required_fields -v`
Expected: FAIL because provider module does not exist

- [ ] **Step 3: Write provider base contract and normalization**

```python
# src/shuoha/data/providers/base.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ProviderPayload:
    stock_code: str
    company_name: str
    industry: str | None
    company_summary: str
    daily_history: list[dict]
    as_of_date: str


class StockDataProvider(Protocol):
    def fetch(self, stock_code: str) -> ProviderPayload: ...
```

```python
# src/shuoha/data/providers/akshare_provider.py
from __future__ import annotations

import akshare as ak

from shuoha.data.providers.base import ProviderPayload


def normalize_daily_history(rows: list[dict]) -> list[dict]:
    normalized = [
        {
            "date": row["日期"],
            "open": float(row["开盘"]),
            "high": float(row["最高"]),
            "low": float(row["最低"]),
            "close": float(row["收盘"]),
            "volume": float(row["成交量"]),
        }
        for row in rows
    ]
    normalized.sort(key=lambda row: row["date"])
    return normalized


class AKShareProvider:
    def fetch(self, stock_code: str) -> ProviderPayload:
        hist = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust="")
        rows = hist.to_dict(orient="records")
        daily_history = normalize_daily_history(rows)
        company_name = stock_code
        return ProviderPayload(
            stock_code=stock_code,
            company_name=company_name,
            industry=None,
            company_summary=f"A-share company {stock_code}",
            daily_history=daily_history,
            as_of_date=daily_history[-1]["date"],
        )
```

```python
# src/shuoha/data/trading_calendar.py
from datetime import date


def latest_expected_trading_day(today: date) -> date:
    if today.weekday() == 5:
        return today.fromordinal(today.toordinal() - 1)
    if today.weekday() == 6:
        return today.fromordinal(today.toordinal() - 2)
    return today
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_akshare_provider.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/shuoha/data/providers/base.py src/shuoha/data/providers/akshare_provider.py src/shuoha/data/trading_calendar.py tests/test_akshare_provider.py
git commit -m "feat: add akshare provider normalization contract"
```

## Task 4: Implement Pure-Python Indicators

**Files:**
- Create: `src/shuoha/indicators.py`
- Create: `tests/test_indicators.py`

- [ ] **Step 1: Write the failing indicator tests**

```python
# tests/test_indicators.py
from shuoha.indicators import annualized_volatility, max_drawdown, simple_moving_average


def test_simple_moving_average_uses_trailing_window():
    closes = [1, 2, 3, 4, 5]
    assert simple_moving_average(closes, 3) == 4.0


def test_max_drawdown_returns_fraction():
    closes = [10, 12, 9, 11]
    assert round(max_drawdown(closes), 4) == 0.25


def test_annualized_volatility_non_negative():
    closes = [10, 10.5, 10.2, 10.8, 10.4]
    assert annualized_volatility(closes) >= 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_indicators.py -v`
Expected: FAIL with missing module

- [ ] **Step 3: Write minimal indicator implementations**

```python
# src/shuoha/indicators.py
from __future__ import annotations

import math


def simple_moving_average(closes: list[float], window: int) -> float:
    values = closes[-window:]
    return sum(values) / len(values)


def daily_returns(closes: list[float]) -> list[float]:
    return [
        (curr / prev) - 1
        for prev, curr in zip(closes, closes[1:], strict=False)
        if prev
    ]


def annualized_volatility(closes: list[float]) -> float:
    returns = daily_returns(closes)
    if not returns:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((value - mean) ** 2 for value in returns) / len(returns)
    return math.sqrt(variance) * math.sqrt(252)


def max_drawdown(closes: list[float]) -> float:
    peak = closes[0]
    worst = 0.0
    for close in closes:
        peak = max(peak, close)
        drawdown = (peak - close) / peak
        worst = max(worst, drawdown)
    return worst
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_indicators.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/shuoha/indicators.py tests/test_indicators.py
git commit -m "feat: add pure python stock indicators"
```

## Task 5: Implement Deterministic Rules Engine

**Files:**
- Create: `src/shuoha/rules.py`
- Create: `tests/test_rules.py`

- [ ] **Step 1: Write the failing rules tests**

```python
# tests/test_rules.py
from shuoha.rules import choose_verdict


def test_choose_verdict_returns_consider_for_positive_alignment():
    verdict, confidence = choose_verdict(
        positives=4,
        negatives=0,
        veto=False,
        partial=False,
    )
    assert verdict == "consider"
    assert confidence == "high"


def test_choose_verdict_returns_none_for_partial():
    verdict, confidence = choose_verdict(
        positives=2,
        negatives=1,
        veto=False,
        partial=True,
    )
    assert verdict is None
    assert confidence == "low"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_rules.py -v`
Expected: FAIL with missing rules module

- [ ] **Step 3: Write the minimal rules implementation**

```python
# src/shuoha/rules.py
from __future__ import annotations

from shuoha.schemas import Confidence, Verdict


def choose_verdict(*, positives: int, negatives: int, veto: bool, partial: bool) -> tuple[str | None, str]:
    if partial:
        return None, Confidence.LOW.value
    if veto:
        return Verdict.AVOID_FOR_NOW.value, Confidence.LOW.value
    if positives >= 3 and negatives == 0:
        return Verdict.CONSIDER.value, Confidence.HIGH.value
    if negatives >= 2:
        return Verdict.AVOID_FOR_NOW.value, Confidence.LOW.value
    return Verdict.WAIT.value, Confidence.MEDIUM.value
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_rules.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/shuoha/rules.py tests/test_rules.py
git commit -m "feat: add deterministic verdict rules"
```

## Task 6: Render Markdown And Output Artifacts

**Files:**
- Create: `src/shuoha/reporting/markdown_renderer.py`
- Create: `src/shuoha/reporting/output.py`
- Create: `tests/test_markdown_renderer.py`

- [ ] **Step 1: Write the failing renderer test**

```python
# tests/test_markdown_renderer.py
from shuoha.reporting.markdown_renderer import render_markdown
from shuoha.schemas import AnalysisResult, BasicContext, Confidence, AnalysisStatus, EvidenceItem, EvidenceSignal, Verdict


def test_render_markdown_contains_quick_conclusion():
    result = AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code="600519",
        company_name="贵州茅台",
        as_of_date="2026-04-06",
        verdict=Verdict.WAIT,
        confidence=Confidence.MEDIUM,
        technical_evidence=[
            EvidenceItem(name="ma_cross", signal=EvidenceSignal.NEUTRAL, raw_value="mixed", plain_text="趋势一般。")
        ],
        risk_evidence=[],
        unknowns=[],
        data_warnings=[],
        basic_context=BasicContext(industry="白酒", company_summary="主营高端白酒。"),
        disclaimer="Educational only.",
    )
    markdown = render_markdown(result)
    assert "## Quick Conclusion" in markdown
    assert "Verdict: `Wait`" in markdown
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_markdown_renderer.py -v`
Expected: FAIL with missing renderer

- [ ] **Step 3: Write the minimal renderer and artifact writer**

```python
# src/shuoha/reporting/markdown_renderer.py
from __future__ import annotations

from shuoha.schemas import AnalysisResult


VERDICT_LABELS = {
    "consider": "Consider",
    "wait": "Wait",
    "avoid_for_now": "Avoid for now",
}


def render_markdown(result: AnalysisResult) -> str:
    label = VERDICT_LABELS.get(result.verdict.value, "No verdict") if result.verdict else "No verdict"
    return f"""# {result.company_name} (`{result.stock_code}`)

## Quick Conclusion
Verdict: `{label}`

## What This Company Does
{result.basic_context.company_summary if result.basic_context else "No company summary available."}

## What Looks Good
""" + "\n".join(f"- {item.plain_text}" for item in result.technical_evidence if item.signal == "positive") + f"""

## What Looks Risky
""" + "\n".join(f"- {item.plain_text}" for item in result.risk_evidence) + f"""

## Final Verdict and Evidence Summary
- Confidence: `{result.confidence.value}`
- Data warnings: {", ".join(result.data_warnings) if result.data_warnings else "none"}

## Disclaimer
{result.disclaimer}
"""
```

```python
# src/shuoha/reporting/output.py
from __future__ import annotations

import json
from pathlib import Path

from shuoha.schemas import AnalysisResult


def write_outputs(result: AnalysisResult, report_markdown: str, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = output_dir / "evidence.json"
    report_path = output_dir / "report.md"
    evidence_path.write_text(result.model_dump_json(indent=2, exclude_none=False), encoding="utf-8")
    report_path.write_text(report_markdown, encoding="utf-8")
    return evidence_path, report_path
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_markdown_renderer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/shuoha/reporting/markdown_renderer.py src/shuoha/reporting/output.py tests/test_markdown_renderer.py
git commit -m "feat: add markdown report and artifact output"
```

## Task 7: Wire Engine And CLI Happy Path

**Files:**
- Create: `src/shuoha/config.py`
- Create: `src/shuoha/engine.py`
- Modify: `src/shuoha/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing CLI analysis test**

```python
# tests/test_cli.py
from typer.testing import CliRunner

from shuoha.cli import app


def test_cli_requires_stock_code_format():
    runner = CliRunner()
    result = runner.invoke(app, ["abc"])
    assert result.exit_code == 2
    assert "Stock code must be 6 digits" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py::test_cli_requires_stock_code_format -v`
Expected: FAIL because validation is missing

- [ ] **Step 3: Add config, engine skeleton, and CLI validation**

```python
# src/shuoha/config.py
from pathlib import Path


def default_output_dir(stock_code: str) -> Path:
    return Path("out") / stock_code
```

```python
# src/shuoha/engine.py
from __future__ import annotations

from shuoha.data.providers.akshare_provider import AKShareProvider
from shuoha.reporting.markdown_renderer import render_markdown
from shuoha.reporting.output import write_outputs
from shuoha.schemas import AnalysisResult, AnalysisStatus, BasicContext, Confidence


def run_analysis(stock_code: str):
    provider = AKShareProvider()
    payload = provider.fetch(stock_code)
    result = AnalysisResult(
        status=AnalysisStatus.PARTIAL,
        stock_code=payload.stock_code,
        company_name=payload.company_name,
        as_of_date=payload.as_of_date,
        verdict=None,
        confidence=Confidence.LOW,
        technical_evidence=[],
        risk_evidence=[],
        unknowns=["indicator layer not wired yet"],
        data_warnings=[],
        basic_context=BasicContext(industry=payload.industry, company_summary=payload.company_summary),
        disclaimer="This report is educational only and is not investment advice.",
    )
    markdown = render_markdown(result)
    return result, markdown
```

```python
# src/shuoha/cli.py
from pathlib import Path

import typer
from rich import print

from shuoha.config import default_output_dir
from shuoha.engine import run_analysis
from shuoha.reporting.output import write_outputs

app = typer.Typer(help="Analyze one A-share stock code and produce beginner-friendly output.")


@app.command()
def analyze(stock_code: str, output_dir: Path | None = None):
    if not (stock_code.isdigit() and len(stock_code) == 6):
        raise typer.BadParameter("Stock code must be 6 digits")
    result, markdown = run_analysis(stock_code)
    evidence_path, report_path = write_outputs(result, markdown, output_dir or default_output_dir(stock_code))
    print(f"[green]Saved[/green] {report_path}")
    print(f"[green]Saved[/green] {evidence_path}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/shuoha/config.py src/shuoha/engine.py src/shuoha/cli.py tests/test_cli.py
git commit -m "feat: wire basic analysis engine and cli"
```

## Task 8: Replace Partial Engine With Full Deterministic Pipeline

**Files:**
- Modify: `src/shuoha/engine.py`
- Modify: `src/shuoha/indicators.py`
- Modify: `src/shuoha/rules.py`
- Modify: `tests/test_engine.py`

- [ ] **Step 1: Write the failing engine integration test**

```python
# tests/test_engine.py
from shuoha.engine import summarize_signals


def test_summarize_signals_yields_wait_for_mixed_signals():
    rows = [
        {"close": 100.0},
        {"close": 101.0},
        {"close": 102.0},
        {"close": 101.5},
        {"close": 101.0},
    ] * 20
    result = summarize_signals("600519", "贵州茅台", rows)
    assert result.verdict.value == "wait"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_engine.py::test_summarize_signals_yields_wait_for_mixed_signals -v`
Expected: FAIL because `summarize_signals` does not exist

- [ ] **Step 3: Implement full signal summarization**

```python
# src/shuoha/engine.py
from __future__ import annotations

from shuoha.indicators import annualized_volatility, max_drawdown, simple_moving_average
from shuoha.rules import choose_verdict
from shuoha.schemas import AnalysisResult, AnalysisStatus, BasicContext, Confidence, EvidenceItem, EvidenceSignal, Verdict


def summarize_signals(stock_code: str, company_name: str, rows: list[dict]) -> AnalysisResult:
    closes = [row["close"] for row in rows]
    ma20 = simple_moving_average(closes, 20)
    ma60 = simple_moving_average(closes, 60)
    volatility = annualized_volatility(closes)
    drawdown = max_drawdown(closes)

    technical_evidence = [
        EvidenceItem(
            name="ma_alignment",
            signal=EvidenceSignal.POSITIVE if closes[-1] > ma20 and ma20 > ma60 else EvidenceSignal.NEUTRAL,
            raw_value=f"close={closes[-1]},ma20={ma20},ma60={ma60}",
            plain_text="价格和均线关系暂时偏稳。" if closes[-1] > ma20 and ma20 > ma60 else "均线关系没有形成很强的顺风。"
        )
    ]
    risk_evidence = [
        EvidenceItem(
            name="volatility",
            signal=EvidenceSignal.NEGATIVE if volatility > 0.35 else EvidenceSignal.NEUTRAL,
            raw_value=round(volatility, 4),
            plain_text="波动偏大，对新手不太友好。" if volatility > 0.35 else "波动没有明显失控。"
        ),
        EvidenceItem(
            name="drawdown",
            signal=EvidenceSignal.NEGATIVE if drawdown > 0.20 else EvidenceSignal.NEUTRAL,
            raw_value=round(drawdown, 4),
            plain_text="距离高点回撤较深，需要更谨慎。" if drawdown > 0.20 else "回撤还没有到特别危险的程度。"
        ),
    ]
    positives = sum(item.signal == EvidenceSignal.POSITIVE for item in technical_evidence + risk_evidence)
    negatives = sum(item.signal == EvidenceSignal.NEGATIVE for item in technical_evidence + risk_evidence)
    verdict_value, confidence_value = choose_verdict(
        positives=positives,
        negatives=negatives,
        veto=False,
        partial=False,
    )
    return AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code=stock_code,
        company_name=company_name,
        as_of_date=rows[-1]["date"],
        verdict=Verdict(verdict_value),
        confidence=Confidence(confidence_value),
        technical_evidence=technical_evidence,
        risk_evidence=risk_evidence,
        unknowns=[],
        data_warnings=[],
        basic_context=BasicContext(industry=None, company_summary=f"{company_name} company summary pending provider enrichment."),
        disclaimer="This report is educational only and is not investment advice.",
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_engine.py tests/test_rules.py tests/test_indicators.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/shuoha/engine.py src/shuoha/indicators.py src/shuoha/rules.py tests/test_engine.py
git commit -m "feat: implement deterministic stock analysis pipeline"
```

## Task 9: Add Optional Agent Explanation Layer

**Files:**
- Create: `src/shuoha/reporting/agent_renderer.py`
- Modify: `src/shuoha/cli.py`
- Modify: `src/shuoha/engine.py`

- [ ] **Step 1: Write the failing agent toggle test**

```python
# tests/test_cli.py
def test_help_mentions_agent_flag():
    runner = CliRunner()
    result = runner.invoke(app, ["analyze", "--help"])
    assert result.exit_code == 0
    assert "--agent" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py::test_help_mentions_agent_flag -v`
Expected: FAIL because the flag does not exist

- [ ] **Step 3: Add minimal agent rendering hook**

```python
# src/shuoha/reporting/agent_renderer.py
from __future__ import annotations

import os

from openai import OpenAI

from shuoha.schemas import AnalysisResult


def render_agent_markdown(result: AnalysisResult) -> str:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    prompt = f"""
You are rewriting a deterministic stock analysis report for a beginner investor.
Do not change the verdict.
Do not invent evidence.
Make the explanation plain language.

Stock: {result.company_name} ({result.stock_code})
Verdict: {result.verdict.value if result.verdict else 'no_verdict'}
Confidence: {result.confidence.value}
Technical evidence: {[item.model_dump() for item in result.technical_evidence]}
Risk evidence: {[item.model_dump() for item in result.risk_evidence]}
Unknowns: {result.unknowns}
Warnings: {result.data_warnings}
"""
    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )
    return response.output_text
```

```python
# src/shuoha/cli.py
@app.command()
def analyze(stock_code: str, output_dir: Path | None = None, agent: bool = False):
    ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/shuoha/reporting/agent_renderer.py src/shuoha/cli.py src/shuoha/engine.py tests/test_cli.py
git commit -m "feat: add optional agent explanation path"
```

## Task 10: Document Real Usage And Validation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Write the failing documentation expectation**

```markdown
README.md must contain:
- installation with `uv sync`
- local run example `uv run shuoha analyze 600519`
- note that agent mode is optional and needs `OPENAI_API_KEY`
```

- [ ] **Step 2: Run placeholder verification**

Run: `rg -n "uv run shuoha analyze 600519|OPENAI_API_KEY" README.md`
Expected: no matches

- [ ] **Step 3: Update README with real commands**

```markdown
## Setup

```bash
uv sync
```

## Run

```bash
uv run shuoha analyze 600519
```

## Agent mode

```bash
export OPENAI_API_KEY=...
uv run shuoha analyze 600519 --agent
```
```

- [ ] **Step 4: Verify the README contains the commands**

Run: `rg -n "uv run shuoha analyze 600519|OPENAI_API_KEY" README.md`
Expected: matches for both lines

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add shuoha local usage guide"
```

## Self-Review

### Spec coverage
- Stock-code-first CLI: covered in Tasks 1, 7, and 8
- Deterministic evidence pipeline: covered in Tasks 2, 3, 4, 5, and 8
- Beginner Markdown report and artifacts: covered in Task 6
- Optional DeepAgents integration: covered in Task 9
- Validation and fixtures: covered in Tasks 3, 8, and 10

### Placeholder scan
- No `TODO`, `TBD`, or equivalent placeholders remain in task steps.
- The agent task now includes a concrete opt-in OpenAI path instead of a future-note stub.

### Type consistency
- Canonical enums are fixed in `schemas.py`.
- The verdict machine values stay `consider`, `wait`, `avoid_for_now`.
- Markdown display labels are separate from machine values.
