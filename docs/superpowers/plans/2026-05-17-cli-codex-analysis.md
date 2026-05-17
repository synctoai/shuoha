# CLI Codex Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `--cli local` and `--cli codex` to `shuoha analyze`, with Codex producing a multi-stock deep research dashboard from shuoha-prepared AKShare and indicator context.

**Architecture:** Keep the existing local deterministic pipeline as the default. Add a small external-CLI path that prepares per-stock contexts with `AKShareProvider` and `summarize_signals()`, builds a Codex prompt, runs `codex exec`, and writes one combined Markdown report.

**Tech Stack:** Python 3.12, Typer, Pydantic, pytest, AKShare provider already in the repo, local `codex exec` subprocess.

---

## File Map

- Modify `src/shuoha/cli.py`: accept multiple stock code arguments and a `--cli` backend option.
- Modify `src/shuoha/config.py`: add a default Codex output directory helper.
- Create `src/shuoha/external_cli.py`: run `codex exec` and surface clear failures.
- Create `src/shuoha/codex_analysis.py`: prepare stock contexts and build the Codex prompt.
- Modify `src/shuoha/reporting/output.py`: add a simple Markdown-only report writer.
- Modify `README.md`: document `--cli local` and `--cli codex`.
- Modify `tests/test_cli.py`: cover CLI backend behavior.
- Create `tests/test_codex_analysis.py`: cover prompt building and partial data handling.
- Create `tests/test_external_cli.py`: cover Codex subprocess behavior.

---

### Task 1: CLI Backend Option

**Files:**
- Modify: `src/shuoha/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Add these tests to `tests/test_cli.py`:

```python
def test_help_mentions_cli_backend_option():
    runner = CliRunner()
    result = runner.invoke(app, ["analyze", "--help"])
    assert result.exit_code == 0
    assert "--cli" in result.stdout


def test_local_cli_rejects_multiple_stock_codes():
    runner = CliRunner()
    result = runner.invoke(app, ["analyze", "600519", "000657", "--cli", "local"])
    assert result.exit_code == 2
    assert "多股票分析目前请使用 --cli codex" in result.stdout


def test_codex_cli_accepts_multiple_stock_codes(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "shuoha.cli.run_codex_analysis",
        lambda stock_codes: "🎯 2026-05-17 决策仪表盘\n共分析2只股票",
    )
    monkeypatch.setattr(
        "shuoha.cli.write_markdown_report",
        lambda report_markdown, output_dir: tmp_path / "report.md",
    )

    runner = CliRunner()
    result = runner.invoke(app, ["analyze", "000657", "600105", "--cli", "codex"])

    assert result.exit_code == 0
    assert "决策仪表盘" in result.stdout
    assert "已生成" in result.stdout
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/test_cli.py::test_help_mentions_cli_backend_option tests/test_cli.py::test_local_cli_rejects_multiple_stock_codes tests/test_cli.py::test_codex_cli_accepts_multiple_stock_codes -v
```

Expected: failures because `--cli`, `run_codex_analysis`, and `write_markdown_report` are not implemented.

- [ ] **Step 3: Implement minimal CLI changes**

Update `src/shuoha/cli.py` so `analyze` receives `stock_codes: list[str]`, validates each code, and branches on `cli_backend`.

Implementation shape:

```python
from typing import Annotated

import typer

from shuoha.config import default_codex_output_dir, default_output_dir
from shuoha.codex_analysis import run_codex_analysis
from shuoha.reporting.output import write_markdown_report, write_outputs


