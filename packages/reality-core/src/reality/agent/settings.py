from __future__ import annotations

import os

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session, object_session

from reality.db.core import ROOT, AISettings, now
from reality.security import secrets as secret_store
from reality.services.core import NotFound, get_tenant
from reality.services.tenant_policy import require_business_operation

KEY_PATH = ROOT / ".reality-secret.key"

AI_PROVIDER_PRESETS = (
    {"id": "managed", "name": "Reality-managed", "base_url": "", "models": ()},
    {
        "id": "anthropic",
        "name": "Anthropic",
        "base_url": "https://api.anthropic.com",
        "models": (("claude-haiku-4-5-20251001", "Claude Haiku 4.5 · economical"),),
    },
    {
        "id": "google",
        "name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "models": (("gemini-3.7-flash", "Gemini 3.7 Flash"),),
    },
    {
        "id": "openai",
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": (
            ("gpt-5.6-terra", "GPT-5.6 Terra · balanced"),
            ("gpt-5.6-luna", "GPT-5.6 Luna · fast and economical"),
            ("gpt-5.6-sol", "GPT-5.6 Sol · highest capability"),
        ),
    },
    {
        "id": "openrouter",
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "models": (("~openai/gpt-latest", "Latest OpenAI flagship via OpenRouter"),),
    },
    {
        "id": "groq",
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "models": (
            ("llama-3.3-70b-versatile", "Llama 3.3 70B Versatile"),
            ("openai/gpt-oss-120b", "GPT-OSS 120B"),
            ("openai/gpt-oss-20b", "GPT-OSS 20B"),
        ),
    },
    {
        "id": "mistral",
        "name": "Mistral AI",
        "base_url": "https://api.mistral.ai/v1",
        "models": (("mistral-large-latest", "Mistral Large (latest)"),),
    },
    {
        "id": "custom",
        "name": "Custom OpenAI-compatible endpoint",
        "base_url": "",
        "models": (),
    },
)


def ai_provider_preset(provider: str, base_url: str) -> str:
    if provider == "anthropic":
        return "anthropic"
    if provider == "local":
        return "managed"
    normalized = base_url.rstrip("/")
    return next(
        (
            preset["id"]
            for preset in AI_PROVIDER_PRESETS
            if preset["base_url"] and preset["base_url"] == normalized
        ),
        "custom",
    )


def _fernet() -> Fernet:
    configured = os.environ.get("REALITY_SETTINGS_KEY", "").encode()
    if configured:
        return Fernet(configured)
    if not KEY_PATH.exists():
        KEY_PATH.write_bytes(Fernet.generate_key())
        KEY_PATH.chmod(0o600)
    return Fernet(KEY_PATH.read_bytes().strip())


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode() if value else ""


def decrypt_secret(value: str) -> str:
    if not value:
        return ""
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as error:
        raise NotFound("The configured AI API key cannot be decrypted.") from error


def ai_settings(session: Session, tenant_id: str) -> AISettings:
    require_business_operation(session, tenant_id, "ai_settings")
    get_tenant(session, tenant_id)
    settings = session.get(AISettings, tenant_id)
    if settings is None:
        settings = AISettings(tenant_id=tenant_id)
        session.add(settings)
        session.commit()
    if settings.encrypted_api_key and not settings.api_key_secret_id:
        # One-time, lossless migration from the former AI-specific encrypted
        # column into the shared vault.
        secret_store.KEY_PATH = KEY_PATH
        record = secret_store.put_secret(
            session,
            tenant_id,
            purpose="llm_api_key",
            provider=ai_provider_preset(settings.provider, settings.base_url),
            label="Copilot API key",
            value=decrypt_secret(settings.encrypted_api_key),
        )
        settings.api_key_secret_id = record.id
        settings.encrypted_api_key = ""
        session.commit()
    return settings


def save_ai_settings(
    session: Session,
    tenant_id: str,
    *,
    provider: str,
    model: str,
    base_url: str,
    api_key: str = "",
    clear_api_key: bool = False,
) -> AISettings:
    require_business_operation(session, tenant_id, "ai_settings_update")
    if provider not in {"local", "openai_compatible", "anthropic"}:
        raise ValueError("Unsupported AI provider.")
    if provider in {"openai_compatible", "anthropic"} and not model.strip():
        raise ValueError("A model is required for an external AI provider.")
    settings = ai_settings(session, tenant_id)
    if (
        provider in {"openai_compatible", "anthropic"}
        and not api_key.strip()
        and (
            clear_api_key
            or settings.provider != provider
            or settings.base_url.rstrip("/") != base_url.strip().rstrip("/")
            or not settings.api_key_secret_id
        )
    ):
        raise ValueError("An API key is required for an external AI provider.")
    settings.provider = provider
    settings.model = model.strip()
    settings.base_url = base_url.strip().rstrip("/") or "https://api.openai.com/v1"
    if clear_api_key:
        if settings.api_key_secret_id:
            secret_store.revoke_secret(session, tenant_id, settings.api_key_secret_id)
        settings.api_key_secret_id = None
        settings.encrypted_api_key = ""
    elif api_key.strip():
        secret_store.KEY_PATH = KEY_PATH
        record = secret_store.replace_secret(
            session,
            tenant_id,
            settings.api_key_secret_id,
            purpose="llm_api_key",
            provider=ai_provider_preset(provider, settings.base_url),
            label="Copilot API key",
            value=api_key.strip(),
        )
        settings.api_key_secret_id = record.id
        settings.encrypted_api_key = ""
    settings.updated_at = now()
    session.commit()
    return settings


def configured_api_key(settings: AISettings) -> str:
    session = object_session(settings)
    if session is None:
        raise NotFound("The configured AI API key is detached from its session.")
    require_business_operation(session, settings.tenant_id, "ai_key_resolve")
    if settings.api_key_secret_id:
        secret_store.KEY_PATH = KEY_PATH
        clear_value = secret_store.resolve_secret(
            session, settings.tenant_id, settings.api_key_secret_id
        )
        return clear_value
    return decrypt_secret(settings.encrypted_api_key)


def has_configured_api_key(settings: AISettings) -> bool:
    if settings.encrypted_api_key:
        return True
    metadata = configured_api_key_metadata(settings)
    return metadata is not None and metadata.status == "active"


def configured_api_key_metadata(settings: AISettings):
    session = object_session(settings)
    if session is None or not settings.api_key_secret_id:
        return None
    return secret_store.secret_metadata(
        session, settings.tenant_id, settings.api_key_secret_id
    )


def copilot_api_key(session: Session, tenant_id: str) -> str:
    require_business_operation(session, tenant_id, "generic_copilot_context")
    settings = session.get(AISettings, tenant_id)
    if (
        settings is not None
        and settings.provider == "anthropic"
        and has_configured_api_key(settings)
    ):
        return configured_api_key(settings)
    return os.environ.get("ANTHROPIC_API_KEY", "").strip()
