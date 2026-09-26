"""Private-pipe adapter for the shared scheduler and worker process loops."""

import json
import logging
import os
import sys
import threading


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"scheduler", "worker"}:
        raise SystemExit(2)
    config = json.loads(sys.stdin.readline(16384))
    os.environ.update(
        REALITY_DATABASE_URL=config["database_url"],
        REALITY_ROOT=config["core_root"],
        REALITY_ARTIFACT_DIR=config["artifact_root"],
        REALITY_AUTH_MODE="enabled",
        REALITY_DESKTOP="1",
    )
    from reality.security.key_provider import install_process_key

    install_process_key(
        config["vault_master_key"], installation_id=config["installation_id"]
    )
    from reality.jobs.runtime import ProcessLoop

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    loop = ProcessLoop(
        sys.argv[1],
        session_info={
            "desktop_installation_id": config["installation_id"],
            "desktop_owner_id": config["owner_id"],
        },
    )

    def parent_closed():
        sys.stdin.read()
        loop.stop.set()

    threading.Thread(target=parent_closed, daemon=True).start()
    _summary, status = loop.run(continuous=True, poll_seconds=1)
    raise SystemExit(status)


if __name__ == "__main__":
    main()