@app.command()
def analyze(
    stock_codes: Annotated[list[str], typer.Argument()],
    output_dir: Path | None = None,
    agent: bool = False,
    cli_backend: str = typer.Option(
        "local",
        "--cli",
        help="分析后端：local 使用本地确定性分析，codex 使用 Codex CLI 深度分析。",
    ),
    full: bool = typer.Option(False, "--full/--brief", help="控制终端输出模式：完整报告或电梯摘要。"),
) -> None:
    if cli_backend not in {"local", "codex"}:
        typer.echo("cli 只能是 local 或 codex")
        raise typer.Exit(2)
    for stock_code in stock_codes:
        if not (stock_code.isdigit() and len(stock_code) == 6):
            typer.echo("股票代码必须是 6 位数字")
            raise typer.Exit(2)
    if cli_backend == "local":
        if len(stock_codes) != 1:
            typer.echo("多股票分析目前请使用 --cli codex")
            raise typer.Exit(2)
        stock_code = stock_codes[0]
        result, markdown = run_analysis(stock_code, agent=agent)
        ...
        return
    markdown = run_codex_analysis(stock_codes)
    print(markdown)
    report_path = write_markdown_report(markdown, output_dir or default_codex_output_dir())
    print(f"[green]已生成[/green] {report_path}")
```

Keep the existing local branch output behavior exactly as it is after assigning `stock_code = stock_codes[0]`.

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
uv run pytest tests/test_cli.py -v
```

Expected: all CLI tests pass.

---

### Task 2: Codex Prompt Builder And Context Preparation

**Files:**
- Create: `src/shuoha/codex_analysis.py`
- Test: `tests/test_codex_analysis.py`

- [ ] **Step 1: Write failing prompt tests**

Create `tests/test_codex_analysis.py`:

```python
from shuoha.codex_analysis import CodexStockContext, build_codex_prompt
from shuoha.schemas import AnalysisResult, AnalysisStatus, BasicContext, Confidence, EvidenceItem, EvidenceSignal, Verdict, VerdictBias


def _result(stock_code="000657"):
    return AnalysisResult(
        status=AnalysisStatus.OK,
        stock_code=stock_code,
        company_name="中钨高新",
        as_of_date="2026-05-17",
        verdict=Verdict.WAIT,
        bias=VerdictBias.BULLISH,
        confidence=Confidence.MEDIUM,
        technical_evidence=[
            EvidenceItem(name="ma_alignment", signal=EvidenceSignal.POSITIVE, raw_value="close=10.00,ma20=9.00,ma60=8.00", plain_text="趋势暂时偏强。")
        ],
        risk_evidence=[
            EvidenceItem(name="drawdown", signal=EvidenceSignal.NEGATIVE, raw_value=0.21, plain_text="回撤较深。")
        ],
        unknowns=[],
        data_warnings=[],
        basic_context=BasicContext(industry="有色金属", company_summary="主营硬质合金。"),
        disclaimer="本报告仅供学习交流，不构成投资建议。",
    )


def test_build_codex_prompt_includes_dashboard_requirements_and_stock_context():
    prompt = build_codex_prompt([CodexStockContext(stock_code="000657", result=_result())])
    assert "000657" in prompt
    assert "中钨高新" in prompt
    assert "决策仪表盘" in prompt
    assert "重要信息速览" in prompt
    assert "风险警报" in prompt
    assert "利好催化" in prompt
    assert "未查到可靠来源" in prompt
    assert "不要编造" in prompt


def test_build_codex_prompt_includes_partial_context_warning():
    prompt = build_codex_prompt(
        [
            CodexStockContext(
                stock_code="600105",
                result=None,
                data_warnings=["本地 AKShare 数据拉取失败：network down"],
            )
        ]
    )
    assert "600105" in prompt
    assert "本地 AKShare 数据拉取失败" in prompt
    assert "仍需继续研究该股票" in prompt
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/test_codex_analysis.py -v
```

Expected: import failure because `shuoha.codex_analysis` does not exist.

- [ ] **Step 3: Implement prompt builder**

Create `src/shuoha/codex_analysis.py`:

