from pathlib import Path

from shuoha.schemas import AnalysisResult


def write_outputs(result: AnalysisResult, report_markdown: str, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = output_dir / "evidence.json"
    report_path = output_dir / "report.md"
    evidence_path.write_text(result.model_dump_json(indent=2, exclude_none=False), encoding="utf-8")
    report_path.write_text(report_markdown, encoding="utf-8")
    return evidence_path, report_path


def write_markdown_report(report_markdown: str, output_dir: Path, filename: str = "report.md") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / filename
    report_path.write_text(report_markdown, encoding="utf-8")
    return report_path
