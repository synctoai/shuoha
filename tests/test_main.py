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
    assert "分析一只 A 股股票" in result.stdout
