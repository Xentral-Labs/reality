import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError


@pytest.mark.parametrize(
    "previous_head",
    [
        "0039_learning_playground",
        "0040_commitment_revisions",
        "0043_practice_companies",
        "0043_return_announcements",
    ],
)
def test_playground_and_main_migration_heads_converge(
    postgres_database, monkeypatch, previous_head
):
    """Both deployed histories upgrade without restamping or dropping tenant data."""
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, previous_head)
    engine = create_engine(postgres_database)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO tenant (id, name, created_at) VALUES ('preserved', 'Existing', CURRENT_TIMESTAMP)"
                )
            )
            if previous_head == "0039_learning_playground":
                connection.execute(
                    text(
                        "INSERT INTO tenant (id, name, purpose, created_at) VALUES ('sandbox-preserved', 'Learning', 'playground', CURRENT_TIMESTAMP)"
                    )
                )
        command.upgrade(config, "head")
        assert {"playground_run", "playground_step", "commitment_revision"} <= set(
            inspect(engine).get_table_names()
        )
        assert "return_announcement" in inspect(engine).get_table_names()
        assert "supply_assignment" in inspect(engine).get_table_names()
        assert "sandbox_kind" in {
            column["name"] for column in inspect(engine).get_columns("playground_run")
        }
        # Convergence is the claim, so ask the script directory what the single head
        # is rather than naming it. Naming it made this test fail on the next
        # migration for a reason that had nothing to do with either history.
        heads = ScriptDirectory.from_config(config).get_heads()
        assert len(heads) == 1
        with engine.connect() as connection:
            assert (
                connection.scalar(text("SELECT name FROM tenant WHERE id='preserved'"))
                == "Existing"
            )
            assert (
                connection.scalar(text("SELECT version_num FROM alembic_version"))
                == heads[0]
            )
            if previous_head == "0039_learning_playground":
                assert (
                    connection.scalar(
                        text("SELECT purpose FROM tenant WHERE id='sandbox-preserved'")
                    )
                    == "playground"
                )
    finally:
        engine.dispose()


def test_playground_upgrade_preserves_business_and_scopes_steps(
    postgres_database: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0038_return_resolution")
    engine = create_engine(postgres_database)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO tenant (id, name, created_at) "
                    "VALUES ('existing', 'Playground demo', CURRENT_TIMESTAMP)"
                )
            )
        command.upgrade(config, "head")
        with engine.connect() as connection:
            assert (
                connection.scalar(
                    text("SELECT purpose FROM tenant WHERE id='existing'")
                )
                == "business"
            )
        inspector = inspect(engine)
        kind = next(
            column
            for column in inspector.get_columns("playground_run")
            if column["name"] == "sandbox_kind"
        )
        assert not kind["nullable"] and "temporary" in kind["default"]
        assert {"playground_run", "playground_step"} <= set(inspector.get_table_names())
        step_links = inspector.get_foreign_keys("playground_step")
        assert any(
            link["constrained_columns"] == ["tenant_id", "run_id"]
            for link in step_links
        )
        assert any(
            link["constrained_columns"] == ["tenant_id", "proposal_id"]
            for link in step_links
        )
        assert any(
            index["unique"] and index["name"] == "uq_playground_run_active_owner"
            for index in inspector.get_indexes("playground_run")
        )
        # Only a disposable, unused Playground schema may be downgraded.
        command.downgrade(config, "0038_return_resolution")
        assert "purpose" not in {
            column["name"] for column in inspect(engine).get_columns("tenant")
        }
        command.upgrade(config, "head")
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.execute(
                text("UPDATE tenant SET purpose='playground' WHERE id='existing'")
            )
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO tenant (id, name, purpose, created_at) "
                    "VALUES ('retained-sandbox', 'Learning', 'playground', CURRENT_TIMESTAMP)"
                )
            )
        with pytest.raises(RuntimeError, match="Cannot downgrade"):
            command.downgrade(config, "0038_return_resolution")
        with engine.connect() as connection:
            assert (
                connection.scalar(
                    text("SELECT purpose FROM tenant WHERE id='retained-sandbox'")
                )
                == "playground"
            )
        assert {"playground_run", "playground_step"} <= set(
            inspect(engine).get_table_names()
        )
    finally:
        engine.dispose()


