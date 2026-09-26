"""Run the current core migrations for a staged local database over a private pipe."""

import json
import os
import sys


def main() -> None:
    config = json.loads(sys.stdin.readline(16384))
    if set(config) != {"database_url", "core_root"}:
        raise RuntimeError("Invalid migration configuration.")
    os.environ.update(
        REALITY_DATABASE_URL=config["database_url"],
        REALITY_ROOT=config["core_root"],
        REALITY_DESKTOP="1",
    )
    from reality.db.core import init_db

    init_db()


if __name__ == "__main__":
    main()
