{{/*
Expand the name of the chart.
*/}}
{{- define "guardstack.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "guardstack.fullname" -}}
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

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "guardstack.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "guardstack.labels" -}}
helm.sh/chart: {{ include "guardstack.chart" . }}
{{ include "guardstack.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: guardstack
{{- end }}

{{/*
Selector labels
*/}}
{{- define "guardstack.selectorLabels" -}}
app.kubernetes.io/name: {{ include "guardstack.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "guardstack.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "guardstack.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create PostgreSQL connection string
*/}}
{{- define "guardstack.postgresql.connectionString" -}}
{{- if .Values.postgresql.enabled }}
postgresql://{{ .Values.postgresql.auth.username }}:$(POSTGRES_PASSWORD)@{{ include "guardstack.fullname" . }}-postgresql:5432/{{ .Values.postgresql.auth.database }}?sslmode=prefer
{{- else }}
{{- .Values.externalDatabase.connectionString }}
{{- end }}
{{- end }}

{{/*
Create Redis connection string
*/}}
{{- define "guardstack.redis.connectionString" -}}
{{- if .Values.redis.enabled }}
redis://:$(REDIS_PASSWORD)@{{ include "guardstack.fullname" . }}-redis-master:6379/0
{{- else }}
{{- .Values.externalRedis.connectionString }}
{{- end }}
{{- end }}

{{/*
Create MinIO endpoint
*/}}
{{- define "guardstack.minio.endpoint" -}}
{{- if .Values.minio.enabled }}
http://{{ include "guardstack.fullname" . }}-minio:9000
{{- else }}
{{- .Values.externalS3.endpoint }}
{{- end }}
{{- end }}

{{/*
Worker labels
*/}}
{{- define "guardstack.worker.labels" -}}
{{ include "guardstack.labels" . }}
app.kubernetes.io/component: worker
{{- end }}

{{/*
Worker selector labels
*/}}
{{- define "guardstack.worker.selectorLabels" -}}
{{ include "guardstack.selectorLabels" . }}
app.kubernetes.io/component: worker
{{- end }}

{{/*
API labels
*/}}
{{- define "guardstack.api.labels" -}}
{{ include "guardstack.labels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
API selector labels
*/}}
{{- define "guardstack.api.selectorLabels" -}}
{{ include "guardstack.selectorLabels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
Return the proper image name
*/}}
{{- define "guardstack.image" -}}
{{- $registryName := .Values.image.registry | default "" }}
{{- $repositoryName := .Values.image.repository }}
{{- $tag := .Values.image.tag | default .Chart.AppVersion }}
{{- if $registryName }}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag }}
{{- else }}
{{- printf "%s:%s" $repositoryName $tag }}
{{- end }}
{{- end }}
