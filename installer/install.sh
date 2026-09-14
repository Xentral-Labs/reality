#!/bin/sh
# Reality self-hosted installer (spec 187).
#
#   curl -fsSL https://get.runreality.ai | sh
#   curl -fsSL https://get.runreality.ai | sh -s -- upgrade
#   ./reality/reality.sh backup
#
# One POSIX shell script for install, upgrade, start, stop, logs, status,
# backup and restore. It never reads stdin (it is usually a pipe), it writes
# only into the installation directory, and it stops before writing anything
# when a prerequisite is missing.
set -eu

# The publish workflow replaces the placeholder with the release version so a
# downloaded script installs the release it belongs to. A raw copy from the
# repository installs "edge", the moving tag of main.
INSTALLER_VERSION="__REALITY_INSTALLER_VERSION__"
REPO="Xentral-Labs/reality"
REPO_URL="https://github.com/${REPO}"
RAW_URL="https://raw.githubusercontent.com/${REPO}"
ASSETS="compose.yml compose.direct.yml compose.proxy.yml compose.s3.yml Caddyfile README.md"
HEALTH_BUDGET_SECONDS=180

DOCKER="${REALITY_DOCKER_BIN:-docker}"
SOURCE_DIR="${REALITY_INSTALLER_SOURCE_DIR:-}"

COMMAND=""
DIR=""
PORT=8080
BIND="0.0.0.0"
MCP_PORT=8001
EMAIL="${REALITY_ADMIN_EMAIL:-}"
DOMAIN=""
VERSION=""
DRY_RUN=0
ARCHIVE=""

usage() {
  cat <<'USAGE'
Reality self-hosted installer

Usage:
  install.sh [install] [--email <owner email>] [--domain <host>] [--port <n>]
             [--bind <address>] [--mcp-port <n>] [--version <release>] [--dir <path>]
             [--dry-run]
  reality.sh upgrade [--version <release>]
  reality.sh start | stop | logs | status
  reality.sh backup
  reality.sh restore <archive.tar>

Flags:
  --email     First owner (platform admin). Default: owner@reality.local
  --domain    Public hostname. Enables HTTPS through Caddy on ports 80 and 443
              and serves MCP on mcp.<domain>. Needs both DNS records.
  --port      Host port for the App without a domain. Default: 8080
  --bind      Host address for that port. Default: 0.0.0.0
  --mcp-port  Loopback port for MCP without a domain. Default: 8001
  --version   Release to install or upgrade to, e.g. 0.1.0, edge, sha-a204c14
  --dir       Installation directory. Default: ./reality
  --dry-run   Write the files; skip the Docker and port checks
  --help      This text

Environment:
  REALITY_ADMIN_EMAIL            Same as --email
  REALITY_IMAGE_REGISTRY         Image registry, default ghcr.io/xentral-labs
  REALITY_PROJECT_NAME           Compose project (container and volume prefix), default reality
  REALITY_INSTALLER_SOURCE_DIR   Take the Compose files from a local directory
USAGE
}

say() { printf '%s\n' "$*"; }
warn() { printf 'reality: %s\n' "$*" >&2; }
fail() { warn "$*"; exit 1; }

need_value() {
  [ "$#" -ge 2 ] || { warn "$1 requires a value"; usage >&2; exit 2; }
}

