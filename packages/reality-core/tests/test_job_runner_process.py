"""The isolated job child must not write bytecode into a signed application bundle."""

from __future__ import annotations

import sys

from reality.jobs.runner import child_command


def test_child_inherits_the_bytecode_policy(monkeypatch):
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    command = child_command("ten_1", "run_1", "token")
    assert command[1] == "-B"
    assert command[2:] == [
        "-m",
        "reality.jobs.runner",
        "ten_1",
        "run_1",
        "token",
        "--session-info-stdin",
    ]


def test_child_keeps_the_default_when_bytecode_is_allowed(monkeypatch):
    monkeypatch.setattr(sys, "dont_write_bytecode", False)
    assert "-B" not in child_command("ten_1", "run_1", "token")