def test_initial_migration_builds_complete_schema(
    postgres_database: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)

    command.upgrade(config, "head")

    inspector = inspect(create_engine(postgres_database))
    assert {
        "tenant",
        "source_record",
        "source_stream",
        "import_job",
        "document",
        "document_line",
        "commitment",
        "commitment_hold",
        "reservation",
        "handling_unit",
        "lot",
        "serial_unit",
        "movement",
        "movement_correction",
        "ledger_reversal",
        "ledger_entry",
        "settlement_allocation",
        "party_role",
        "party_hold",
        "action",
        "ai_settings",
        "projection_row",
        "projection_checkpoint",
        "alembic_version",
        "company_invitation",
        "invitation_delivery",
    } <= set(inspector.get_table_names())
    assert "terminal_at" in {
        column["name"] for column in inspector.get_columns("company_invitation")
    }
    assert {"tenant_id", "subject_type", "subject_id", "outcome"} <= {
        column["name"] for column in inspector.get_columns("security_audit_event")
    }
    membership_checks = {
        constraint["name"]
        for constraint in inspector.get_check_constraints("tenant_membership")
    }
    assert {
        "ck_tenant_membership_role",
        "ck_tenant_membership_status",
    } <= membership_checks
    assert {column["name"] for column in inspector.get_columns("ledger_entry")} >= {
        "posting_group_id",
        "account_id",
        "amount",
        "debit_credit",
    }
    assert {
        "payment_ledger_entry_id",
        "invoice_ledger_entry_id",
        "amount",
        "currency",
    } <= {column["name"] for column in inspector.get_columns("settlement_allocation")}
    for table in ("party", "item", "location"):
        assert "is_active" in {
            column["name"] for column in inspector.get_columns(table)
        }
    for table in ("party", "item"):
        assert "source_record_id" in {
            column["name"] for column in inspector.get_columns(table)
        }
    assert {"role", "party_id", "default_location_id"} <= {
        column["name"] for column in inspector.get_columns("party_role")
    }
    assert {"ordered_at", "requested_delivery_at", "ship_to_party_id"} <= {
        column["name"] for column in inspector.get_columns("document")
    }
    assert {"item_type", "tracking_type", "conversion_factor"} <= {
        column["name"] for column in inspector.get_columns("item")
    }
    assert {"cancelled_at", "priority", "due_at"} <= {
        column["name"] for column in inspector.get_columns("commitment")
    }
    assert {"payload_hash", "version", "source_version_at"} <= {
        column["name"] for column in inspector.get_columns("source_record")
    }
    assert "archived_at" in {
        column["name"] for column in inspector.get_columns("tenant")
    }
    assert "handling_unit_id" in {
        column["name"] for column in inspector.get_columns("movement")
    }
    for table in ("movement", "reservation"):
        assert {"lot_id", "serial_unit_id"} <= {
            column["name"] for column in inspector.get_columns(table)
        }
    assert "handling_unit_id" in {
        column["name"] for column in inspector.get_columns("reservation")
    }
    assert {
        "quantity",
        "unit",
        "unit_price",
        "gross_amount",
        "price_list_entry_id",
    } <= {column["name"] for column in inspector.get_columns("document_line")}


def test_source_idempotency_migration_backfills_versions_and_stream(
    postgres_database: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0009_payment_terms")
    engine = create_engine(postgres_database)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO tenant (id, name, created_at) "
                "VALUES ('ten_test', 'Test', '2026-01-01 00:00:00')"
            )
        )
        for source_id, payload in (("src_one", '{"v":1}'), ("src_two", '{"v":2}')):
            connection.execute(
                text(
                    "INSERT INTO source_record "
                    "(id, tenant_id, source_system, source_type, external_id, payload, "
                    "received_at) VALUES (:id, 'ten_test', 'shopify', 'order', '42', "
                    ":payload, :received_at)"
                ),
                {
                    "id": source_id,
                    "payload": payload,
                    "received_at": "2026-01-01 00:00:00"
                    if source_id == "src_one"
                    else "2026-01-02 00:00:00",
                },
            )

    command.upgrade(config, "head")

    with engine.connect() as connection:
        versions = connection.execute(
            text("SELECT id, version FROM source_record ORDER BY version")
        ).all()
        current = connection.execute(
            text("SELECT current_source_record_id FROM source_stream")
        ).scalar_one()
    assert versions == [("src_one", 1), ("src_two", 2)]
    assert current == "src_two"


