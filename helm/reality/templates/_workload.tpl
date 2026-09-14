{{/*
Renders the pod spec shared by every workload in this chart. Called with a list:
  (list $root $name $component)

$component keys consumed here: image, port, command, args, env, envFrom,
resources, probes, securityContext, podSecurityContext, volumes, volumeMounts,
nodeSelector, tolerations, affinity, secrets (bool), terminationGracePeriodSeconds.

Component overrides use `default <root value> <component value>`, which treats
an EMPTY component value as "unset" and falls back to the root. A component can
therefore replace a root list or map but cannot CLEAR one — setting
`web.tolerations: []` keeps the root tolerations. To drop an inherited value for
one component, remove it from the root and set it on the other components
instead. This is Helm's `default` semantics, not a chart bug.
*/}}
{{- define "reality.podSpec" -}}
{{- $root := index . 0 -}}
{{- $name := index . 1 -}}
{{- $c := index . 2 -}}
{{/*
  A component may pin its own ServiceAccount. The migration Job does, because it
  runs as a PRE-INSTALL HOOK: Helm creates and waits on hooks BEFORE applying the
  ordinary release manifest, and the chart's ServiceAccount lives in that
  manifest. Referencing it from the hook made the Job unschedulable —
  `pods "reality-migrate-" is forbidden: serviceaccount "reality" not found` —
  so the hook never completed and Helm blocked forever without ever creating a
  single Deployment.
  `alembic upgrade head` talks only to Postgres, so it has no use for the IRSA
  role and the namespace `default` ServiceAccount is sufficient.
*/}}
serviceAccountName: {{ $c.serviceAccountName | default (include "reality.serviceAccountName" $root) }}
{{- with $root.Values.imagePullSecrets }}
imagePullSecrets:
  {{- toYaml . | nindent 2 }}
{{- end }}
securityContext:
  {{- toYaml (default $root.Values.podSecurityContext $c.podSecurityContext) | nindent 2 }}
{{- with (default $root.Values.terminationGracePeriodSeconds $c.terminationGracePeriodSeconds) }}
terminationGracePeriodSeconds: {{ . }}
{{- end }}
containers:
  - name: {{ $name }}
    image: {{ include "reality.image" (list $root $c) | quote }}
    imagePullPolicy: {{ $root.Values.image.pullPolicy }}
    securityContext:
      {{- toYaml (default $root.Values.securityContext $c.securityContext) | nindent 6 }}
    {{- with $c.command }}
    command:
      {{- toYaml . | nindent 6 }}
    {{- end }}
    {{- with $c.args }}
    args:
      {{- toYaml . | nindent 6 }}
    {{- end }}
    {{- if $c.port }}
    ports:
      - name: http
        containerPort: {{ $c.port }}
        protocol: TCP
    {{- end }}
    env:
      {{- if $c.secrets }}
      {{- include "reality.commonEnv" $root | nindent 6 }}
      {{- end }}
      {{- with $c.env }}
      {{- range $k, $v := . }}
      - name: {{ $k }}
        value: {{ $v | quote }}
      {{- end }}
      {{- end }}
    {{- if $c.secrets }}
    envFrom:
      - secretRef:
          name: {{ include "reality.secretName" $root }}
      {{- range $root.Values.secrets.extraSecretRefs }}
      - secretRef:
          name: {{ . }}
      {{- end }}
      {{- range $root.Values.secrets.extraConfigMapRefs }}
      - configMapRef:
          name: {{ . }}
      {{- end }}
    {{- end }}
    {{- with $c.probes }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
    resources:
      {{- toYaml (default $root.Values.resources $c.resources) | nindent 6 }}
    {{- with $c.volumeMounts }}
    volumeMounts:
      {{- toYaml . | nindent 6 }}
    {{- end }}
{{- with $c.volumes }}
volumes:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- with (default $root.Values.nodeSelector $c.nodeSelector) }}
nodeSelector:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- with (default $root.Values.tolerations $c.tolerations) }}
tolerations:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- with (default $root.Values.affinity $c.affinity) }}
affinity:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- end }}
