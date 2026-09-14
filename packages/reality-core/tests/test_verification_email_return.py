import re
from urllib.parse import parse_qs, urlsplit

from reality.web import email as email_module


def test_verification_email_returns_to_app_without_putting_code_in_url(monkeypatch):
    sent = []
    monkeypatch.setenv("APP_URL", "https://app.example.com/")
    monkeypatch.setattr(
        email_module, "send_email", lambda **message: sent.append(message)
    )
    email_module.send_verification_email("owner+trial@example.com", "123456")
    message = sent[0]
    link = re.search(r'href="([^"]+)"', message["html_body"]).group(1)
    parsed = urlsplit(link)
    assert parsed.netloc == "app.example.com"
    assert parsed.path == "/verify-email"
    assert parse_qs(parsed.fragment)["email"] == ["owner+trial@example.com"]
    assert "123456" not in link
    assert not parsed.query
    assert link in message["text"]
    assert "123456" in message["html_body"]
