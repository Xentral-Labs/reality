"""SQL search support uses the same semantics and preserves existing data."""

import json
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from reality.db.search_sql import install_search_support

CASES = json.loads(
    (Path(__file__).parent / "fixtures/global_search_matching.json").read_text()
)


@pytest.mark.parametrize("case", CASES, ids=lambda row: row["query"])
def test_sql_matches_corpus(session, case):
    install_search_support(session.connection())
    result = session.scalar(
        text("select reality_search_tier_v1(:q, :names, :refs)"),
        {"q": case["query"], "names": [case["label"]], "refs": case["references"]},
    )
    assert result == case["tier"]


def test_upgrade_downgrade_preserves_rows(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option(
        "script_location", str(Path(__file__).parents[1] / "migrations")
    )
    command.upgrade(config, "0065_requested_analysis")
    engine = create_engine(postgres_database)
    with engine.begin() as conn:
        conn.execute(
            text(
                "insert into tenant (id,name,created_at,purpose) values ('search_migration','Unchanged',now(),'business')"
            )
        )
    for revision in ["head", "0065_requested_analysis", "head"]:
        command.upgrade(config, revision) if revision == "head" else command.downgrade(
            config, revision
        )
        with engine.connect() as conn:
            assert (
                conn.scalar(text("select name from tenant where id='search_migration'"))
                == "Unchanged"
            )
            exists = conn.scalar(
                text(
                    "select to_regprocedure('reality_search_tier_v1(text,text[],text[])') is not null"
                )
            )
            assert exists == (revision == "head")
    engine.dispose()
