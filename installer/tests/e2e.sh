#!/bin/sh
# End-to-end proof for the installer (spec 187 FR-016): install from locally
# built images, check ports and health, sign in, create data, back up, destroy,
# restore, upgrade. Used by .github/workflows/installer.yml and by hand:
#
#   sh installer/tests/e2e.sh                # builds the five images first
#   REALITY_E2E_SKIP_BUILD=1 sh installer/tests/e2e.sh
set -eu

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
REGISTRY="${REALITY_E2E_REGISTRY:-reality-e2e}"
TAG_A="${REALITY_E2E_TAG_A:-e2e-a}"
TAG_B="${REALITY_E2E_TAG_B:-e2e-b}"
PORT="${REALITY_E2E_PORT:-18080}"
MCP_PORT="${REALITY_E2E_MCP_PORT:-18001}"
PROJECT="${REALITY_E2E_PROJECT:-reality-e2e}"
WORK="${REALITY_E2E_WORK:-$(mktemp -d)}"
OWNER="owner@example.com"

export REALITY_INSTALLER_SOURCE_DIR="$ROOT/installer"
export REALITY_IMAGE_REGISTRY="$REGISTRY"
export REALITY_PROJECT_NAME="$PROJECT"

step() { printf '\n==> %s\n' "$*"; }
die() { printf 'e2e: %s\n' "$*" >&2; exit 1; }

cleanup() {
  if [ -d "$WORK/reality" ]; then
    (cd "$WORK/reality" && docker compose down -v --remove-orphans >/dev/null 2>&1) || true
  fi
}
trap cleanup EXIT INT TERM

build_images() {
  step "Building images as $REGISTRY/reality-<role>:$TAG_A (api also as $TAG_B)"
  for role in api mcp web scheduler worker; do
    docker build -q -f "$ROOT/apps/$role/Dockerfile" \
      --build-arg REALITY_VERSION="$TAG_A" --build-arg REALITY_COMMIT=e2e \
      -t "$REGISTRY/reality-$role:$TAG_A" "$ROOT"
    docker tag "$REGISTRY/reality-$role:$TAG_A" "$REGISTRY/reality-$role:$TAG_B"
  done
  docker build -q -f "$ROOT/apps/api/Dockerfile" \
    --build-arg REALITY_VERSION="$TAG_B" --build-arg REALITY_COMMIT=e2e \
    -t "$REGISTRY/reality-api:$TAG_B" "$ROOT"
}

app() { printf 'http://127.0.0.1:%s%s' "$PORT" "$1"; }

status_version() {
  curl -fsS "$(app /api/v1/system/status)" | sed -n 's/.*"version":"\([^"]*\)".*/\1/p'
}

login() { # password cookie-jar
  curl -fsS -c "$2" -H 'Content-Type: application/json' \
    -d "{\"email\":\"$OWNER\",\"password\":\"$1\"}" "$(app /api/auth/login)" >/dev/null
}

published_ports() {
  docker ps --filter "label=com.docker.compose.project=$PROJECT" --format '{{.Ports}}' \
    | tr ',' '\n' | sed 's/^ *//' | grep -- '->' | sort -u
}

env_value() { sed -n "s/^$1=//p" "$WORK/reality/.env" | head -n 1; }

[ "${REALITY_E2E_SKIP_BUILD:-0}" = "1" ] || build_images

step "Install into $WORK/reality on port $PORT (project $PROJECT)"
mkdir -p "$WORK"
if [ -d "$WORK/reality" ]; then
  (cd "$WORK/reality" && docker compose down -v --remove-orphans >/dev/null 2>&1) || true
  rm -rf "$WORK/reality"
fi
cd "$WORK"
REALITY_IMAGE_TAG="$TAG_A" sh "$ROOT/installer/install.sh" \
  --port "$PORT" --mcp-port "$MCP_PORT" --email "$OWNER" | tee "$WORK/install.log"
