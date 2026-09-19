"""Exercise OS allocation in native child processes, without a database or fixed port."""

from __future__ import annotations

import errno
import json
import selectors
import socket
import subprocess
import urllib.request
from contextlib import ExitStack, contextmanager

import pytest

CONVENTIONAL_PORTS = (5432, 54329, 8000, 8001, 8080, 8081, 5173)


@contextmanager
def running_probe(binary, role, generation):
    process = subprocess.Popen(
        [str(binary), role, str(generation)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            assert selector.select(5), "Probe did not report its bound endpoint"
        line = process.stdout.readline()
        assert line, (
            process.stderr.read() if process.poll() is not None else "No endpoint"
        )
        endpoint = json.loads(line)
        yield process, endpoint
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        process.stdout.close()
        process.stderr.close()


def get_health(endpoint):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(endpoint["origin"] + "/healthz", timeout=2) as response:
        return json.load(response)


def test_three_roles_start_with_conventional_ports_occupied(probe_binary):
    with ExitStack() as stack:
        sentinels = []
        for port in CONVENTIONAL_PORTS:
            listener = stack.enter_context(socket.socket())
            try:
                listener.bind(("127.0.0.1", port))
            except OSError as error:
                # A real pre-existing application already occupies this port. Never stop it.
                assert error.errno == errno.EADDRINUSE
                continue
            listener.listen()
            listener.settimeout(2)
            sentinels.append(listener)
        endpoints = []
        for role in ("api", "scheduler", "worker"):
            _, endpoint = stack.enter_context(running_probe(probe_binary, role, 7))
            assert endpoint["role"] == role
            assert endpoint["generation"] == 7
            assert endpoint["origin"].startswith("http://127.0.0.1:")
            assert int(endpoint["origin"].rsplit(":", 1)[1]) not in CONVENTIONAL_PORTS
            assert get_health(endpoint) == {"role": role, "generation": 7}
            endpoints.append(endpoint["origin"])
        assert len(set(endpoints)) == 3
        for listener in sentinels:
            with socket.create_connection(listener.getsockname(), timeout=2):
                accepted, _ = listener.accept()
                accepted.close()


def test_reported_port_stays_bound_and_serves_without_rebinding(probe_binary):
    with running_probe(probe_binary, "api", 1) as (_, endpoint):
        port = int(endpoint["origin"].rsplit(":", 1)[1])
        with socket.socket() as competitor:
            with pytest.raises(OSError) as failure:
                competitor.bind(("127.0.0.1", port))
            assert failure.value.errno == errno.EADDRINUSE
        assert get_health(endpoint)["generation"] == 1
        assert get_health(endpoint)["generation"] == 1


def test_separate_process_generations_coexist_and_restart(probe_binary):
    with (
        running_probe(probe_binary, "api", 1) as (_, first),
        running_probe(probe_binary, "api", 2) as (_, second),
    ):
        assert first["origin"] != second["origin"]
        assert get_health(first)["generation"] == 1
        assert get_health(second)["generation"] == 2
    with running_probe(probe_binary, "api", 3) as (_, restarted):
        assert get_health(restarted)["generation"] == 3


def test_untrusted_role_is_rejected_before_listening(probe_binary):
    result = subprocess.run(
        check=False,
        args=[str(probe_binary), 'api"injected', "1"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode != 0
    assert not result.stdout
