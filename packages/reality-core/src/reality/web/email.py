from __future__ import annotations

import html
import logging
import os
import smtplib
from email.message import EmailMessage
from urllib.parse import urlencode

import httpx

log = logging.getLogger(__name__)

_PRIVACY_URL = "https://xentral.com/de/legal/datenschutz"
_SUPPORT_EMAIL = "support@xentral.com"
_LEGAL_TEXT = """Xentral ERP Software GmbH
Viktoriastraße 3b, 2. OG
D-86150 Augsburg
www.xentral.com

Sitz der Gesellschaft: Augsburg
Handelsregister: Augsburg, HRB 23930
Geschäftsführung: Benedikt Sauter, Domenico Cipolla
USt-IdNr.: DE263136143

Unsere datenschutzrechtlichen Hinweise bezüglich der Verarbeitung Ihrer personenbezogenen Daten:
https://xentral.com/de/legal/datenschutz"""


def _with_legal_footer(text: str, html_body: str) -> tuple[str, str]:
    text_with_footer = f"{text.rstrip()}\n\n---\n\n{_LEGAL_TEXT}\n"
    html_with_footer = f"""{html_body.rstrip()}
    <div style="font-family:Inter,Arial,sans-serif;color:#667085;max-width:560px;margin:0 auto;padding:24px;border-top:1px solid #e4e7ec;font-size:12px;line-height:1.6">
      <strong style="color:#344054">Xentral ERP Software GmbH</strong><br>
      Viktoriastraße 3b, 2. OG · D-86150 Augsburg<br>
      <a href="https://www.xentral.com" style="color:#475467">www.xentral.com</a><br><br>
      Sitz der Gesellschaft: Augsburg · Handelsregister: Augsburg, HRB 23930<br>
      Geschäftsführung: Benedikt Sauter, Domenico Cipolla<br>
      USt-IdNr.: DE263136143<br><br>
      Unsere datenschutzrechtlichen Hinweise bezüglich der Verarbeitung Ihrer personenbezogenen Daten finden Sie
      <a href="{_PRIVACY_URL}" style="color:#475467">hier</a>.
    </div>"""
    return text_with_footer, html_with_footer


def _provider() -> str:
    configured = os.environ.get("REALITY_EMAIL_PROVIDER", "").strip().lower()
    if configured:
        return configured
    if os.environ.get("RESEND_API_KEY", "").strip():
        return "resend"
    if os.environ.get("REALITY_SMTP_HOST", "").strip():
        return "smtp"
    return "log"


def _dispatch_email(*, recipient: str, subject: str, text: str, html_body: str) -> None:
    provider = _provider()
    sender = os.environ.get("REALITY_EMAIL_FROM", "Reality <onboarding@resend.dev>")
    text, html_body = _with_legal_footer(text, html_body)
    if provider == "log":
        log.info("Email disabled; delivery suppressed for recipient %s.", recipient)
        return
    if provider == "resend":
        api_key = os.environ.get("RESEND_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "RESEND_API_KEY is required when REALITY_EMAIL_PROVIDER=resend"
            )
        response = httpx.post(
            os.environ.get("REALITY_RESEND_API_URL", "https://api.resend.com/emails"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": sender,
                "to": [recipient],
                "subject": subject,
                "text": text,
                "html": html_body,
            },
            timeout=10,
        )
        response.raise_for_status()
        return
    if provider == "smtp":
        host = os.environ.get("REALITY_SMTP_HOST", "").strip()
        if not host:
            raise RuntimeError(
                "REALITY_SMTP_HOST is required when REALITY_EMAIL_PROVIDER=smtp"
            )
        message = EmailMessage()
        message["Subject"], message["From"], message["To"] = subject, sender, recipient
        message.set_content(text)
        message.add_alternative(html_body, subtype="html")
        port = int(os.environ.get("REALITY_SMTP_PORT", "587"))
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            if os.environ.get("REALITY_SMTP_TLS", "true").lower() == "true":
                smtp.starttls()
            username = os.environ.get("REALITY_SMTP_USERNAME", "")
            if username:
                smtp.login(username, os.environ.get("REALITY_SMTP_PASSWORD", ""))
            smtp.send_message(message)
        return
    raise RuntimeError(f"Unsupported REALITY_EMAIL_PROVIDER: {provider}")


