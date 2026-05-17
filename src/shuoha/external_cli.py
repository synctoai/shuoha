from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
import shutil
import subprocess
import tempfile


class ExternalCliError(RuntimeError):
    pass


ProgressReporter = Callable[[str], None]


def _notify(progress: ProgressReporter | None, message: str) -> None:
    if progress is not None:
        progress(message)


def run_codex_exec(
    prompt: str,
    *,
    cwd: Path,
    progress: ProgressReporter | None = None,
    heartbeat_seconds: int = 30,
) -> str:
    if shutil.which("codex") is None:
        raise ExternalCliError("未找到 codex 命令，请先安装并登录 Codex CLI。")
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "codex-report.md"
        args = [
            "codex",
            "exec",
            "--cd",
            str(cwd),
            "--skip-git-repo-check",
            "--output-last-message",
            str(output_path),
            "-",
        ]
        process = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
        )

        waited_seconds = 0
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(process.communicate, prompt)
            while True:
                try:
                    stdout, stderr = future.result(timeout=heartbeat_seconds)
                    break
                except TimeoutError:
                    waited_seconds += heartbeat_seconds
                    _notify(progress, f"Codex 仍在分析中，已等待 {waited_seconds} 秒...")

        if process.returncode != 0:
            detail = stderr.strip() or stdout.strip() or f"exit code {process.returncode}"
            raise ExternalCliError(f"codex 执行失败：{detail}")
        if not output_path.exists():
            raise ExternalCliError("codex 没有生成报告。")
        report = output_path.read_text(encoding="utf-8").strip()
        if not report:
            raise ExternalCliError("codex 没有生成报告。")
        return report
