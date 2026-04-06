from pathlib import Path


def default_output_dir(stock_code: str) -> Path:
    return Path("out") / stock_code
