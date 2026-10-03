"""Spec 335: set-up companies get the carrier-claim account; rollback removes it."""

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def test_set_up_companies_get_the_claim_account_and_rollback_removes_it(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0122_purchasing_depth")
    engine = create_engine(postgres_database)
    try:
        with engine.begin() as connection:
            for tenant in ("set-up", "bare"):
                connection.execute(
                    text(
                        "INSERT INTO tenant (id,name,purpose,created_at) "
                        "VALUES (:t,:t,'business',now())"
                    ),
                    {"t": tenant},
                )
            # Only the first company set up its accounts.
            connection.execute(
                text(
                    "INSERT INTO subledger_account "
                    "(tenant_id,id,code,name,role,state,revision,default_destination_id) "
                    "VALUES ('set-up','reduction','reduction','Reduction',"
                    "'customer_reduction','active',1,'dest-reduction')"
                )
            )

        command.upgrade(config, "0125_delivery_failures")
        with engine.connect() as connection:
            claims = connection.execute(
                text(
                    "SELECT tenant_id, default_destination_id IS NOT NULL "
                    "FROM subledger_account WHERE role = 'carrier_claim_income'"
                )
            ).all()
        assert claims == [("set-up", True)]
        assert "delivery_failure" in inspect(engine).get_table_names()

        command.downgrade(config, "0122_purchasing_depth")
        with engine.connect() as connection:
            assert not connection.execute(
                text(
                    "SELECT count(*) FROM subledger_account "
                    "WHERE role = 'carrier_claim_income'"
                )
            ).scalar()
        assert "delivery_failure" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()