def send_email(
    *, recipient: str, subject: str, text: str, html_body: str, kind: str = "unknown"
) -> None:
    """Dispatch an email and record the outcome.

    `kind` is a bounded enumeration supplied by the caller (verification,
    invitation, access_decision) -- never the recipient, which would put an
    email address into a metric label and both explode cardinality and store
    personal data in Prometheus.

    "suppressed" is reported distinctly from "sent": with REALITY_EMAIL_PROVIDER
    unset or `log`, delivery silently does nothing, and a dashboard that counted
    that as success would look healthy while no mail left the building.
    """
    provider = _provider()
    from reality.telemetry.metrics import email_sent

    try:
        _dispatch_email(
            recipient=recipient, subject=subject, text=text, html_body=html_body
        )
    except Exception:
        email_sent(provider, "error", kind)
        raise
    email_sent(provider, "suppressed" if provider == "log" else "sent", kind)


def send_verification_email(email: str, code: str) -> None:
    safe_code = html.escape(code)
    app_url = (os.environ.get("APP_URL") or "http://localhost:8080").rstrip("/")
    return_url = f"{app_url}/verify-email#{urlencode({'email': email})}"
    safe_url = html.escape(return_url, quote=True)
    send_email(
        recipient=email,
        subject=f"{code} is your Reality verification code",
        text=(
            f"Confirm your email\n\n{code}\n\nThis code expires in 10 minutes. Never share it."
            f"\n\nClosed the tab? Open Reality and enter your code: {return_url}"
        ),
        html_body=f"""
        <div style="font-family:Inter,Arial,sans-serif;color:#111827;max-width:560px;margin:auto;padding:40px 24px">
          <div style="font-size:22px;font-weight:700">Reality</div>
          <h1 style="font-size:28px;margin:40px 0 12px">Confirm your email</h1>
          <p style="color:#667085">Enter this verification code in Reality:</p>
          <div style="font-size:40px;font-weight:700;letter-spacing:8px;margin:28px 0">{safe_code}</div>
          <p style="color:#667085">This code expires in 10 minutes. Never share it.</p>
          <a href="{safe_url}" style="display:inline-block;margin:16px 0;padding:13px 20px;border-radius:10px;background:#635bff;color:white;text-decoration:none;font-weight:600">Enter verification code</a>
          <p style="color:#667085;font-size:14px">Closed the tab? This button reopens Reality. Enter the code above to confirm your email. If it has expired, request a new code there.</p>
        </div>""",
            kind="verification",
    )


def send_access_decision_email(email: str, approved: bool) -> None:
    app_url = (
        f"{(os.environ.get('APP_URL') or 'http://localhost:8080').rstrip('/')}/app"
    )
    safe_url = html.escape(app_url, quote=True)
    if approved:
        send_email(
            recipient=email,
            subject="Your Reality access is ready",
            text=f"Your Reality account has been approved.\n\nSign in: {app_url}",
            html_body=f"""
            <div style="font-family:Inter,Arial,sans-serif;color:#111827;max-width:560px;margin:auto;padding:40px 24px">
              <div style="font-size:22px;font-weight:700">Reality</div>
              <h1 style="font-size:28px;margin:40px 0 12px">You're in.</h1>
              <p style="color:#667085">Your Reality account has been approved.</p>
              <a href="{safe_url}" style="display:inline-block;margin-top:20px;padding:13px 20px;border-radius:10px;background:#635bff;color:white;text-decoration:none;font-weight:600">Open Reality</a>
            </div>""",
                kind="access_decision",
    )
    else:
        send_email(
            recipient=email,
            subject="Your Reality access request",
            text="We cannot activate your Reality account at this time.",
            html_body="""
            <div style="font-family:Inter,Arial,sans-serif;color:#111827;max-width:560px;margin:auto;padding:40px 24px">
              <div style="font-size:22px;font-weight:700">Reality</div>
              <h1 style="font-size:28px;margin:40px 0 12px">Your access request</h1>
              <p style="color:#667085">We cannot activate your Reality account at this time.</p>
            </div>""",
        )


