"""The unsigned tester artifact cannot enter a public release path."""

from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[3] / ".github/workflows/macos-release.yml"


def test_tester_beta_is_explicit_and_publication_is_refused():
    workflow = WORKFLOW.read_text()

    assert "tester_beta:" in workflow
    assert 'beta=("--unsigned-tester-beta")' in workflow
    assert "Refuse public unsigned tester beta" in workflow
    assert "inputs.tester_beta && (startsWith(github.ref, 'refs/tags/mac-v') || inputs.publish)" in workflow
    assert "!inputs.tester_beta && (startsWith(github.ref, 'refs/tags/mac-v') || inputs.publish)" in workflow


def test_tester_beta_has_a_distinct_private_artifact_name():
    workflow = WORKFLOW.read_text()

    assert "reality-local-unsigned-tester-beta-" in workflow
    assert "inputs.tester_beta && 'reality-local-unsigned-tester-beta-'" in workflow
