{{/*
Chart name.
*/}}
{{- define "reality.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Fully qualified release name, truncated to the 63-char DNS label limit.
*/}}
{{- define "reality.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "reality.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "reality.labels" -}}
helm.sh/chart: {{ include "reality.chart" . }}
{{ include "reality.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "reality.selectorLabels" -}}
app.kubernetes.io/name: {{ include "reality.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "reality.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "reality.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Name of the Kubernetes Secret every Python workload loads its secrets from.
Either materialised by the ExternalSecret this chart renders, or created
out-of-band when externalSecret.enabled=false.
*/}}
{{- define "reality.secretName" -}}
{{- default (printf "%s-secrets" (include "reality.fullname" .)) .Values.secrets.existingSecret }}
{{- end }}

{{/*
Image reference for a component. Components share one ECR repository and are
distinguished by a tag prefix, because the target account provisions a single
`runreality` repo. Tags are IMMUTABLE in that repo, so a tag is never reused.
*/}}
{{- define "reality.image" -}}
{{- $root := index . 0 -}}
{{- $component := index . 1 -}}
{{- $repository := required "image.repository must be set to the registry holding the Reality images (the chart composes <repository>:<component>-<tag>, one repository with component-prefixed tags)" ($component.image.repository | default $root.Values.image.repository) -}}
{{- $tag := $component.image.tag | default $root.Values.image.tag | default $root.Chart.AppVersion -}}
{{- if $component.image.tagPrefix -}}
{{- printf "%s:%s%s" $repository $component.image.tagPrefix $tag -}}
{{- else -}}
{{- printf "%s:%s" $repository $tag -}}
{{- end -}}
{{- end }}

{{/*
In-cluster DNS name of a component's Service, fully qualified but WITHOUT a
trailing dot.

The web image resolves this through nginx's own `resolver` directive rather than
through libc, so there is no ndots search-path expansion and a short Service
name would not resolve. A trailing dot does not work either — nginx rejects the
reply with "unexpected DNS response" and serves 502 (verified). The bare
<svc>.<ns>.svc.cluster.local form is the one that works.
*/}}
{{- define "reality.componentHost" -}}
{{- $root := index . 0 -}}
{{- $name := index . 1 -}}
{{- printf "%s-%s.%s.svc.cluster.local" (include "reality.fullname" $root) $name $root.Release.Namespace -}}
{{- end }}

{{/*
Non-secret environment shared by every Python workload (api, mcp, worker,
migrate). Secret material never appears here — it arrives via envFrom on the
Vault-backed Secret.

Deliberate choices:
  * REALITY_ENV=production arms the guard that makes REALITY_MASTER_KEY
    mandatory instead of silently generating a per-pod ephemeral Fernet key.
  * REALITY_DB_POOL_* are the ONLY pool names Python reads. The
    REALITY_BACKEND_DB_* / REALITY_MCP_DB_* names in .env.example are Compose
    indirection and are ignored by the application.
  * AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY are deliberately absent. boto3 is
    constructed with no explicit credentials, so the default chain resolves the
    IRSA role; setting env credentials would shadow it.
  * REALITY_S3_ENDPOINT_URL is deliberately absent so botocore resolves the real
    AWS S3 endpoint (the code maps an empty value to None).
*/}}
{{- define "reality.commonEnv" -}}
- name: REALITY_ENV
  value: "production"
{{/*
  service.version. Wired to the image tag so a metric or span identifies the
  build that produced it -- the same tag CI bumps in the Argo Application.
*/}}
- name: REALITY_IMAGE_TAG
  value: {{ .Values.image.tag | default .Chart.AppVersion | quote }}
{{- if and .Values.telemetry.enabled .Values.telemetry.endpoint }}
{{/*
  The presence of OTEL_EXPORTER_OTLP_ENDPOINT is the single switch the
  application keys off: unset means no providers, no instrumentation, no cost.
*/}}
- name: OTEL_EXPORTER_OTLP_ENDPOINT
  value: {{ .Values.telemetry.endpoint | quote }}
- name: OTEL_METRIC_EXPORT_INTERVAL
  value: {{ .Values.telemetry.metricExportIntervalMs | quote }}
{{/*
  Short export timeouts. The default is 10s per attempt with retries, so a
  wrong endpoint or a collector that blackholes SYNs adds ~30s of retry noise
  to every pod shutdown and floods the logs with exporter errors.
*/}}
- name: OTEL_METRIC_EXPORT_TIMEOUT
  value: "3000"
- name: OTEL_BSP_EXPORT_TIMEOUT
  value: "3000"
{{/*
  service.instance.id / k8s.node.name. Set explicitly: left to itself the SDK
  invents a random UUID per process, so every restart on spot capacity would
  mint a whole new set of series. The node name lets a latency spike be
  correlated with a spot reclaim.
*/}}
- name: REALITY_POD_NAME
  valueFrom:
    fieldRef:
      fieldPath: metadata.name
- name: REALITY_NODE_NAME
  valueFrom:
    fieldRef:
      fieldPath: spec.nodeName
{{- end }}
{{/*
  REALITY_SETTINGS_KEY is NOT an alias of REALITY_MASTER_KEY in both directions.
  security/secrets.py accepts it as a fallback FOR the master key, but
  agent/settings.py:_fernet() reads ONLY this name — and when it is unset it
  generates a Fernet key at $REALITY_ROOT/.reality-secret.key, which is per-pod
  and ephemeral. With more than one api replica each pod gets a DIFFERENT key,
  so a tenant-configured provider API key encrypted by one replica cannot be
  decrypted by the other, and a restart loses it outright.

  Mapped from the master key's own Secret entry rather than stored twice in
  Vault: the two are interchangeable Fernet keys, and sourcing one value under
  two env names makes them impossible to drift apart.
*/}}
- name: REALITY_SETTINGS_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "reality.secretName" . }}
      key: REALITY_MASTER_KEY
