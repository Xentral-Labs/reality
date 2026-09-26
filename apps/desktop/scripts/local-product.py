"""Private-pipe-only entrypoint for disposable interactive desktop development."""

import json
import os
import socket
import sys
import threading
from pathlib import Path


def main():
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
    from reality.db.core import AppUser, Session, init_db

    if sys.argv[1:] == ["--prepare"]:
        init_db()
        from reality.services.desktop_identity import bootstrap_owner

        Session.configure(info={"desktop_installation_id": config["installation_id"]})
        with Session() as session:
            owner = bootstrap_owner(session, config["installation_id"])
            owner_id = owner.id
            session.commit()
        print(json.dumps({"owner_id": owner_id}), flush=True)
        return
    from reality.services.account_sessions import issue_session, revoke_session

    owner_id = config["owner_id"]
    Session.configure(
        info={
            "desktop_installation_id": config["installation_id"],
            "desktop_owner_id": owner_id,
        }
    )
    with Session() as session:
        owner = session.get(AppUser, owner_id)
        token = issue_session(session, owner)
        session.commit()
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(128)
    origin = f"http://127.0.0.1:{listener.getsockname()[1]}"
    os.environ.update(APP_URL=origin, API_URL=origin)
    import uvicorn
    from reality.web.app import app as product
    from reality.web.desktop import create_desktop_app

    app = create_desktop_app(
        origin=origin,
        frontend=Path(config["frontend"]),
        session_factory=Session,
        product=product,
        development=True,
    )
    server = uvicorn.Server(uvicorn.Config(app, log_level="error", access_log=False))

    def parent_closed():
        sys.stdin.read()
        server.should_exit = True

    threading.Thread(target=parent_closed, daemon=True).start()
    # Only native code reads stdout. Never log this message or put it in a URL.
    print(
        json.dumps(
            {
                "origin": origin,
                "token": token,
                "cookie_name": "reality_session",
                "path": "/app",
                "test_root": str(Path(config["artifact_root"]).parent),
            }
        ),
        flush=True,
    )
    try:
        server.run(sockets=[listener])
    finally:
        listener.close()
        with Session() as session:
            revoke_session(session, token)
            session.commit()


if __name__ == "__main__":
    main()
