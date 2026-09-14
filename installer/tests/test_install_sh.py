"""Dry-run proofs for the self-hosted installer (spec 187).

These tests never touch Docker. They run install.sh with --dry-run and a local
asset directory and inspect what it writes, refuses and prints.
"""

from __future__ import annotations

import base64
import os
import socket
import subprocess
from pathlib import Path

import pytest

INSTALLER_DIR = Path(__file__).resolve().parents[1]
SCRIPT = INSTALLER_DIR / "install.sh"
SHIPPED_ASSETS = [
    "compose.yml",
    "compose.direct.yml",
    "compose.proxy.yml",
    "compose.s3.yml",
    "Caddyfile",
    "README.md",
]
PLACEHOLDERS = ("replace-me", "generated", "changeme", "__REALITY_INSTALLER_VERSION__")


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def run(
    *args: str, cwd: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    arguments = list(args)
    installing = not any(a in arguments for a in ("upgrade", "restore", "--help"))
    if installing and "--domain" not in arguments:
        # The developer stack may hold 8080 and 8001 on this host.
        if "--port" not in arguments:
            arguments += ["--port", str(free_port())]
        if "--mcp-port" not in arguments:
            arguments += ["--mcp-port", str(free_port())]
    environment = {
        **os.environ,
        "REALITY_INSTALLER_SOURCE_DIR": str(INSTALLER_DIR),
        "REALITY_ADMIN_EMAIL": "",
    }
    if env:
        environment.update(env)
    return subprocess.run(
        ["sh", str(SCRIPT), *arguments],
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def read_env(directory: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in (directory / ".env").read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        values[key] = value
    return values


@pytest.fixture
def home(tmp_path: Path) -> Path:
    return tmp_path


def test_dry_run_writes_a_complete_installation_without_placeholders(home: Path):
    result = run("--dry-run", "--version", "0.1.0", cwd=home)

    assert result.returncode == 0, result.stderr
    target = home / "reality"
    for name in [*SHIPPED_ASSETS, "reality.sh", ".env"]:
        assert (target / name).is_file(), name
    assert os.access(target / "reality.sh", os.X_OK)
    assert oct((target / ".env").stat().st_mode & 0o777) == "0o600"

    env = read_env(target)
    text = (target / ".env").read_text()
    for placeholder in PLACEHOLDERS:
        assert placeholder not in text, placeholder
    assert env["REALITY_VERSION"] == "0.1.0"
    assert env["COMPOSE_FILE"] == "compose.yml:compose.direct.yml"
    assert env["COMPOSE_PROJECT_NAME"] == "reality"
    assert env["APP_URL"] == f"http://localhost:{env['REALITY_PORT']}"
    assert env["MCP_URL"] == f"http://localhost:{env['REALITY_MCP_PORT']}/"
    assert env["REALITY_COOKIE_SECURE"] == "false"
    assert env["REALITY_MCP_ENV"] == ""
    assert env["REALITY_PLATFORM_ADMIN_EMAIL"] == "owner@reality.local"
    assert len(env["POSTGRES_PASSWORD"]) == 48
    assert len(env["REALITY_PLATFORM_ADMIN_PASSWORD"]) == 24
    assert "owner@reality.local" in result.stdout
    assert "Dry run" in result.stdout


def test_generated_master_key_is_a_valid_fernet_key(home: Path):
    from cryptography.fernet import Fernet

    run("--dry-run", "--version", "0.1.0", cwd=home)
    key = read_env(home / "reality")["REALITY_MASTER_KEY"]

    assert len(key) == 44
    assert len(base64.urlsafe_b64decode(key)) == 32
    Fernet(key.encode()).encrypt(b"probe")


def test_second_run_changes_nothing_and_points_to_upgrade(home: Path):
    run("--dry-run", "--version", "0.1.0", cwd=home)
    before = (home / "reality" / ".env").read_text()

    result = run("--dry-run", "--version", "0.2.0", cwd=home)

    assert result.returncode == 0
    assert "already installed" in result.stdout
    assert "reality.sh upgrade" in result.stdout
    assert (home / "reality" / ".env").read_text() == before


def test_domain_selects_proxy_mode_with_https_and_mcp_subdomain(home: Path):
    result = run(
        "--dry-run", "--version", "0.1.0", "--domain", "reality.example.com", cwd=home
    )

    assert result.returncode == 0, result.stderr
    env = read_env(home / "reality")
    assert env["COMPOSE_FILE"] == "compose.yml:compose.proxy.yml"
    assert env["REALITY_DOMAIN"] == "reality.example.com"
    assert env["APP_URL"] == "https://reality.example.com"
    assert env["MCP_URL"] == "https://mcp.reality.example.com/"
    assert env["REALITY_COOKIE_SECURE"] == "true"
    assert env["REALITY_MCP_ENV"] == "production"
    caddyfile = (home / "reality" / "Caddyfile").read_text()
    assert "mcp.{$REALITY_DOMAIN}" in caddyfile


def test_domain_must_be_a_bare_hostname(home: Path):
    result = run("--dry-run", "--domain", "https://reality.example.com", cwd=home)

    assert result.returncode == 1
    assert "bare hostname" in result.stderr
    assert not (home / "reality").exists()


def test_email_flag_becomes_the_first_owner(home: Path):
    result = run(
        "--dry-run", "--version", "0.1.0", "--email", "owner@example.com", cwd=home
    )

    assert result.returncode == 0, result.stderr
    assert (
        read_env(home / "reality")["REALITY_PLATFORM_ADMIN_EMAIL"]
        == "owner@example.com"
    )
    assert "No --email given" not in result.stdout


def test_port_and_bind_flow_into_env_and_urls(home: Path):
    result = run(
        "--dry-run",
        "--version",
        "0.1.0",
        "--port",
        "9090",
        "--bind",
        "127.0.0.1",
        cwd=home,
    )

    assert result.returncode == 0, result.stderr
    env = read_env(home / "reality")
    assert env["REALITY_PORT"] == "9090"
    assert env["REALITY_BIND"] == "127.0.0.1"
    assert env["APP_URL"] == "http://localhost:9090"


def fake_docker(home: Path) -> Path:
    """A docker that passes the prerequisite checks and must never be reached otherwise."""
    stub = home / "bin" / "docker"
    stub.parent.mkdir()
    stub.write_text(
        '#!/bin/sh\ncase "$1" in info) exit 0;; compose) exit 0;; esac\necho "unexpected docker $*" >&2; exit 99\n'
    )
    stub.chmod(0o755)
    return stub


def test_busy_port_is_refused_before_anything_is_written(home: Path):
    docker = fake_docker(home)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]

        result = run(
            "--version",
            "0.1.0",
            "--port",
            str(port),
            cwd=home,
            env={"REALITY_DOCKER_BIN": str(docker)},
        )

    assert result.returncode == 1
    assert f"port {port} is already in use" in result.stderr
    assert "--port" in result.stderr
    assert not (home / "reality").exists()


def test_unknown_flag_prints_usage(home: Path):
    result = run("--frobnicate", cwd=home)

    assert result.returncode == 2
    assert "unknown flag" in result.stderr
    assert "Usage:" in result.stderr
    assert not (home / "reality").exists()


def test_missing_docker_is_named_before_any_file_is_written(home: Path):
    result = run(
        "--version",
        "0.1.0",
        cwd=home,
        env={"REALITY_DOCKER_BIN": "/nonexistent/docker"},
    )

    assert result.returncode == 1
    assert "Docker is not installed" in result.stderr
    assert not (home / "reality").exists()


def test_upgrade_rewrites_only_the_version_line(home: Path):
    run("--dry-run", "--version", "0.1.0", cwd=home)
    target = home / "reality"
    before = read_env(target)

    result = run(
        "upgrade", "--dry-run", "--version", "0.2.0", "--dir", str(target), cwd=home
    )

    assert result.returncode == 0, result.stderr
    after = read_env(target)
    assert after["REALITY_VERSION"] == "0.2.0"
    assert {k: v for k, v in after.items() if k != "REALITY_VERSION"} == {
        k: v for k, v in before.items() if k != "REALITY_VERSION"
    }
    assert "0.1.0 -> 0.2.0" in result.stdout


def test_upgrade_to_the_installed_version_is_a_no_op(home: Path):
    run("--dry-run", "--version", "0.1.0", cwd=home)

    result = run(
        "upgrade",
        "--dry-run",
        "--version",
        "0.1.0",
        "--dir",
        str(home / "reality"),
        cwd=home,
    )

    assert result.returncode == 0
    assert "already installed" in result.stdout


def test_upgrade_refuses_a_directory_without_a_version_marker(home: Path):
    foreign = home / "reality"
    foreign.mkdir()
    (foreign / ".env").write_text("POSTGRES_DB=reality\n")

    result = run("upgrade", "--dry-run", "--dir", str(foreign), cwd=home)

    assert result.returncode == 1
    assert "not created by the installer" in result.stderr


def test_restore_needs_an_archive_and_an_empty_directory(home: Path):
    result = run("restore", cwd=home)
    assert result.returncode == 2
    assert "restore needs an archive path" in result.stderr

    missing = run("restore", str(home / "nope.tar"), cwd=home)
    assert missing.returncode == 1
    assert "archive not found" in missing.stderr


def test_shipped_assets_match_the_script_list():
    script = SCRIPT.read_text()
    listed = script.split('ASSETS="', 1)[1].split('"', 1)[0].split()
    assert listed == SHIPPED_ASSETS
    for name in SHIPPED_ASSETS:
        assert (INSTALLER_DIR / name).is_file(), name


def test_env_example_covers_every_generated_variable(home: Path):
    run("--dry-run", "--version", "0.1.0", cwd=home)
    generated = set(read_env(home / "reality"))
    example = {
        line.partition("=")[0]
        for line in (INSTALLER_DIR / ".env.example").read_text().splitlines()
        if line and not line.startswith("#")
    }
    assert generated == example


@pytest.mark.parametrize("web_becomes_ready", [True, False])
def test_success_waits_for_web_proxy_health(home: Path, web_becomes_ready: bool):
    """FR-013: a healthy API alone must not announce a usable App."""
    bin_dir = home / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        """#!/bin/sh
case "$1" in
  info) exit 0 ;;
  compose)
    case "$2" in ps) printf '%s\\n' "$4" ;; esac
    exit 0 ;;
  inspect)
    if [ "$4" = web ]; then
      if [ -f "$TEST_WEB_CHECKED" ] && [ "$TEST_WEB_READY" = yes ]; then
        echo healthy
      else
        touch "$TEST_WEB_CHECKED"
        echo starting
      fi
    else
      echo healthy
    fi
    exit 0 ;;
esac
exit 99
"""
    )
    docker.chmod(0o755)
    sleep = bin_dir / "sleep"
    sleep.write_text("#!/bin/sh\nexit 0\n")
    sleep.chmod(0o755)
    checked = home / "web-checked"
    result = run(
        "--version",
        "0.1.0",
        cwd=home,
        env={
            "REALITY_DOCKER_BIN": str(docker),
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "TEST_WEB_CHECKED": str(checked),
            "TEST_WEB_READY": "yes" if web_becomes_ready else "no",
        },
    )
    assert checked.exists(), "Installer did not check the web proxy"
    if web_becomes_ready:
        assert result.returncode == 0
        assert "Reality is running." in result.stdout
    else:
        assert result.returncode != 0
        assert "Reality is running." not in result.stdout
        assert "did not become healthy" in result.stderr