parse_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      install|upgrade|start|stop|logs|status|backup|restore)
        [ -z "$COMMAND" ] || { warn "only one command is allowed"; usage >&2; exit 2; }
        COMMAND="$1" ;;
      --email) need_value "$@"; EMAIL="$2"; shift ;;
      --domain) need_value "$@"; DOMAIN="$2"; shift ;;
      --port) need_value "$@"; PORT="$2"; shift ;;
      --bind) need_value "$@"; BIND="$2"; shift ;;
      --mcp-port) need_value "$@"; MCP_PORT="$2"; shift ;;
      --version) need_value "$@"; VERSION="$2"; shift ;;
      --dir) need_value "$@"; DIR="$2"; shift ;;
      --dry-run) DRY_RUN=1 ;;
      --help|-h) usage; exit 0 ;;
      -*) warn "unknown flag: $1"; usage >&2; exit 2 ;;
      *)
        if [ "$COMMAND" = "restore" ] && [ -z "$ARCHIVE" ]; then
          ARCHIVE="$1"
        else
          warn "unexpected argument: $1"; usage >&2; exit 2
        fi ;;
    esac
    shift
  done
  [ -n "$COMMAND" ] || COMMAND="install"
  case "$PORT" in
    ''|*[!0-9]*) fail "--port must be a number" ;;
  esac
  case "$MCP_PORT" in
    ''|*[!0-9]*) fail "--mcp-port must be a number" ;;
  esac
  case "$DOMAIN" in
    */*|*:*|http*) fail "--domain takes a bare hostname such as reality.example.com" ;;
  esac
}

# The control copy lives inside the installation directory; when invoked as
# ./reality/reality.sh the directory is the script's own.
default_dir() {
  if [ -n "$DIR" ]; then
    printf '%s' "$DIR"
  elif [ -f "$0" ] && [ -f "$(dirname "$0")/.env" ]; then
    printf '%s' "$(dirname "$0")"
  else
    printf '%s' "./reality"
  fi
}

# --- prerequisites -----------------------------------------------------------

check_docker() {
  command -v "$DOCKER" >/dev/null 2>&1 \
    || fail "Docker is not installed. Install Docker Engine or Docker Desktop first: https://docs.docker.com/get-docker/"
  "$DOCKER" info >/dev/null 2>&1 \
    || fail "The Docker daemon is not running or you lack permission to use it. Start Docker or add your user to the docker group."
  "$DOCKER" compose version >/dev/null 2>&1 \
    || fail "The Docker Compose v2 plugin is missing ('docker compose', not 'docker-compose'). Install the compose plugin."
}

check_curl() {
  [ -n "$SOURCE_DIR" ] || command -v curl >/dev/null 2>&1 || fail "curl is required to download the Compose files."
}

port_in_use() {
  if command -v nc >/dev/null 2>&1; then
    nc -z 127.0.0.1 "$1" >/dev/null 2>&1
  elif command -v ss >/dev/null 2>&1; then
    ss -ltn 2>/dev/null | awk '{print $4}' | grep -q ":$1\$"
  elif command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
  else
    return 1
  fi
}

check_ports() {
  if [ -n "$DOMAIN" ]; then
    for p in 80 443; do
      port_in_use "$p" && fail "port $p is already in use; the domain mode needs 80 and 443. Stop the other service first."
    done
  else
    port_in_use "$PORT" && fail "port $PORT is already in use. Pick another with --port <n>."
    port_in_use "$MCP_PORT" && fail "port $MCP_PORT is already in use on this host; MCP needs it on loopback."
  fi
  return 0
}

# --- secrets -----------------------------------------------------------------

random_hex() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex "$1"
  else
    od -An -N"$1" -tx1 /dev/urandom | tr -d ' \n'
  fi
}

# Fernet keys are 32 random bytes in URL-safe base64 (44 characters).
fernet_key() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -base64 32 | tr '+/' '-_'
  else
    od -An -N32 -tx1 /dev/urandom | tr -d ' \n' | xxd -r -p | base64 | tr '+/' '-_'
  fi
}

# --- assets ------------------------------------------------------------------

asset_base_url() {
  case "$1" in
    edge) printf '%s/main/installer' "$RAW_URL" ;;
    sha-*) printf '%s/%s/installer' "$RAW_URL" "${1#sha-}" ;;
    *) printf '%s/releases/download/v%s' "$REPO_URL" "$1" ;;
  esac
}

fetch_asset() { # name destination version
  if [ -n "$SOURCE_DIR" ]; then
    [ -f "$SOURCE_DIR/$1" ] || fail "missing $1 in REALITY_INSTALLER_SOURCE_DIR=$SOURCE_DIR"
    cp "$SOURCE_DIR/$1" "$2"
  else
    curl -fsSL "$(asset_base_url "$3")/$1" -o "$2" \
      || fail "could not download $1 for version $3 from $(asset_base_url "$3")"
  fi
}

fetch_assets() { # directory version
  for name in $ASSETS; do
    fetch_asset "$name" "$1/$name" "$2"
  done
  fetch_asset install.sh "$1/reality.sh" "$2"
  chmod +x "$1/reality.sh"
}

resolve_version() {
  if [ -n "$VERSION" ]; then
    printf '%s' "$VERSION"
  elif [ "$INSTALLER_VERSION" != "__REALITY_INSTALLER_VERSION__" ]; then
    printf '%s' "$INSTALLER_VERSION"
  elif [ -n "$SOURCE_DIR" ]; then
    printf '%s' "${REALITY_IMAGE_TAG:-edge}"
  else
    printf '%s' "edge"
  fi
}

latest_release() {
  command -v curl >/dev/null 2>&1 || fail "curl is required to look up the latest release; pass --version instead."
  tag=$(curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest" \
    | sed -n 's/.*"tag_name": *"v\{0,1\}\([^"]*\)".*/\1/p' | head -n 1)
  [ -n "$tag" ] || fail "could not determine the latest release; pass --version <release>."
  printf '%s' "$tag"
}