grep -q "Password:" "$WORK/install.log" || die "the installer did not print the owner password"

step "Health, version and ports"
curl -fsS "$(app /healthz)" | grep -q '"ok"' || die "healthz failed"
[ "$(status_version)" = "$TAG_A" ] || die "expected version $TAG_A, got $(status_version)"
ports=$(published_ports)
printf '%s\n' "$ports"
printf '%s\n' "$ports" | grep -q ":$PORT->80/tcp" || die "App port $PORT is not published"
printf '%s\n' "$ports" | grep -q "^127.0.0.1:$MCP_PORT->8001/tcp" || die "MCP is not on loopback"
if printf '%s\n' "$ports" | grep -- '->8001/tcp' | grep -qv '^127.0.0.1:'; then die "MCP is published beyond loopback"; fi
targets=$(printf '%s\n' "$ports" | sed 's/.*->//' | sort -u | tr '\n' ' ')
[ "$targets" = "80/tcp 8001/tcp " ] || die "unexpected published container ports: $targets"
curl -fsS "http://127.0.0.1:$MCP_PORT/readyz" >/dev/null || die "MCP readyz failed on loopback"

step "Second run is a no-op"
sh "$ROOT/installer/install.sh" --port "$PORT" --mcp-port "$MCP_PORT" | grep -q "already installed" \
  || die "second run did not report the existing installation"

step "Sign in as the first owner and create a company"
password=$(env_value REALITY_PLATFORM_ADMIN_PASSWORD)
key_before=$(env_value REALITY_MASTER_KEY)
login "$password" "$WORK/jar"
curl -fsS -b "$WORK/jar" -H 'Content-Type: application/json' \
  -d '{"request_key":"e2e-company","name":"E2E Proof GmbH","environment":"business","content":"empty","confirmed":true}' \
  "$(app /api/company-setup)" >/dev/null || die "company creation failed"
curl -fsS -b "$WORK/jar" "$(app /api/v1/companies)" | grep -q "E2E Proof GmbH" || die "company not listed"
docker run --rm -v "${PROJECT}_artifacts:/data" alpine:3 \
  sh -c 'echo proof > /data/e2e-marker && chown 1001:1001 /data/e2e-marker'

step "Backup"
sh "$WORK/reality/reality.sh" backup | tee "$WORK/backup.log"
archive=$(sed -n 's/^Backup written: //p' "$WORK/backup.log")
[ -f "$archive" ] || die "no backup archive"
tar -tf "$archive" | grep -q "config/.env" || die "archive lacks .env"

step "Destroy the installation (containers, volumes, directory)"
(cd "$WORK/reality" && docker compose down -v --remove-orphans)
rm -rf "$WORK/reality"

step "Restore on the empty host"
sh "$ROOT/installer/install.sh" restore "$archive" --dir "$WORK/reality" | tee "$WORK/restore.log"
[ "$(env_value REALITY_MASTER_KEY)" = "$key_before" ] || die "master key changed across restore"
login "$password" "$WORK/jar2"
curl -fsS -b "$WORK/jar2" "$(app /api/v1/companies)" | grep -q "E2E Proof GmbH" || die "company lost in restore"
docker run --rm -v "${PROJECT}_artifacts:/data:ro" alpine:3 cat /data/e2e-marker | grep -q proof \
  || die "artifact marker lost in restore"

step "Upgrade $TAG_A -> $TAG_B"
sh "$WORK/reality/reality.sh" upgrade --version "$TAG_B" | tee "$WORK/upgrade.log"
[ "$(env_value REALITY_VERSION)" = "$TAG_B" ] || die ".env not repinned"
[ "$(status_version)" = "$TAG_B" ] || die "expected version $TAG_B after upgrade, got $(status_version)"
login "$password" "$WORK/jar3"

step "PASS: install, ports, sign-in, backup, restore and upgrade verified"
