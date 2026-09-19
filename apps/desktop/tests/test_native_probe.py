"""The native cookie proof must never expose its bearer secret to page scripts."""

from __future__ import annotations

import http.client
import importlib.util
import json
import threading
from pathlib import Path

import pytest


@pytest.fixture
def probe():
    path = Path(__file__).resolve().parents[1] / "scripts/native-probe.py"
    spec = importlib.util.spec_from_file_location("native_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    server = module.ProbeServer(Path("/unused/runtime"), Path("/unused/scripts"))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def request(
    probe, path="/", *, token=True, host=None, origin=None, method="GET", body=None
):
    connection = http.client.HTTPConnection("127.0.0.1", probe.server_port, timeout=3)
    headers = {}
    if token:
        headers["Cookie"] = f"reality_native_probe={probe.token}"
    if host:
        headers["Host"] = host
    if origin:
        headers["Origin"] = origin
    if body is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(body)
    try:
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        return response.status, response.read(), dict(response.getheaders())
    finally:
        connection.close()


def test_no_localhost_authentication_bypass(probe):
    assert request(probe, token=False)[0] == 401
    assert request(probe, host="evil.example")[0] == 403
    assert request(probe, origin="https://evil.example")[0] == 403


def test_valid_cookie_opens_page_without_disclosing_it(probe):
    status, body, headers = request(probe)
    assert status == 200
    assert probe.token.encode() not in body
    assert headers["Cache-Control"] == "no-store"
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert "Set-Cookie" not in headers


def test_proof_requires_same_origin_and_typed_payload(probe):
    payload = {"cookie_hidden": True, "native_command_denied": True}
    assert request(probe, "/proof", method="POST", body=payload)[0] == 403
    assert (
        request(
            probe,
            "/proof",
            method="POST",
            origin=probe.origin,
            body={"cookie_hidden": "true"},
        )[0]
        == 400
    )
    assert (
        request(probe, "/proof", method="POST", origin=probe.origin, body=payload)[0]
        == 200
    )
    assert probe.status()["cookie_hidden"] is True
    assert probe.status()["native_command_denied"] is True


def test_new_instance_has_a_different_cookie_secret(probe):
    assert len(probe.token) >= 40
    assert request(probe, "/status")[0] == 200
    assert probe.token.encode() not in request(probe, "/status")[1]
