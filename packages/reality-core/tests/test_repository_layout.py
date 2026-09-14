from __future__ import annotations

from pathlib import Path

import yaml


def repository_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "compose.yml").exists() and (candidate / "specs").is_dir():
            return candidate
    raise AssertionError("Repository root could not be resolved")


def test_stable_application_and_shared_core_tree_is_explicit() -> None:
    root = repository_root()
    required = {
        "apps/api/Dockerfile",
        "apps/mcp/Dockerfile",
        "apps/web/Dockerfile",
        "packages/reality-core/pyproject.toml",
        "packages/reality-core/src/reality",
        "packages/reality-core/migrations",
        "packages/reality-core/config",
        "packages/reality-core/fixtures",
        "packages/reality-core/tests",
        "packages/reality-core/alembic.ini",
    }
    assert all((root / path).exists() for path in required)
    assert not (root / "backend").exists()
    assert not (root / "frontend").exists()


def test_api_and_mcp_images_install_one_shared_core_without_copied_rules() -> None:
    root = repository_root()
    api = (root / "apps/api/Dockerfile").read_text(encoding="utf-8")
    mcp = (root / "apps/mcp/Dockerfile").read_text(encoding="utf-8")

    for dockerfile in (api, mcp):
        assert "packages/reality-core" in dockerfile
        assert "pip install" in dockerfile
    assert "reality.web.app:app" in api
    assert "reality.mcp.app:app" in mcp
    assert not (root / "apps/api/src/reality").exists()
    assert not (root / "apps/mcp/src/reality").exists()


def test_python_images_copy_all_force_included_package_directories() -> None:
    root = repository_root()
    dockerfiles = (
        "Dockerfile",
        "apps/api/Dockerfile",
        "apps/docs/Dockerfile",
        "apps/mcp/Dockerfile",
        "apps/scheduler/Dockerfile",
        "apps/worker/Dockerfile",
    )

    for path in dockerfiles:
        dockerfile = (root / path).read_text(encoding="utf-8")
        assert "packages/reality-core/storylines" in dockerfile, path


def test_compose_maps_each_runtime_to_its_application_definition() -> None:
    root = repository_root()
    compose = yaml.safe_load((root / "compose.yml").read_text(encoding="utf-8"))
    services = compose["services"]

    assert services["api"]["build"]["dockerfile"] == "apps/api/Dockerfile"
    assert services["mcp"]["build"]["dockerfile"] == "apps/mcp/Dockerfile"
    assert services["web"]["build"]["dockerfile"] == "apps/web/Dockerfile"
    assert services["api"]["build"]["context"] == "."
    assert services["mcp"]["build"]["context"] == "."
    assert services["web"]["build"]["context"] == "."
    assert "api" in services["web"]["depends_on"]
    assert (
        services["api"]["environment"]["REALITY_DB_POOL_SIZE"]
        != services["mcp"]["environment"]["REALITY_DB_POOL_SIZE"]
    )


def test_active_repository_contracts_use_only_current_paths() -> None:
    root = repository_root()
    active_files = (
        ".github/workflows/quality.yml",
        "Makefile",
        "README.md",
        "compose.yml",
        "scripts/check_spec_policy.py",
        "docs/ARCHITECTURE.md",
        "docs/CLI_SPEC.md",
        "docs/SPEC_COVERAGE_MATRIX.md",
        "docs/SPEC_DRIVEN_WORKFLOW.md",
        "docs/WEB_SPEC.md",
        "docs/features/operational_fields.md",
        "docs/features/web.md",
    )
    combined = "\n".join(
        (root / path).read_text(encoding="utf-8") for path in active_files
    )
    assert "backend/" not in combined
    assert "frontend/" not in combined
    assert "packages/reality-core" in combined
    assert "apps/web" in combined


def test_documented_commands_resolve_to_current_workspaces() -> None:
    root = repository_root()
    makefile = (root / "Makefile").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    workflow = (root / ".github/workflows/quality.yml").read_text(encoding="utf-8")

    for text in (makefile, readme, workflow):
        assert "packages/reality-core" in text
        assert "apps/web" in text
    assert "pip install -e './packages/reality-core[dev]'" in readme
    for target, service in (
        ("api", "api"),
        ("app", "web"),
        ("docs", "docs"),
        ("mcp", "mcp"),
    ):
        assert f"{target}:" in makefile
        assert f"docker compose up --build {service}" in makefile


