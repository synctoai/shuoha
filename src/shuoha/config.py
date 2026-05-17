from datetime import date
from pathlib import Path


def default_output_dir(stock_code: str) -> Path:
    return Path("out") / stock_code


def default_codex_output_dir(today: date | None = None) -> Path:
    value = today or date.today()
    return Path("out") / "codex" / value.isoformat()


def default_cache_dir() -> Path:
    return Path(".cache") / "shuoha" / "provider"
