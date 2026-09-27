"""Spec 290: proposal feedback storage is additive and reversible."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest
from alembic import command
from alembic.config import Config
from reality.db.core import AppUser, JourneyProposal, JourneyProposalVote, now
from reality.services.business_journeys import set_vote
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.orm import sessionmaker

CORE_ROOT = Path(__file__).parents[1]
ALEMBIC_INI = str(CORE_ROOT / "alembic.ini")


def _alembic_config(database_url: str) -> Config:
    config = Config(ALEMBIC_INI)
    config.set_main_option("script_location", str(CORE_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_business_journey_feedback_migration_round_trip(
    postgres_database: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = _alembic_config(postgres_database)
    command.upgrade(config, "0099_payment_term_prepayment")
    engine = create_engine(postgres_database)
    try:
        before = inspect(engine)
        assert "journey_proposal" not in before.get_table_names()
        assert "journey_proposal_vote" not in before.get_table_names()

        command.upgrade(config, "0100_business_journey_proposals")
        migrated = inspect(engine)
        assert {
            "creator_account_id",
            "reviewed_by_account_id",
            "reviewed_at",
            "available_journey_id",
        } <= {column["name"] for column in migrated.get_columns("journey_proposal")}
        assert any(
            constraint.get("name") == "uq_journey_proposal_vote_account"
            for constraint in migrated.get_unique_constraints("journey_proposal_vote")
        )

        command.downgrade(config, "0099_payment_term_prepayment")
        rolled_back = inspect(engine)
        assert "journey_proposal" not in rolled_back.get_table_names()
        assert "journey_proposal_vote" not in rolled_back.get_table_names()
    finally:
        engine.dispose()


def test_concurrent_vote_retries_keep_one_active_relationship(
    postgres_database: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = _alembic_config(postgres_database)
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    factory = sessionmaker(engine, expire_on_commit=False)
    try:
        with factory() as session:
            session.add(
                AppUser(
                    id="usr_vote_race",
                    email="vote-race@example.test",
                    password_hash="unused",
                    status="active",
                    email_verified_at=now(),
                )
            )
            session.add(
                JourneyProposal(
                    id="jpr_vote_race",
                    creator_account_id="usr_vote_race",
                    title="Concurrent vote",
                    business_question="Can concurrent votes remain one relationship?",
                    expected_outcome="One active vote remains.",
                    process_area="combined",
                    normalized_fingerprint="0" * 64,
                )
            )
            session.commit()

        barrier = Barrier(2)

        def vote() -> int:
            with factory() as session:
                barrier.wait()
                result = set_vote(
                    session, "usr_vote_race", "jpr_vote_race", active=True
                )
                return int(result["vote_count"])

        with ThreadPoolExecutor(max_workers=2) as pool:
            counts = list(pool.map(lambda _: vote(), range(2)))

        with factory() as session:
            rows = session.scalar(
                select(func.count()).select_from(JourneyProposalVote)
            )
            active = session.scalar(
                select(func.count())
                .select_from(JourneyProposalVote)
                .where(JourneyProposalVote.active.is_(True))
            )
        assert counts == [1, 1]
        assert rows == active == 1
    finally:
        engine.dispose()