def test_public_site_and_product_origins_are_explicit() -> None:
    root = repository_root()
    readme = (root / "README.md").read_text(encoding="utf-8")
    env = (root / ".env.example").read_text(encoding="utf-8")
    compose = (root / "compose.yml").read_text(encoding="utf-8")
    workflow = (root / ".github/workflows/quality.yml").read_text(encoding="utf-8")

    for origin in (
        "https://runreality.ai",
        "https://app.runreality.ai",
        "https://api.runreality.ai",
        "https://mcp.runreality.ai",
        "https://docs.runreality.ai",
    ):
        assert origin in readme
    for url in (
        "SITE_URL=http://localhost:8082",
        "APP_URL=http://localhost:8080",
        "API_URL=http://localhost:8000",
        "MCP_URL=http://localhost:8001/",
        "DOCS_URL=http://localhost:8083",
    ):
        assert url in env
    assert "railway.app" not in env
    assert "runreality.ai" not in env
    assert "FRONTEND_URL=" not in env
    assert "BACKEND_URL=" not in env
    for port in (
        "API_PORT=8000",
        "APP_PORT=8080",
        "MCP_PORT=8001",
        "DOCS_PORT=8083",
    ):
        assert port in env
    for variable in ("APP_PORT", "API_PORT", "MCP_PORT", "DOCS_PORT"):
        assert f"${{{variable}:-" in compose
    assert "APP_URL: ${APP_URL:-}" in compose
    assert "API_URL: ${API_URL:-}" in compose
    assert "FRONTEND_URL:" not in compose
    assert "BACKEND_URL:" not in compose
    assert "apps/docs/package-lock.json" in workflow
    assert "cd apps/docs" in workflow


def test_development_stack_has_reload_and_observable_logs() -> None:
    root = repository_root()
    makefile = (root / "Makefile").read_text(encoding="utf-8")
    development = (root / "compose.dev.yml").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")

    compose_command = "docker compose -f compose.yml -f compose.dev.yml"
    for target in ("dev", "dev-up", "dev-logs", "dev-status", "dev-down"):
        assert f"{target}:" in makefile
    assert f"{compose_command} up --build" in makefile
    assert f"{compose_command} logs --follow" in makefile
    assert f"{compose_command} ps" in makefile
    assert f"{compose_command} down --remove-orphans" in makefile

    assert development.count('"--reload",') == 2
    assert development.count('["npm", "run", "dev"') == 2
    assert "./packages/reality-core:/app/packages/reality-core" in development
    assert "./apps/web:/app" in development
    assert "./apps/docs:/app" in development
    assert "make dev-logs" in readme
    for browser in ("web",):
        package = (root / "apps" / browser / "package.json").read_text(encoding="utf-8")
        assert "vite --config vite.config.ts" in package


def test_temporary_hosted_demo_contract_is_safe_and_reversible() -> None:
    root = repository_root()
    guide = (root / "docs/RAILWAY_DEMO.md").read_text(encoding="utf-8")

    for required in (
        "alembic upgrade head",
        "api.railway.internal:8000",
        "REALITY_COOKIE_SECURE=true",
        "REALITY_AUTH_EXPOSE_CODES=false",
        "REALITY_PUBLIC_SIGNUP_ENABLED=false",
        "REALITY_ARTIFACT_STORAGE=file",
        "ephemeral",
        "Remove the public domain",
        "revoke",
    ):
        assert required.casefold() in guide.casefold()
    assert "`app`, `docs`\nand `mcp` receive separate" in guide
    assert "apps/mcp/Dockerfile" in guide
    assert "make railway-deploy" in guide
    deploy_script = (root / "scripts" / "deploy_railway_demo.sh").read_text(
        encoding="utf-8"
    )
    assert "deploy_service api" in deploy_script
    assert deploy_script.index("deploy_service api") < deploy_script.index(
        "deploy_service scheduler"
    )
    assert deploy_script.index("deploy_service scheduler") < deploy_script.index(
        "deploy_service worker"
    )
    assert "verify_background_service scheduler" in deploy_script
    assert "verify_background_service worker" in deploy_script
    assert "deploy_service app" in deploy_script
    background_image = (root / "Dockerfile").read_text(encoding="utf-8")
    assert "REALITY_BACKGROUND_ROLE" in background_image
    assert "reality-scheduler" in background_image
    assert "reality-worker" in background_image
    assert "scheduler|worker" not in background_image
    assert "`specs/032-railway-demo-deployment`" in guide
