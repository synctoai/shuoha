from pathlib import Path


def default_output_dir(stock_code: str) -> Path:
    return Path("out") / stock_code


def default_cache_dir() -> Path:
    return Path(".cache") / "shuoha" / "provider"
