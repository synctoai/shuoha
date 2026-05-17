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