def send_access_request_notification(email: str) -> None:
    recipient = os.environ.get("REALITY_ACCESS_NOTIFICATION_EMAIL", "").strip()
    if not recipient:
        return
    admin_url = f"{(os.environ.get('APP_URL') or 'http://localhost:8080').rstrip('/')}/admin/access"
    safe_email = html.escape(email)
    safe_url = html.escape(admin_url, quote=True)
    send_email(
        recipient=recipient,
        subject=f"Reality access request from {email}",
        text=(
            f"A verified user requested access to Reality.\n\n"
            f"User: {email}\n\nReview the request: {admin_url}"
        ),
        html_body=f"""
        <div style="font-family:Inter,Arial,sans-serif;color:#111827;max-width:560px;margin:auto;padding:40px 24px">
          <div style="font-size:22px;font-weight:700">Reality</div>
          <h1 style="font-size:28px;margin:40px 0 12px">New access request</h1>
          <p style="color:#667085">A verified user joined the Reality waitlist.</p>
          <div style="margin:24px 0;padding:16px;border-radius:10px;background:#f2f4f7">
            <strong>{safe_email}</strong>
          </div>
          <a href="{safe_url}" style="display:inline-block;padding:13px 20px;border-radius:10px;background:#635bff;color:white;text-decoration:none;font-weight:600">Review access request</a>
        </div>""",
    )


_INVITATION_COPY = {
    "en": ("Join {company} in Reality", "You have been invited to join {company}."),
    "de": ("{company} in Reality beitreten", "Du wurdest zu {company} eingeladen."),
    "nl": ("Word lid van {company} in Reality", "Je bent uitgenodigd voor {company}."),
    "es": ("Únete a {company} en Reality", "Te han invitado a {company}."),
}


def send_company_invitation_email(
    email: str,
    company_name: str,
    token: str,
    *,
    locale: str = "en",
) -> None:
    subject_template, intro_template = _INVITATION_COPY.get(
        locale, _INVITATION_COPY["en"]
    )
    product_url = (os.environ.get("APP_URL") or "http://localhost:8080").rstrip("/")
    invitation_url = f"{product_url}/invitation#token={token}"
    header_company = " ".join(company_name.splitlines())
    subject = subject_template.format(company=header_company)
    intro = intro_template.format(company=company_name)
    safe_company = html.escape(company_name)
    safe_url = html.escape(invitation_url, quote=True)
    send_email(
        recipient=email,
        subject=subject,
        text=(
            f"{intro}\n\nOpen invitation: {invitation_url}\n\n"
            f"If you did not expect this invitation, report it to {_SUPPORT_EMAIL}."
        ),
        html_body=f"""
        <div style="font-family:Inter,Arial,sans-serif;color:#111827;max-width:560px;margin:auto;padding:40px 24px">
          <div style="font-size:22px;font-weight:700">Reality</div>
          <h1 style="font-size:28px;margin:40px 0 12px">Join {safe_company}</h1>
          <p style="color:#667085">{html.escape(intro)}</p>
          <a href="{safe_url}" style="display:inline-block;margin-top:20px;padding:13px 20px;border-radius:10px;background:#635bff;color:white;text-decoration:none;font-weight:600">Open invitation</a>
          <p style="color:#667085;margin-top:28px">If you did not expect this invitation, report it to <a href="mailto:{_SUPPORT_EMAIL}" style="color:#475467">{_SUPPORT_EMAIL}</a>.</p>
        </div>""",
            kind="invitation",
    )
