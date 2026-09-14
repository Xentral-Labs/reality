#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
environment_file="${REALITY_RAILWAY_ENV_FILE:-${repository_root}/.env}"

if [[ -z "${RAILWAY_TOKEN:-}" && -f "${environment_file}" ]]; then
  RAILWAY_TOKEN="$(awk -F= '$1=="RAILWAY_TOKEN" {sub(/^[^=]*=/, ""); print; exit}' "${environment_file}")"
  export RAILWAY_TOKEN
fi

: "${RAILWAY_TOKEN:?Set RAILWAY_TOKEN or add it to the ignored .env file.}"

: "${REALITY_RAILWAY_PROJECT_ID:?Set REALITY_RAILWAY_PROJECT_ID to your Railway project id.}"
project_id="${REALITY_RAILWAY_PROJECT_ID}"
environment="${REALITY_RAILWAY_ENVIRONMENT:-production}"
: "${APP_URL:?Set APP_URL to the generated Railway domain for the app service.}"
app_url="${APP_URL}"
: "${DOCS_URL:?Set DOCS_URL to the generated Railway domain for the docs service.}"
docs_url="${DOCS_URL}"
: "${MCP_URL:?Set MCP_URL to the generated Railway domain for the mcp service (trailing slash).}"
mcp_url="${MCP_URL}"

deploy_service() {
  local service="$1"
  railway up \
    --project "${project_id}" \
    --environment "${environment}" \
    --service "${service}" \
    --ci \
    --message "Deploy ${service} from $(git rev-parse --short HEAD)"
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

# API first and App last is intentional: App Nginx resolves the API's private
# address when it starts. Static surfaces and MCP can deploy between them.
deploy_service api
deploy_service scheduler
verify_background_service scheduler
deploy_service worker
verify_background_service worker
deploy_service mcp
deploy_service docs
deploy_service app

curl --fail --silent --show-error "${docs_url}/" >/dev/null
curl --fail --silent --show-error "${app_url}/healthz" >/dev/null
curl --fail --silent --show-error "${mcp_url%/}/readyz" >/dev/null

printf 'Railway demo deployment verified.\n'
printf 'Docs: %s\nApp: %s\nMCP: %s\n' \
  "${docs_url}" "${app_url}" "${mcp_url}"