```python
from dataclasses import dataclass, field

from shuoha.schemas import AnalysisResult


@dataclass
class CodexStockContext:
    stock_code: str
    result: AnalysisResult | None = None
    data_warnings: list[str] = field(default_factory=list)


def _format_result(result: AnalysisResult) -> str:
    evidence = result.technical_evidence + result.risk_evidence
    evidence_lines = [
        f"- {item.name}: {item.signal.value}; raw={item.raw_value}; explanation={item.plain_text}"
        for item in evidence
    ]
    context = result.basic_context
    return "\n".join(
        [
            f"股票：{result.company_name} ({result.stock_code})",
            f"数据日期：{result.as_of_date}",
            f"行业：{context.industry if context else '未知'}",
            f"公司简介：{context.company_summary if context else '未知'}",
            f"本地确定性结论参考：{result.verdict.value if result.verdict else 'no_verdict'}",
            f"偏向：{result.bias.value}",
            f"置信度：{result.confidence.value}",
            "本地技术/风险证据：",
            "\n".join(evidence_lines) if evidence_lines else "- 无",
            f"本地数据告警：{result.data_warnings or []}",
        ]
    )


def build_codex_prompt(contexts: list[CodexStockContext]) -> str:
    sections = []
    for context in contexts:
        if context.result is None:
            sections.append(
                "\n".join(
                    [
                        f"股票：{context.stock_code}",
                        "本地 AKShare/指标上下文：不可用。",
                        f"数据告警：{context.data_warnings}",
                        "仍需继续研究该股票，但必须披露本地市场数据不可用。",
                    ]
                )
            )
        else:
            sections.append(_format_result(context.result))
    return f"""你是 shuoha 的外部 CLI 深度研究分析器。

请基于下面由 shuoha 复用 AKShare 和本地指标层准备的上下文，继续研究这些 A 股股票的今日或最近交易日新闻、公告、资金流、舆情、行业催化和风险。

硬性要求：
- 用中文 Markdown 输出。
- 输出标题必须包含“决策仪表盘”。
- 包含“共分析N只股票 | 🟢买入:x 🟡观望:y 🔴卖出:z”格式的总览。
- 每只股票必须包含“重要信息速览”“风险警报”“利好催化”“最新动态”。
- 每只股票给出结论、0-100 评分和方向判断。
- 可以参考本地确定性结论，但最终结论允许结合新闻和基本面信息重新判断。
- 不要编造新闻、公告、资金数据、业绩数据或来源。
- 无法确认的信息必须写“未查到可靠来源”。
- 最后写“生成时间: HH:MM”。

股票上下文：

{chr(10).join(f"--- 股票上下文 {index + 1} ---{chr(10)}{section}" for index, section in enumerate(sections))}
"""
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
uv run pytest tests/test_codex_analysis.py -v
```

Expected: prompt tests pass.

---

### Task 3: Codex CLI Runner

**Files:**
- Create: `src/shuoha/external_cli.py`
- Test: `tests/test_external_cli.py`

- [ ] **Step 1: Write failing runner tests**

Create `tests/test_external_cli.py`:

```python
import subprocess

import pytest

from shuoha.external_cli import ExternalCliError, run_codex_exec


def test_run_codex_exec_writes_prompt_to_stdin_and_reads_last_message(monkeypatch, tmp_path):
    calls = {}

    def fake_which(name):
        return "/opt/homebrew/bin/codex" if name == "codex" else None

    def fake_run(args, input, text, capture_output, cwd, check):
        calls["args"] = args
        calls["input"] = input
        output_file = args[args.index("--output-last-message") + 1]
        with open(output_file, "w", encoding="utf-8") as file:
            file.write("# report")
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr("shuoha.external_cli.shutil.which", fake_which)
    monkeypatch.setattr("shuoha.external_cli.subprocess.run", fake_run)

    report = run_codex_exec("prompt text", cwd=tmp_path)

    assert report == "# report"
    assert calls["args"][:2] == ["codex", "exec"]
    assert "--output-last-message" in calls["args"]
    assert calls["input"] == "prompt text"


def test_run_codex_exec_raises_when_codex_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("shuoha.external_cli.shutil.which", lambda name: None)
    with pytest.raises(ExternalCliError, match="未找到 codex"):
        run_codex_exec("prompt", cwd=tmp_path)


def test_run_codex_exec_raises_when_output_empty(monkeypatch, tmp_path):
    monkeypatch.setattr("shuoha.external_cli.shutil.which", lambda name: "/bin/codex")
    monkeypatch.setattr(
        "shuoha.external_cli.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr=""),
    )
    with pytest.raises(ExternalCliError, match="没有生成报告"):
        run_codex_exec("prompt", cwd=tmp_path)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/test_external_cli.py -v
```

