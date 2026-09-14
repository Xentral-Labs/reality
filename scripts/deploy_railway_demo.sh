#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mode="product"
dry_run=false
while (( $# )); do
  case "$1" in
    --only)
      [[ $# -ge 2 ]] || { printf 'Missing --only value.\n' >&2; exit 2; }
      mode="$2"; shift 2 ;;
    --dry-run) dry_run=true; shift ;;
    --help)
      printf 'Usage: %s [--only product|site|all] [--dry-run]\n' "$0"
      printf 'Site deployment requires REALITY_RAILWAY_SITE_ROOT pointing to a separate Git checkout.\n'
      exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
done
case "$mode" in product|site|all) ;; *) printf 'Invalid deployment mode: %s\n' "$mode" >&2; exit 2 ;; esac

site_root=""
if [[ "$mode" != product ]]; then
  : "${REALITY_RAILWAY_SITE_ROOT:?Set REALITY_RAILWAY_SITE_ROOT to the separate marketing repository checkout.}"
  site_root="$(cd "$REALITY_RAILWAY_SITE_ROOT" && pwd)"
  [[ "$site_root" != "$repository_root" ]] || { printf 'Site must use a separate checkout.\n' >&2; exit 2; }
fi

services=()
if [[ "$mode" != site ]]; then services=(api scheduler worker mcp docs); fi
if [[ "$mode" != product ]]; then services+=(site); fi
if [[ "$mode" != site ]]; then services+=(app); fi

source_root() {
  if [[ "$1" == site ]]; then printf '%s' "$site_root"; else printf '%s' "$repository_root"; fi
}
dockerfile() {
  case "$1" in
    site) printf 'apps/site/Dockerfile.railway' ;;
    app) printf 'apps/web/Dockerfile' ;;
    *) printf 'apps/%s/Dockerfile' "$1" ;;
  esac
}

# Validate all selected sources before any deployment, including combined mode.
for service in "${services[@]}"; do
  root="$(source_root "$service")"
  file="$(dockerfile "$service")"
  [[ -f "$root/$file" ]] || { printf 'Missing Dockerfile: %s/%s\n' "$root" "$file" >&2; exit 2; }
  revision="$(git -C "$root" rev-parse --short HEAD)"
  printf '%s | %s | %s | %s\n' "$service" "$root" "$revision" "$file"
done
if "$dry_run"; then exit 0; fi

environment_file="${REALITY_RAILWAY_ENV_FILE:-${repository_root}/.env}"
if [[ -z "${RAILWAY_TOKEN:-}" && -f "$environment_file" ]]; then
  RAILWAY_TOKEN="$(awk -F= '$1=="RAILWAY_TOKEN" {sub(/^[^=]*=/, ""); print; exit}' "$environment_file")"
  export RAILWAY_TOKEN
fi
# Railway also supports an existing CLI login when no project token is supplied.

: "${REALITY_RAILWAY_PROJECT_ID:?Set REALITY_RAILWAY_PROJECT_ID.}"
project_id="$REALITY_RAILWAY_PROJECT_ID"
environment="${REALITY_RAILWAY_ENVIRONMENT:-production}"
if [[ "$mode" != product ]]; then
  : "${SITE_URL:?Set SITE_URL to the marketing service domain.}"
  site_url="$SITE_URL"
fi
if [[ "$mode" != site ]]; then
  : "${APP_URL:?Set APP_URL to the app service domain.}"
  : "${DOCS_URL:?Set DOCS_URL to the docs service domain.}"
  : "${MCP_URL:?Set MCP_URL to the MCP service domain.}"
  app_url="$APP_URL"
  docs_url="$DOCS_URL"
  mcp_url="$MCP_URL"
fi

deploy_service() {
  local service="$1"
  local root
  root="$(source_root "$service")"
  railway up "$root" --path-as-root \
    --project "${project_id}" \
    --environment "${environment}" \
    --service "${service}" \
    --ci \
    --message "Deploy ${service} from $(git -C "$root" rev-parse --short HEAD)"
}

verify_background_service() {
  local service="$1"
  local attempt
  for attempt in {1..12}; do
    if railway logs \
      --project "${project_id}" \
      --environment "${environment}" \
      --service "${service}" \
      --lines 50 2>/dev/null | grep -q "event=\"${service}_sweep\""; then
      return 0
    fi
    sleep 5
  done
  printf 'No %s sweep heartbeat observed after deployment.\n' "${service}" >&2
  return 1
}

# Preserve explicit ordering; background readiness gates the next service.
for service in "${services[@]}"; do
  deploy_service "$service"
  case "$service" in scheduler|worker) verify_background_service "$service" ;; esac
done

if [[ "$mode" != product ]]; then
  curl --fail --silent --show-error "${site_url}/" >/dev/null
fi
if [[ "$mode" != site ]]; then
  curl --fail --silent --show-error "${docs_url}/" >/dev/null
  curl --fail --silent --show-error "${app_url}/healthz" >/dev/null
  curl --fail --silent --show-error "${mcp_url%/}/readyz" >/dev/null
fi
printf 'Railway %s deployment verified.\n' "$mode"
