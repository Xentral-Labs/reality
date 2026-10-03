"""Spec 339: the merge table comes and goes, and rollback keeps stated merges."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def test_rollback_is_refused_while_a_merge_is_stated(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0131_party_merges")
    engine = create_engine(postgres_database)
    try:
        assert "party_merge" in inspect(engine).get_table_names()
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO tenant (id,name,purpose,created_at) "
                    "VALUES ('t','t','business',now())"
                )
            )
            for party in ("dup", "sur"):
                connection.execute(
                    text(
                        "INSERT INTO party (tenant_id,id,type,name,payload,is_active,"
                        "accounting_code,default_currency,credit_limit,tax_identifier) "
                        "VALUES ('t',:p,'customer',:p,'{}',true,'','EUR',0,'')"
                    ),
                    {"p": party},
                )
            connection.execute(
                text(
                    "INSERT INTO source_record (tenant_id,id,source_system,source_type,"
                    "external_id,version,payload,payload_hash,received_at) VALUES "
                    "('t','src','internal_party_merge','party_merge','dup',1,'{}','h',now())"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO party_merge (tenant_id,id,duplicate_party_id,"
                    "surviving_party_id,reason,created_at,source_record_id) "
                    "VALUES ('t','m','dup','sur','same',now(),'src')"
                )
            )

        with pytest.raises(RuntimeError, match="party merges are stated"):
            command.downgrade(config, "0128_outbound_deliveries")

        with engine.begin() as connection:
            connection.execute(text("DELETE FROM party_merge"))
        command.downgrade(config, "0128_outbound_deliveries")
        assert "party_merge" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()