# --- .env --------------------------------------------------------------------

env_value() { # key file
  sed -n "s/^$1=//p" "$2" | head -n 1
}

write_env() { # file version
  if [ -n "$DOMAIN" ]; then
    compose_file="compose.yml:compose.proxy.yml"
    app_url="https://${DOMAIN}"
    mcp_url="https://mcp.${DOMAIN}/"
    cookie_secure="true"
    mcp_env="production"
  else
    compose_file="compose.yml:compose.direct.yml"
    app_url="http://localhost:${PORT}"
    mcp_url="http://localhost:${MCP_PORT}/"
    cookie_secure="false"
    mcp_env=""
  fi
  owner_email="${EMAIL:-owner@reality.local}"
  owner_password="$(random_hex 12)"
  cat >"$1" <<EOF
# Reality self-hosted configuration, written by install.sh on $(date -u +%Y-%m-%dT%H:%M:%SZ).
# Keep this file: REALITY_MASTER_KEY encrypts stored credentials and cannot be recovered.

REALITY_VERSION=$2
REALITY_IMAGE_REGISTRY=${REALITY_IMAGE_REGISTRY:-ghcr.io/xentral-labs}
COMPOSE_PROJECT_NAME=${REALITY_PROJECT_NAME:-reality}

COMPOSE_FILE=${compose_file}
REALITY_BIND=${BIND}
REALITY_PORT=${PORT}
REALITY_MCP_PORT=${MCP_PORT}
REALITY_DOMAIN=${DOMAIN}

APP_URL=${app_url}
MCP_URL=${mcp_url}
REALITY_COOKIE_SECURE=${cookie_secure}
REALITY_MCP_ENV=${mcp_env}

POSTGRES_DB=reality
POSTGRES_USER=reality
POSTGRES_PASSWORD=$(random_hex 24)

REALITY_MASTER_KEY=$(fernet_key)

REALITY_PLATFORM_ADMIN_EMAIL=${owner_email}
REALITY_PLATFORM_ADMIN_PASSWORD=${owner_password}
REALITY_AUTO_APPROVE_LIMIT=0

REALITY_EMAIL_PROVIDER=
REALITY_EMAIL_FROM=
RESEND_API_KEY=
REALITY_SMTP_HOST=
REALITY_SMTP_PORT=587
REALITY_SMTP_TLS=true
REALITY_SMTP_USERNAME=
REALITY_SMTP_PASSWORD=

ANTHROPIC_API_KEY=
ANTHROPIC_WORKSPACE_ID=

MINIO_ROOT_USER=
MINIO_ROOT_PASSWORD=
REALITY_S3_BUCKET=reality-artifacts
REALITY_S3_REGION=eu-central-1
EOF
  chmod 600 "$1"
}

set_env_value() { # key value file
  tmp="$3.tmp"
  awk -v key="$1" -v value="$2" 'BEGIN { done = 0 }
    index($0, key "=") == 1 { print key "=" value; done = 1; next }
    { print }
    END { if (!done) print key "=" value }' "$3" >"$tmp"
  mv "$tmp" "$3"
  chmod 600 "$3"
}

# --- compose -----------------------------------------------------------------

# Compose resolves COMPOSE_FILE from the .env in the working directory, so
# every call runs inside the installation directory.
compose() {
  (cd "$DIR" && "$DOCKER" compose "$@")
}

wait_healthy() { # service
  waited=0
  while [ "$waited" -lt "$HEALTH_BUDGET_SECONDS" ]; do
    id=$(compose ps -q "$1" 2>/dev/null || true)
    if [ -n "$id" ]; then
      state=$("$DOCKER" inspect --format '{{.State.Health.Status}}' "$id" 2>/dev/null || true)
      [ "$state" = "healthy" ] && return 0
    fi
    sleep 3
    waited=$((waited + 3))
  done
  return 1
}

