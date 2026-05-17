import subprocess

import pytest

from shuoha.external_cli import ExternalCliError, run_codex_exec


def test_run_codex_exec_writes_prompt_to_stdin_and_reads_last_message(monkeypatch, tmp_path):
    calls = {}

    def fake_which(name):
        return "/opt/homebrew/bin/codex" if name == "codex" else None

    class FakeProcess:
        returncode = 0

        def __init__(self, args, stdin, stdout, stderr, text, cwd):
            calls["args"] = args
            calls["cwd"] = cwd

        def communicate(self, input=None):
            calls["input"] = input
            output_file = calls["args"][calls["args"].index("--output-last-message") + 1]
            with open(output_file, "w", encoding="utf-8") as file:
                file.write("# report")
            return "", ""

    def fake_popen(args, stdin, stdout, stderr, text, cwd):
        calls["args"] = args
        return FakeProcess(args, stdin, stdout, stderr, text, cwd)

    monkeypatch.setattr("shuoha.external_cli.shutil.which", fake_which)
    monkeypatch.setattr("shuoha.external_cli.subprocess.Popen", fake_popen)

    report = run_codex_exec("prompt text", cwd=tmp_path)

    assert report == "# report"
    assert calls["args"][:2] == ["codex", "exec"]
    assert "--skip-git-repo-check" in calls["args"]
    assert "--output-last-message" in calls["args"]
    assert calls["input"] == "prompt text"


def test_run_codex_exec_raises_when_codex_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("shuoha.external_cli.shutil.which", lambda name: None)
    with pytest.raises(ExternalCliError, match="未找到 codex"):
        run_codex_exec("prompt", cwd=tmp_path)


def test_run_codex_exec_raises_when_output_empty(monkeypatch, tmp_path):
    monkeypatch.setattr("shuoha.external_cli.shutil.which", lambda name: "/bin/codex")

    class FakeProcess:
        returncode = 0

        def communicate(self, input=None):
            return "", ""

    monkeypatch.setattr("shuoha.external_cli.subprocess.Popen", lambda *args, **kwargs: FakeProcess())
    with pytest.raises(ExternalCliError, match="没有生成报告"):
        run_codex_exec("prompt", cwd=tmp_path)


def test_run_codex_exec_reports_heartbeat_while_waiting(monkeypatch, tmp_path):
    calls = {}
    events = []

    class FakeProcess:
        returncode = 0

        def __init__(self, args, stdin, stdout, stderr, text, cwd):
            calls["args"] = args

        def communicate(self, input=None):
            return "", ""

    class FakeFuture:
        def __init__(self):
            self.calls = 0

        def result(self, timeout):
            self.calls += 1
            if self.calls == 1:
                raise TimeoutError()
            output_file = calls["args"][calls["args"].index("--output-last-message") + 1]
            with open(output_file, "w", encoding="utf-8") as file:
                file.write("# report")
            return "", ""

    class FakeExecutor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def submit(self, fn, prompt):
            return FakeFuture()

    monkeypatch.setattr("shuoha.external_cli.shutil.which", lambda name: "/bin/codex")
    monkeypatch.setattr("shuoha.external_cli.subprocess.Popen", lambda *args, **kwargs: FakeProcess(*args, **kwargs))
    monkeypatch.setattr("shuoha.external_cli.ThreadPoolExecutor", lambda max_workers: FakeExecutor())

    report = run_codex_exec("prompt", cwd=tmp_path, progress=events.append, heartbeat_seconds=30)

    assert report == "# report"
    assert events == ["Codex 仍在分析中，已等待 30 秒..."]