Expected: import failure because `shuoha.external_cli` does not exist.

- [ ] **Step 3: Implement runner**

Create `src/shuoha/external_cli.py`:

```python
from pathlib import Path
import shutil
import subprocess
import tempfile


class ExternalCliError(RuntimeError):
    pass


def run_codex_exec(prompt: str, *, cwd: Path) -> str:
    if shutil.which("codex") is None:
        raise ExternalCliError("未找到 codex 命令，请先安装并登录 Codex CLI。")
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "codex-report.md"
        args = [
            "codex",
            "exec",
            "--cd",
            str(cwd),
            "--output-last-message",
            str(output_path),
            "-",
        ]
        completed = subprocess.run(
            args,
            input=prompt,
            text=True,
            capture_output=True,
            cwd=cwd,
            check=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
            raise ExternalCliError(f"codex 执行失败：{detail}")
        if not output_path.exists():
            raise ExternalCliError("codex 没有生成报告。")
        report = output_path.read_text(encoding="utf-8").strip()
        if not report:
            raise ExternalCliError("codex 没有生成报告。")
        return report
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
uv run pytest tests/test_external_cli.py -v
```

Expected: runner tests pass.

---

### Task 4: Codex Analysis Orchestration

**Files:**
- Modify: `src/shuoha/codex_analysis.py`
- Test: `tests/test_codex_analysis.py`

- [ ] **Step 1: Write failing orchestration test**

Append to `tests/test_codex_analysis.py`:

```python
from shuoha.data.providers.base import ProviderPayload
from shuoha.codex_analysis import run_codex_analysis


def test_run_codex_analysis_continues_when_one_stock_fetch_fails(monkeypatch):
    payload = ProviderPayload(
        stock_code="000657",
        company_name="中钨高新",
        industry="有色金属",
        company_summary="主营硬质合金。",
        daily_history=[
            {"date": f"2026-04-{day:02d}", "close": float(10 + day / 10), "volume": float(1000 + day)}
            for day in range(1, 31)
        ]
        + [
            {"date": f"2026-05-{day:02d}", "close": float(13 + day / 10), "volume": float(1300 + day)}
            for day in range(1, 31)
        ],
        as_of_date="2026-05-17",
    )

    def fake_fetch(self, stock_code):
        if stock_code == "600105":
            raise RuntimeError("network down")
        return payload

    captured = {}
    monkeypatch.setattr("shuoha.codex_analysis.AKShareProvider.fetch", fake_fetch)
    monkeypatch.setattr(
        "shuoha.codex_analysis.run_codex_exec",
        lambda prompt, cwd: captured.setdefault("prompt", prompt) or "# codex report",
    )

    report = run_codex_analysis(["000657", "600105"])

    assert report == "# codex report"
    assert "000657" in captured["prompt"]
    assert "600105" in captured["prompt"]
    assert "network down" in captured["prompt"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
uv run pytest tests/test_codex_analysis.py::test_run_codex_analysis_continues_when_one_stock_fetch_fails -v
```

Expected: failure because `run_codex_analysis` is not implemented.

- [ ] **Step 3: Implement orchestration**

Add to `src/shuoha/codex_analysis.py`:

```python
from pathlib import Path

from shuoha.data.providers.akshare_provider import AKShareProvider
from shuoha.engine import summarize_signals
from shuoha.external_cli import run_codex_exec
from shuoha.schemas import BasicContext


def run_codex_analysis(stock_codes: list[str], *, cwd: Path | None = None) -> str:
    provider = AKShareProvider()
    contexts: list[CodexStockContext] = []
    for stock_code in stock_codes:
        try:
            payload = provider.fetch(stock_code)
            result = summarize_signals(payload.stock_code, payload.company_name, payload.daily_history)
            result.basic_context = BasicContext(industry=payload.industry, company_summary=payload.company_summary)
            contexts.append(CodexStockContext(stock_code=stock_code, result=result))
        except Exception as exc:
            contexts.append(
                CodexStockContext(
                    stock_code=stock_code,
                    result=None,
                    data_warnings=[f"本地 AKShare 数据拉取失败：{exc}"],
                )
            )
    prompt = build_codex_prompt(contexts)
    return run_codex_exec(prompt, cwd=cwd or Path.cwd())
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
uv run pytest tests/test_codex_analysis.py -v
```

