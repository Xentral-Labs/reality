from __future__ import annotations

import pytest
from cryptography.fernet import Fernet


def test_desktop_key_is_installed_once_and_never_replaced(monkeypatch):
    from reality.security import key_provider

    first = Fernet.generate_key().decode()
    second = Fernet.generate_key().decode()
    monkeypatch.setattr(key_provider, "_process_key", None)

    key_provider.install_process_key(first, installation_id="installation-a")

    assert key_provider.master_key() == first.encode()
    with pytest.raises(RuntimeError, match="already initialized"):
        key_provider.install_process_key(second, installation_id="installation-a")
    assert key_provider.master_key() == first.encode()


def test_desktop_key_rejects_empty_invalid_and_mismatched_installation(monkeypatch):
    from reality.security import key_provider

    monkeypatch.setattr(key_provider, "_process_key", None)
    with pytest.raises(RuntimeError, match="required"):
        key_provider.install_process_key("", installation_id="installation-a")
    with pytest.raises(RuntimeError, match="valid Fernet"):
        key_provider.install_process_key("not-a-key", installation_id="installation-a")

    key_provider.install_process_key(
        Fernet.generate_key().decode(), installation_id="installation-a"
    )
    with pytest.raises(RuntimeError, match="different installation"):
        key_provider.master_key(installation_id="installation-b")


def test_desktop_mode_fails_closed_without_process_key(monkeypatch):
    from reality.security import key_provider

    monkeypatch.setattr(key_provider, "_process_key", None)
    monkeypatch.setenv("REALITY_DESKTOP", "1")
    monkeypatch.setenv("REALITY_MASTER_KEY", Fernet.generate_key().decode())

    with pytest.raises(RuntimeError, match="private runtime handoff"):
        key_provider.master_key(installation_id="installation-a")


def test_hosted_configuration_keeps_existing_environment_contract(monkeypatch):
    from reality.security import key_provider

    configured = Fernet.generate_key()
    monkeypatch.setattr(key_provider, "_process_key", None)
    monkeypatch.delenv("REALITY_DESKTOP", raising=False)
    monkeypatch.setenv("REALITY_MASTER_KEY", configured.decode())

    assert key_provider.master_key() == configured
