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
