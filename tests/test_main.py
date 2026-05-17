import subprocess
import sys


def test_module_entrypoint_shows_help():
    result = subprocess.run(
        [sys.executable, "-m", "shuoha", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "面向投资小白的 A 股分析 CLI" in result.stdout
    assert "shuoha analyze 600519" in result.stdout
