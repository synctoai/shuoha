from datetime import date
from pathlib import Path


def default_output_dir(stock_code: str) -> Path:
    return Path("out") / stock_code


def default_codex_output_dir(today: date | None = None) -> Path:
    return Path("out") / "codex"


def codex_report_filename(stock_codes: list[str], today: date | None = None) -> str:
    value = today or date.today()
    return f"{'-'.join(stock_codes)}-{value.isoformat()}.md"


def default_cache_dir() -> Path:
    return Path(".cache") / "shuoha" / "provider"
