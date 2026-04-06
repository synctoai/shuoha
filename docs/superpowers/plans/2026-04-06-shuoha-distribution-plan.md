# Shuoha Distribution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a beginner-friendly distribution path so users can install `shuoha` with one command on macOS and Windows without setting up Python or `uv`.

**Architecture:** Build release artifacts as standalone binaries with PyInstaller, publish them through GitHub Releases, and install them via platform-specific scripts that download the correct asset, place it in a user-writable bin directory, and update user PATH. Keep the existing Python/`uv` path for contributors only.

**Tech Stack:** Python 3.12, Typer, PyInstaller, GitHub Actions, POSIX shell, PowerShell, pytest

---

### Task 1: Add a module entrypoint for packaged execution

**Files:**
- Create: `src/shuoha/__main__.py`
- Test: `tests/test_main.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --extra dev pytest tests/test_main.py -v`
Expected: FAIL because `python -m shuoha` has no `__main__` module.

- [ ] **Step 3: Write minimal implementation**

```python
from shuoha.cli import app


def main() -> None:
    app()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --extra dev pytest tests/test_main.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/shuoha/__main__.py tests/test_main.py
git commit -m "feat: add module entrypoint for packaged cli"
```

### Task 2: Add installer and uninstaller scripts

**Files:**
- Create: `scripts/install.sh`
- Create: `scripts/uninstall.sh`
- Create: `scripts/install.ps1`
- Create: `scripts/uninstall.ps1`
- Create: `docs/distribution.md`

- [ ] **Step 1: Add scripts with stable contract**

Behavior:
- macOS/Linux shell script downloads release assets from `synctoai/shuoha`
- PowerShell script downloads Windows release asset from `synctoai/shuoha`
- default version is `latest`
- shell script installs to `~/.local/bin/shuoha`
- PowerShell installs to `%USERPROFILE%\\.shuoha\\bin\\shuoha.exe`
- installer updates user-level PATH
- uninstaller removes binary and PATH injection markers

- [ ] **Step 2: Verify shell syntax**

Run: `bash -n scripts/install.sh scripts/uninstall.sh`
Expected: exit code `0`

- [ ] **Step 3: Document the contract**

Document:
- supported platforms
- release asset names
- environment variables / parameters
- install locations
- uninstall behavior

- [ ] **Step 4: Commit**

```bash
git add scripts/install.sh scripts/uninstall.sh scripts/install.ps1 scripts/uninstall.ps1 docs/distribution.md
git commit -m "feat: add release installer scripts"
```

### Task 3: Add CI release workflow

**Files:**
- Create: `.github/workflows/release.yml`
- Modify: `pyproject.toml`

- [ ] **Step 1: Add build dependency**

Update `pyproject.toml`:
- add `pyinstaller>=6.13.0` to `project.optional-dependencies.dev`

- [ ] **Step 2: Add workflow**

Workflow behavior:
- trigger on `push.tags: v*`
- build standalone binaries for:
  - `macos-13` -> `shuoha-darwin-amd64.tar.gz`
  - `macos-14` -> `shuoha-darwin-arm64.tar.gz`
  - `windows-latest` -> `shuoha-windows-amd64.zip`
- run `python -m PyInstaller --name shuoha --onefile src/shuoha/__main__.py --paths src`
- upload assets to GitHub Release

- [ ] **Step 3: Verify configuration**

Run: `uv sync --extra dev`
Expected: succeeds with updated dev dependency metadata

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/release.yml pyproject.toml uv.lock
git commit -m "feat: add release workflow for standalone binaries"
```

### Task 4: Rewrite user installation docs

**Files:**
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Move one-line install to the top of README**

Add user-facing sections for:
- macOS install
- Windows install
- upgrade
- uninstall

- [ ] **Step 2: Keep Python/uv under developer docs**

README should stop presenting `uv run` as the first user entrypoint and instead present it as a contributor path.

- [ ] **Step 3: Update contributor release instructions**

Document:
- creating a release tag
- expected release assets
- how install scripts resolve versions

- [ ] **Step 4: Verify docs match scripts**

Run: `rg -n "install.sh|install.ps1|latest|shuoha-darwin|shuoha-windows" README.md CONTRIBUTING.md docs/distribution.md`
Expected: references align with actual script/workflow names.

- [ ] **Step 5: Commit**

```bash
git add README.md CONTRIBUTING.md CHANGELOG.md
git commit -m "docs: document one-line binary installation"
```

### Task 5: Final verification

**Files:**
- Verify entire repo state

- [ ] **Step 1: Run targeted tests**

Run: `uv run --extra dev pytest tests/test_main.py tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 2: Run full test suite**

Run: `uv run --extra dev pytest -v`
Expected: PASS

- [ ] **Step 3: Verify shell scripts parse**

Run: `bash -n scripts/install.sh scripts/uninstall.sh`
Expected: exit code `0`

- [ ] **Step 4: Check working tree**

Run: `git status --short`
Expected: clean working tree