- name: REALITY_DB_POOL_SIZE
  value: {{ .Values.database.poolSize | quote }}
- name: REALITY_DB_MAX_OVERFLOW
  value: {{ .Values.database.maxOverflow | quote }}
- name: REALITY_DB_POOL_TIMEOUT
  value: {{ .Values.database.poolTimeout | quote }}
- name: REALITY_ARTIFACT_STORAGE
  value: {{ .Values.storage.backend | quote }}
{{- if eq .Values.storage.backend "s3" }}
- name: REALITY_S3_BUCKET
  value: {{ .Values.storage.bucket | quote }}
- name: REALITY_S3_REGION
  value: {{ .Values.storage.region | quote }}
{{- end }}
- name: REALITY_ARTIFACT_DIR
  value: {{ .Values.storage.scratchDir | quote }}
- name: APP_URL
  value: {{ .Values.urls.app | quote }}
- name: API_URL
  value: {{ .Values.urls.api | default .Values.urls.app | quote }}
- name: SITE_URL
  value: {{ .Values.urls.site | quote }}
- name: DOCS_URL
  value: {{ .Values.urls.docs | quote }}
- name: MCP_URL
  value: {{ .Values.urls.mcp | quote }}
- name: REALITY_AUTH_MODE
  value: {{ .Values.auth.mode | quote }}
- name: REALITY_COOKIE_SECURE
  value: {{ .Values.auth.cookieSecure | quote }}
- name: REALITY_AUTH_EXPOSE_CODES
  value: {{ .Values.auth.exposeCodes | quote }}
- name: REALITY_BOOTSTRAP_TENANT_NAME
  value: {{ .Values.bootstrap.tenantName | quote }}
- name: REALITY_EMAIL_PROVIDER
  value: {{ .Values.email.provider | quote }}
- name: REALITY_EMAIL_FROM
  value: {{ .Values.email.from | quote }}
- name: REALITY_ACCESS_NOTIFICATION_EMAIL
  value: {{ .Values.email.accessNotification | quote }}
- name: REALITY_AUTO_APPROVE_LIMIT
  value: {{ .Values.auth.autoApproveLimit | quote }}
{{- if eq .Values.email.provider "smtp" }}
- name: REALITY_SMTP_HOST
  value: {{ .Values.email.smtp.host | quote }}
- name: REALITY_SMTP_PORT
  value: {{ .Values.email.smtp.port | quote }}
- name: REALITY_SMTP_TLS
  value: {{ .Values.email.smtp.tls | quote }}
{{- end }}
{{- with .Values.extraEnv }}
{{- range $k, $v := . }}
- name: {{ $k }}
  value: {{ $v | quote }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Checksum over everything that can change the SET OF KEYS in the Vault-backed
Secret. Pods load it with envFrom, which is evaluated only at pod start, so a
Secret that gains a key does NOT reach running pods. Hashing just
.Values.externalSecret was not enough: the copilot / email / platformAdmin
toggles append keys inside templates/externalsecret.yaml, so flipping one
changed the Secret while leaving the pod template byte-identical — the release
reported "deployed" and the new key never appeared in the containers.
*/}}
{{- define "reality.secretChecksum" -}}
{{- $parts := list (toYaml .Values.externalSecret) (toYaml .Values.copilot) (toYaml .Values.email.provider) (toYaml .Values.bootstrap.platformAdmin) (toYaml .Values.secrets) -}}
{{- join "|" $parts | sha256sum -}}
{{- end }}
