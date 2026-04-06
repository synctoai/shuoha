from pathlib import Path


def test_release_workflow_collects_akshare_package_data():
    workflow = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "--collect-all akshare" in workflow