def test_membership_invitation_migration_preserves_membership_and_guards_downgrade(
    postgres_database: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0029_ledger_reversals")
    engine = create_engine(postgres_database)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO tenant (id, name, created_at) VALUES "
                "('ten_invite', 'Invite Co', CURRENT_TIMESTAMP)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO app_user "
                "(id, email, password_hash, display_name, status, locale, timezone, "
                "is_platform_admin, created_at, updated_at) VALUES "
                "('usr_owner', 'owner@example.com', 'test', '', 'active', 'en-GB', "
                "'UTC', false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO tenant_membership "
                "(id, tenant_id, user_id, role, status, created_at) VALUES "
                "('tmb_owner', 'ten_invite', 'usr_owner', 'owner', 'active', "
                "CURRENT_TIMESTAMP)"
            )
        )

    command.upgrade(config, "head")

    with engine.begin() as connection:
        assert (
            connection.scalar(
                text("SELECT id FROM tenant_membership WHERE id = 'tmb_owner'")
            )
            == "tmb_owner"
        )
        connection.execute(
            text(
                "INSERT INTO company_invitation "
                "(id, tenant_id, normalized_email, status, token_generation, expires_at, "
                "invited_by_user_id, terminal_at, created_at, updated_at) VALUES "
                "('inv_guard', 'ten_invite', 'member@example.com', 'expired', 1, "
                "CURRENT_TIMESTAMP, 'usr_owner', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, "
                "CURRENT_TIMESTAMP)"
            )
        )

    with pytest.raises(RuntimeError, match="Cannot remove company membership"):
        command.downgrade(config, "0029_ledger_reversals")


