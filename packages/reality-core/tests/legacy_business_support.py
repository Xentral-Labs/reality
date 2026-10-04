"""Represent retained historical business rows without inventing a new decision.

Only history/provenance and pinned migration fixtures use this builder. Current
business stories must use the real confirmed application tools instead. Reflected
inserts preserve the pinned schema; no runtime writer or authority is bypassed.
"""

from sqlalchemy import MetaData, Table

from reality.services import core


def historical_party(
    session,
    tenant_id,
    name,
    party_type,
    *,
    action_id=None,
    source_system="",
    external_id="",
    source_payload=None,
    roles=None,
    source_record_id=None,
    _commit=True,
):
    source = None
    if source_system:
        source, _, _ = core.store_source_record(
            session,
            tenant_id,
            source_system,
            "party",
            external_id,
            source_payload or {"name": name, "type": party_type, "emails": []},
        )
    metadata = MetaData()
    party = Table("party", metadata, autoload_with=session.connection())
    identity = core.uid("pty")
    values = {
        "id": identity,
        "tenant_id": tenant_id,
        "name": name,
        "type": party_type,
        "payload": "{}",
        "is_active": True,
        "source_record_id": source.id if source else source_record_id,
        "accounting_code": "",
        "default_currency": "EUR",
        "credit_limit": 0,
        "tax_identifier": "",
    }
    session.execute(
        party.insert().values(**{k: v for k, v in values.items() if k in party.c})
    )
    role_table = Table("party_role", metadata, autoload_with=session.connection())
    for role in roles or [party_type]:
        session.execute(
            role_table.insert().values(
                id=core.uid("pro"),
                tenant_id=tenant_id,
                party_id=identity,
                role=role,
            )
        )
    # This event represents the retained historical relationship, including an
    # absent creating decision. It does not grant permission to a runtime writer.
    core.emit_business_event(
        session,
        tenant_id,
        "party.created",
        "party",
        identity,
        {"name": name, "type": party_type, "roles": roles or [party_type]},
        source_record_id=values["source_record_id"],
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    from reality.db.core import Party

    return session.get(Party, (tenant_id, identity))
