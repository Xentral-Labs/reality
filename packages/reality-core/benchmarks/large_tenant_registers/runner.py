from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from reality.db.core import Tenant

from .cases import run_catalog
from .dataset import DatasetProfile, build_dataset, load_dataset, validate_dataset
from .derivations import run_derivations
from .report import BenchmarkResult, semantic_result, write_result


def validate_database_target(
    database_name: str, *, confirmed: bool, is_empty: bool, reuse: bool = False
) -> None:
    if not database_name.startswith("reality_benchmark_"):
        raise ValueError("Database name must begin with reality_benchmark_.")
    if not confirmed:
        raise ValueError("Pass --confirm-disposable to use the benchmark database.")
    if not is_empty and not reuse:
        raise ValueError("Benchmark database business tables must be empty.")


def _revision() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _content_digest() -> str:
    root = Path(__file__).parents[2]
    files = sorted(Path(__file__).parent.glob("*.py")) + [
        root / "src/reality/web/read_models.py",
        root / "src/reality/web/api.py",
    ]
    digest = hashlib.sha256()
    for path in files:
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the deterministic large-tenant register benchmark."
    )
    parser.add_argument("--profile", choices=("reduced", "full"), default="full")
    parser.add_argument(
        "--orders",
        type=int,
        default=None,
        help="Override the full profile's order count for a scale run.",
    )
    parser.add_argument(
        "--financial",
        type=int,
        default=None,
        help="Override the full profile's finance-document count; defaults to --orders.",
    )
    parser.add_argument("--seed", type=int, default=32010)
    parser.add_argument(
        "--business-date", type=date.fromisoformat, default=date(2026, 9, 1)
    )
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument("--confirm-disposable", action="store_true")
    parser.add_argument(
        "--reuse",
        action="store_true",
        help="Reuse one completed matching dataset without rebuilding it.",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    database_url = os.environ.get("REALITY_DATABASE_URL", "")
    if not database_url:
        raise ValueError("REALITY_DATABASE_URL is required.")
    engine = create_engine(database_url)
    tables = set(inspect(engine).get_table_names())
    if "tenant" not in tables:
        raise ValueError("Current Reality schema must be applied before the benchmark.")
    with Session(engine) as session:
        tenant_count = int(
            session.scalar(select(func.count()).select_from(Tenant)) or 0
        )
        validate_database_target(
            make_url(database_url).database or "",
            confirmed=args.confirm_disposable,
            is_empty=tenant_count == 0,
            reuse=args.reuse,
        )
        if args.profile == "full":
            profile = DatasetProfile.full(
                seed=args.seed,
                business_date=args.business_date,
                **({"order_count": args.orders} if args.orders else {}),
                **({"financial_count": args.financial} if args.financial else {}),
            )
        else:
            if args.orders or args.financial:
                raise ValueError("Size overrides apply to the full profile only.")
            profile = DatasetProfile.reduced(
                seed=args.seed, business_date=args.business_date
            )
        dataset = (
            load_dataset(session, profile)
            if args.reuse
            else build_dataset(session, profile)
        )
        validate_dataset(session, dataset)
        runs = [run_catalog(session, dataset) for _ in range(args.repeat)]
        derivations = run_derivations(session, dataset)
        if any(semantic_result(run) != semantic_result(runs[0]) for run in runs[1:]):
            raise AssertionError("Repeated benchmark runs produced semantic drift.")
        schema_revision = (
            session.scalar(text("SELECT version_num FROM alembic_version LIMIT 1"))
            if "alembic_version" in tables
            else "metadata-current"
        )
        postgresql = str(session.scalar(text("SHOW server_version")))
        result = BenchmarkResult.from_run(
            dataset,
            runs[0],
            derivations=derivations,
            git_revision=_revision(),
            schema_revision=str(schema_revision),
            postgresql=postgresql,
            working_tree_digest=_content_digest(),
        )
        write_result(result, args.output)
    engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