def test_fact_observation_identity_migration_upgrades_and_downgrades(
    postgres_database: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    inspector = inspect(engine)

    assert "request_fingerprint" in {
        column["name"] for column in inspector.get_columns("fact")
    }
    assert "uq_fact_tenant_request_fingerprint" in {
        constraint["name"] for constraint in inspector.get_unique_constraints("fact")
    }

    command.downgrade(config, "0031_chat_session_archiving")
    inspector = inspect(engine)
    assert "request_fingerprint" not in {
        column["name"] for column in inspector.get_columns("fact")
    }


def test_interpretation_outcome_migration_upgrades_and_downgrades(
    postgres_database: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    tables = {"interpretation_outcome", "interpretation_record_reference"}
    assert tables <= set(inspect(engine).get_table_names())
    command.downgrade(config, "0032_fact_observation_identity")
    assert not tables & set(inspect(engine).get_table_names())


def test_decision_attribution_migration_upgrades_and_downgrades(
    postgres_database: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    attribution = {"decided_at", "decided_by_user_id"}

    assert attribution <= {
        column["name"] for column in inspect(engine).get_columns("action")
    }

    command.downgrade(config, "0033_interpretation_outcomes")
    assert not attribution & {
        column["name"] for column in inspect(engine).get_columns("action")
    }


def test_reality_gap_migration_upgrades_and_downgrades(
    postgres_database: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    tables = {
        "reality_gap",
        "reality_gap_entry",
        "interpretation_rule",
        "rule_interpretation_outcome",
    }
    assert tables <= set(inspect(engine).get_table_names())
    assert "interpretation_rule_id" in {
        column["name"] for column in inspect(engine).get_columns("fact")
    }
    conditional_rule_columns = {
        "conditions_mode",
        "conditions",
        "iteration_path",
        "source_line_id_path",
        "output_mode",
        "output_path",
        "output_scope",
        "constant_value",
    }
    assert conditional_rule_columns <= {
        column["name"] for column in inspect(engine).get_columns("interpretation_rule")
    }
    assert "element_key" in {
        column["name"]
        for column in inspect(engine).get_columns("rule_interpretation_outcome")
    }

    command.downgrade(config, "0035_reality_gaps")
    assert not conditional_rule_columns & {
        column["name"] for column in inspect(engine).get_columns("interpretation_rule")
    }
    assert "element_key" not in {
        column["name"]
        for column in inspect(engine).get_columns("rule_interpretation_outcome")
    }

    command.downgrade(config, "0034_decision_attribution")
    assert not tables & set(inspect(engine).get_table_names())
    assert "interpretation_rule_id" not in {
        column["name"] for column in inspect(engine).get_columns("fact")
    }


def test_erp_rule_migration_accepts_historical_unnamed_outcome_constraint(
    postgres_database: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0035_reality_gaps")
    engine = create_engine(postgres_database)
    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE rule_interpretation_outcome "
                "RENAME CONSTRAINT uq_rule_outcome_source TO "
                "rule_interpretation_outcome_tenant_id_rule_id_source_record_key"
            )
        )

    command.upgrade(config, "head")

    constraints = inspect(engine).get_unique_constraints("rule_interpretation_outcome")
    assert any(
        constraint["name"] == "uq_rule_outcome_source_element"
        and set(constraint["column_names"])
        == {"tenant_id", "rule_id", "source_record_id", "element_key"}
        for constraint in constraints
    )


def test_storyline_migration_backfills_fact_recording_order_and_guards_downgrade(
    postgres_database: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spec 182: recorded_at is backfilled from observed_at; downgrade keeps history."""
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0057_projection_jobs")
    engine = create_engine(postgres_database)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO tenant (id, name, created_at) "
                    "VALUES ('story', 'Story', CURRENT_TIMESTAMP)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO fact (id, tenant_id, subject_type, subject_id, predicate, "
                    "value, observed_at) VALUES ('fct_backfilled', 'story', 'commitment', "
                    "'com_x', 'order.delivery_instruction', 'gate', "
                    "TIMESTAMPTZ '2026-08-01 10:00:00+00')"
                )
            )
        command.upgrade(config, "head")
        inspector = inspect(engine)
        assert {"storyline_trace_entry", "storyline_package"} <= set(
            inspector.get_table_names()
        )
        assert "recorded_at" in {c["name"] for c in inspector.get_columns("fact")}
        assert {"storyline_key", "storyline_version", "storyline_state"} <= {
            c["name"] for c in inspector.get_columns("playground_run")
        }
        step_columns = {c["name"]: c for c in inspector.get_columns("playground_step")}
        assert {"marker_sequence", "marker_at"} <= set(step_columns)
        assert step_columns["proposal_id"]["nullable"] is True
        with engine.connect() as connection:
            assert connection.scalar(
                text(
                    "SELECT recorded_at = observed_at FROM fact WHERE id='fct_backfilled'"
                )
            )
        # A clean downgrade restores 0057; a storyline run blocks it.
        command.downgrade(config, "0057_projection_jobs")
        assert "storyline_trace_entry" not in set(inspect(engine).get_table_names())
        command.upgrade(config, "head")
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO app_user (id, email, password_hash, display_name, status, "
                    "language, locale, timezone, is_platform_admin, created_at, updated_at) "
                    "VALUES ('usr_story', 'story@example.test', 'x', 'Story', 'active', "
                    "'en', 'en-GB', 'UTC', false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO playground_run (id, tenant_id, owner_user_id, preset_key, "
                    "sandbox_kind, preset_version, lesson_key, lesson_version, "
                    "client_request_key, status, storyline_key, storyline_version, created_at) "
                    "VALUES ('run_story', 'story', 'usr_story', 'storyline', 'practice', 1, "
                    "'storyline', 1, 'req-1', 'initializing', 'order-to-close', 1, "
                    "CURRENT_TIMESTAMP)"
                )
            )
        with pytest.raises(RuntimeError, match="Storyline runs exist"):
            command.downgrade(config, "0057_projection_jobs")
    finally:
        engine.dispose()