start_stack() {
  say "Starting Reality $(env_value REALITY_VERSION "$DIR/.env") (images are pulled on first start) ..."
  if ! compose up -d --remove-orphans; then
    warn "start failed. If an image could not be pulled, check REALITY_VERSION and"
    warn "REALITY_IMAGE_REGISTRY in $DIR/.env and your network. Migration log:"
    compose logs --no-log-prefix migrate >&2 || true
    exit 1
  fi
  if ! wait_healthy web; then
    warn "the App did not become healthy within ${HEALTH_BUDGET_SECONDS}s. Inspect with:"
    warn "  $DIR/reality.sh logs"
    exit 1
  fi
}

print_access() {
  domain=$(env_value REALITY_DOMAIN "$DIR/.env")
  say ""
  say "Reality is running."
  if [ -n "$domain" ]; then
    say "  App:  https://${domain}   (the certificate may take a minute on first start)"
    say "  MCP:  https://mcp.${domain}/"
  else
    say "  App:  $(env_value APP_URL "$DIR/.env")"
    say "  MCP:  $(env_value MCP_URL "$DIR/.env")   (loopback only)"
  fi
}

# --- commands ----------------------------------------------------------------

cmd_install() {
  DIR=$(default_dir)
  if [ -e "$DIR/.env" ]; then
    say "Reality is already installed in $DIR (version $(env_value REALITY_VERSION "$DIR/.env"))."
    say "To upgrade:   $DIR/reality.sh upgrade"
    say "To reinstall: stop it, move the directory away, and run the installer again."
    exit 0
  fi
  [ ! -e "$DIR" ] || [ -d "$DIR" ] || fail "$DIR exists and is not a directory"
  parent=$(dirname "$DIR")
  [ -w "$parent" ] || fail "cannot write to $parent"
  check_curl
  if [ "$DRY_RUN" -eq 0 ]; then
    check_docker
    check_ports
  fi
  version=$(resolve_version)

  mkdir -p "$DIR"
  fetch_assets "$DIR" "$version"
  write_env "$DIR/.env" "$version"
  say "Wrote $DIR/.env, Compose files and reality.sh for Reality ${version}."
  if [ -z "$EMAIL" ]; then
    say "No --email given; the first owner is owner@reality.local. To add another owner later, set both REALITY_PLATFORM_ADMIN_* values in .env and run reality.sh start."
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    say "Dry run: Docker was not started."
    exit 0
  fi
  start_stack
  print_access
  say ""
  say "First owner sign-in (shown once, keep it):"
  say "  Email:     $(env_value REALITY_PLATFORM_ADMIN_EMAIL "$DIR/.env")"
  say "  Password:  $(env_value REALITY_PLATFORM_ADMIN_PASSWORD "$DIR/.env")"
  say ""
  say "Commands and backups: see $DIR/README.md"
}

require_installation() {
  DIR=$(default_dir)
  [ -f "$DIR/.env" ] || fail "no installation found in $DIR. Run the installer first or pass --dir <path>."
}

cmd_upgrade() {
  require_installation
  current=$(env_value REALITY_VERSION "$DIR/.env")
  [ -n "$current" ] || fail "$DIR/.env carries no REALITY_VERSION; this installation was not created by the installer. Follow the Docker Compose guide to upgrade by hand."
  if [ -n "$VERSION" ]; then
    target="$VERSION"
  elif [ "$INSTALLER_VERSION" != "__REALITY_INSTALLER_VERSION__" ]; then
    target="$INSTALLER_VERSION"
  elif [ -n "$SOURCE_DIR" ]; then
    target="${REALITY_IMAGE_TAG:-$current}"
  else
    target=$(latest_release)
  fi
  if [ "$target" = "$current" ]; then
    say "Reality $current is already installed; nothing to do."
    exit 0
  fi
  check_curl
  [ "$DRY_RUN" -eq 1 ] || check_docker
  say "Upgrading Reality $current -> $target ..."
  fetch_assets "$DIR" "$target"
  set_env_value REALITY_VERSION "$target" "$DIR/.env"
  if [ "$DRY_RUN" -eq 1 ]; then
    say "Dry run: .env now pins $target; Docker was not touched."
    exit 0
  fi
  start_stack
  print_access
}