Expected: all Codex analysis tests pass.

---

### Task 5: Markdown-Only Output Path

**Files:**
- Modify: `src/shuoha/config.py`
- Modify: `src/shuoha/reporting/output.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing output-dir assertion**

Extend `test_codex_cli_accepts_multiple_stock_codes` in `tests/test_cli.py` so the fake `write_markdown_report` captures `output_dir`:

```python
written = {}

def fake_write_markdown_report(report_markdown, output_dir):
    written["markdown"] = report_markdown
    written["output_dir"] = output_dir
    return tmp_path / "report.md"

monkeypatch.setattr("shuoha.cli.write_markdown_report", fake_write_markdown_report)
...
assert written["output_dir"].parts[-3:] == ("out", "codex", "2026-05-17")
```

If freezing the date is awkward, assert only that `"codex"` appears in `written["output_dir"].parts` and add a separate unit test for `default_codex_output_dir(today=date(2026, 5, 17))`.

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
uv run pytest tests/test_cli.py::test_codex_cli_accepts_multiple_stock_codes -v
```

Expected: failure because `default_codex_output_dir` and `write_markdown_report` are not implemented.

- [ ] **Step 3: Implement output helpers**

Add to `src/shuoha/config.py`:

```python
from datetime import date


def default_codex_output_dir(today: date | None = None) -> Path:
    value = today or date.today()
    return Path("out") / "codex" / value.isoformat()
```

Add to `src/shuoha/reporting/output.py`:

```python
def write_markdown_report(report_markdown: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "report.md"
    report_path.write_text(report_markdown, encoding="utf-8")
    return report_path
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
uv run pytest tests/test_cli.py tests/test_codex_analysis.py tests/test_external_cli.py -v
```

Expected: all targeted tests pass.

---

### Task 6: README Documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Add a section near terminal usage:

```markdown
### 外部 CLI 深度分析

默认本地模式仍然是确定性分析：

```bash
shuoha analyze 600519 --cli local
```

如果本机已安装并登录 Codex CLI，可以让 shuoha 复用 AKShare 和本地指标结果，再交给 Codex 继续研究新闻、公告、资金流、舆情和行业催化：

```bash
shuoha analyze 000657 600105 300260 --cli codex
```

`--cli codex` 会生成一份多股票决策仪表盘报告，并写入 `out/codex/<date>/report.md`。
```

- [ ] **Step 2: Run docs-related smoke tests**

Run:

```bash
uv run pytest tests/test_cli.py::test_help_mentions_cli_backend_option -v
```

Expected: PASS.

---

### Task 7: Full Verification

**Files:**
- All modified files.

- [ ] **Step 1: Run full test suite**

Run:

```bash
uv run pytest
```

Expected: all tests pass.

- [ ] **Step 2: Run help smoke manually**

Run:

```bash
uv run shuoha analyze --help
```

Expected: help includes `--cli`, `--full`, `--brief`, and `--agent`.

- [ ] **Step 3: Inspect git diff**

Run:

```bash
git diff -- src tests README.md
```

Expected: diff only contains the scoped CLI backend, Codex runner, prompt builder, output helper, and docs changes.

---

## Self-Review Notes

- Spec coverage: The plan covers `--cli local`, `--cli codex`, AKShare context reuse, Codex prompt construction, subprocess execution, report output, missing Codex handling, partial AKShare failures, and documentation.
- Placeholder scan: No task uses TBD/TODO or asks for unspecified tests.
- Type consistency: `CodexStockContext`, `build_codex_prompt()`, `run_codex_exec()`, `run_codex_analysis()`, `default_codex_output_dir()`, and `write_markdown_report()` are introduced before use.