cmd_start() { require_installation; check_docker; start_stack; print_access; }
cmd_stop() { require_installation; check_docker; compose down; say "Stopped. Data is kept in the volumes."; }
cmd_logs() { require_installation; check_docker; compose logs -f --tail 200; }
cmd_status() {
  require_installation; check_docker
  say "Reality $(env_value REALITY_VERSION "$DIR/.env") in $DIR"
  compose ps
}

volume_name() { printf '%s_%s' "$(env_value COMPOSE_PROJECT_NAME "$DIR/.env")" "$1"; }

cmd_backup() {
  require_installation; check_docker
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  archive="$(pwd)/reality-backup-${stamp}.tar"
  work=$(mktemp -d)
  user=$(env_value POSTGRES_USER "$DIR/.env")
  database=$(env_value POSTGRES_DB "$DIR/.env")
  say "Dumping PostgreSQL ..."
  compose exec -T db pg_dump -U "$user" -d "$database" -Fc >"$work/database.dump" \
    || fail "pg_dump failed; is the stack running? (./reality.sh start)"
  say "Archiving source binaries ..."
  "$DOCKER" run --rm -v "$(volume_name artifacts):/data:ro" -v "$work:/backup" alpine:3 \
    tar -czf /backup/artifacts.tar.gz -C /data . || fail "could not archive the artifacts volume"
  mkdir -p "$work/config"
  cp "$DIR/.env" "$work/config/.env"
  for name in $ASSETS reality.sh; do
    [ -f "$DIR/$name" ] && cp "$DIR/$name" "$work/config/$name"
  done
  tar -cf "$archive" -C "$work" .
  rm -rf "$work"
  say ""
  say "Backup written: $archive"
  say "It contains the database, the source binaries and .env with REALITY_MASTER_KEY."
  say "Store it where only operators can read it."
}

cmd_restore() {
  [ -n "$ARCHIVE" ] || { warn "restore needs an archive path"; usage >&2; exit 2; }
  [ -f "$ARCHIVE" ] || fail "archive not found: $ARCHIVE"
  DIR=$(default_dir)
  if [ -e "$DIR" ] && [ -n "$(ls -A "$DIR" 2>/dev/null)" ]; then
    fail "$DIR is not empty. Restore only into a fresh directory (use --dir <path> or move the old one away)."
  fi
  check_docker
  work=$(mktemp -d)
  tar -xf "$ARCHIVE" -C "$work" || fail "could not read the archive"
  if [ ! -f "$work/config/.env" ] || [ ! -f "$work/database.dump" ]; then
    fail "the archive is not a Reality backup"
  fi
  mkdir -p "$DIR"
  cp "$work/config/.env" "$DIR/.env"
  chmod 600 "$DIR/.env"
  for name in $ASSETS reality.sh; do
    [ -f "$work/config/$name" ] && cp "$work/config/$name" "$DIR/$name"
  done
  chmod +x "$DIR/reality.sh"
  user=$(env_value POSTGRES_USER "$DIR/.env")
  database=$(env_value POSTGRES_DB "$DIR/.env")

  say "Starting PostgreSQL ..."
  compose up -d db
  wait_healthy db || fail "PostgreSQL did not become healthy"
  say "Restoring the database ..."
  compose exec -T db pg_restore -U "$user" -d "$database" --clean --if-exists --no-owner --no-privileges <"$work/database.dump" \
    || warn "pg_restore reported errors; continuing (harmless on an empty database)"
  say "Restoring source binaries ..."
  "$DOCKER" run --rm -v "$(volume_name artifacts):/data" -v "$work:/backup:ro" alpine:3 \
    sh -c 'tar -xzf /backup/artifacts.tar.gz -C /data && chown -R 1001:1001 /data' \
    || fail "could not restore the artifacts volume"
  rm -rf "$work"
  start_stack
  print_access
  say "Restored from $ARCHIVE. Encrypted credentials are readable because .env carries the original key."
}

main() {
  parse_args "$@"
  case "$COMMAND" in
    install) cmd_install ;;
    upgrade) cmd_upgrade ;;
    start) cmd_start ;;
    stop) cmd_stop ;;
    logs) cmd_logs ;;
    status) cmd_status ;;
    backup) cmd_backup ;;
    restore) cmd_restore ;;
  esac
}

main "$@"
