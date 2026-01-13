# Deployment Guide

This guide covers deploying GuardStack to production environments using Kubernetes and Helm.

## Prerequisites

Before deploying GuardStack, ensure you have:

- **Kubernetes cluster**: v1.28 or later
- **Helm**: v3.12 or later
- **kubectl**: Configured with cluster access
- **Storage class**: For persistent volumes
- **Ingress controller**: NGINX or Traefik recommended
- **cert-manager**: For TLS certificate management

## Deployment Options

### Option 1: Helm Chart (Recommended)

#### Add the Helm Repository

```bash
helm repo add guardstack https://charts.guardstack.io
helm repo update
```

#### Create Namespace

```bash
kubectl create namespace guardstack
```

#### Create Secrets

```bash
# Database credentials
kubectl create secret generic guardstack-db-credentials \
  --namespace guardstack \
  --from-literal=username=guardstack \
  --from-literal=password=<secure-password>

# Redis credentials
kubectl create secret generic guardstack-redis-credentials \
  --namespace guardstack \
  --from-literal=password=<redis-password>

# API keys for LLM providers
kubectl create secret generic guardstack-api-keys \
  --namespace guardstack \
  --from-literal=openai-api-key=<your-key> \
  --from-literal=anthropic-api-key=<your-key>
```

#### Create Values File

```yaml
# values-production.yaml
global:
  environment: production

replicaCount: 3
workerReplicaCount: 5

image:
  repository: ghcr.io/guardstack/guardstack
  tag: "1.0.0"
  pullPolicy: IfNotPresent

resources:
  api:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 2000m
      memory: 4Gi
  worker:
    requests:
      cpu: 1000m
      memory: 2Gi
    limits:
      cpu: 4000m
      memory: 8Gi

postgresql:
  enabled: true
  auth:
    existingSecret: guardstack-db-credentials
    secretKeys:
      userPasswordKey: password
  primary:
    persistence:
      size: 100Gi
    resources:
      requests:
        cpu: 500m
        memory: 1Gi

redis:
  enabled: true
  auth:
    existingSecret: guardstack-redis-credentials
  master:
    persistence:
      size: 10Gi

minio:
  enabled: true
  mode: distributed
  replicas: 4
  persistence:
    size: 100Gi

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
  hosts:
    - host: guardstack.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: guardstack-tls
      hosts:
        - guardstack.yourdomain.com

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

argoWorkflows:
  enabled: true
  controller:
    replicas: 2
```

#### Install the Chart

```bash
helm install guardstack guardstack/guardstack \
  --namespace guardstack \
  --values values-production.yaml \
  --wait
```

#### Verify Deployment

```bash
# Check pods
kubectl get pods -n guardstack

# Check services
kubectl get svc -n guardstack

# Check ingress
kubectl get ingress -n guardstack

# View logs
kubectl logs -l app.kubernetes.io/name=guardstack -n guardstack
```

### Option 2: Docker Compose (Development/Testing)

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    image: ghcr.io/guardstack/guardstack:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://guardstack:password@postgres:5432/guardstack
      - REDIS_URL=redis://redis:6379
      - MINIO_ENDPOINT=minio:9000
    depends_on:
      - postgres
      - redis
      - minio

  worker:
    image: ghcr.io/guardstack/guardstack:latest
    command: celery -A guardstack.worker worker -l info
    environment:
      - DATABASE_URL=postgresql://guardstack:password@postgres:5432/guardstack
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_USER=guardstack
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=guardstack
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=minio
      - MINIO_ROOT_PASSWORD=minio123
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"

volumes:
  postgres_data:
  minio_data:
```

```bash
docker-compose up -d
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `MINIO_ENDPOINT` | MinIO/S3 endpoint | Required |
| `MINIO_ACCESS_KEY` | MinIO access key | Required |
| `MINIO_SECRET_KEY` | MinIO secret key | Required |
| `SECRET_KEY` | Application secret key | Required |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `WORKERS` | Number of uvicorn workers | `4` |

### Database Setup

#### Run Migrations

```bash
# Via kubectl exec
kubectl exec -it deployment/guardstack-api -n guardstack -- \
  alembic upgrade head

# Or via Helm hook (automatic)
# Migrations run automatically on install/upgrade
```

#### Enable pgvector Extension

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Storage Configuration

#### MinIO Bucket Setup

```bash
# Create required buckets
mc alias set guardstack http://minio:9000 minio minio123
mc mb guardstack/models
mc mb guardstack/evaluations
mc mb guardstack/reports
```

### TLS Configuration

#### Using cert-manager

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
```

## High Availability

### Database HA

```yaml
# values-ha.yaml
postgresql:
  architecture: replication
  readReplicas:
    replicaCount: 2
```

### Redis HA

```yaml
redis:
  architecture: replication
  replica:
    replicaCount: 2
  sentinel:
    enabled: true
```

### API HA

```yaml
replicaCount: 3

affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              app.kubernetes.io/name: guardstack
          topologyKey: kubernetes.io/hostname

podDisruptionBudget:
  enabled: true
  minAvailable: 2
```

## Monitoring

### Prometheus Integration

```yaml
serviceMonitor:
  enabled: true
  interval: 30s
  scrapeTimeout: 10s

metrics:
  enabled: true
  port: 9090
```

### Grafana Dashboards

Import the provided dashboards:

```bash
kubectl apply -f https://raw.githubusercontent.com/guardstack/guardstack/main/deploy/grafana/dashboards.yaml
```

### Alerting Rules

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: guardstack-alerts
  namespace: guardstack
spec:
  groups:
    - name: guardstack
      rules:
        - alert: GuardStackHighErrorRate
          expr: |
            rate(http_requests_total{status=~"5.*",app="guardstack"}[5m]) > 0.1
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: High error rate in GuardStack
```

## Backup and Recovery

### Database Backup

```bash
# Create backup CronJob
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: guardstack-db-backup
  namespace: guardstack
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: postgres:16
              command:
                - /bin/sh
                - -c
                - |
                  pg_dump -h postgresql -U guardstack guardstack | \
                  gzip > /backup/guardstack-$(date +%Y%m%d).sql.gz
              volumeMounts:
                - name: backup
                  mountPath: /backup
          volumes:
            - name: backup
              persistentVolumeClaim:
                claimName: guardstack-backup-pvc
          restartPolicy: OnFailure
EOF
```

### MinIO Backup

```bash
# Sync to external S3
mc mirror guardstack/models s3/guardstack-backup/models
mc mirror guardstack/evaluations s3/guardstack-backup/evaluations
```

## Troubleshooting

### Common Issues

#### Pod Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n guardstack

# Check logs
kubectl logs <pod-name> -n guardstack --previous
```

#### Database Connection Issues

```bash
# Test connection
kubectl run -it --rm debug --image=postgres:16 -n guardstack -- \
  psql -h postgresql -U guardstack -d guardstack
```

#### Permission Issues

```bash
# Check RBAC
kubectl auth can-i --list --namespace guardstack

# Check service account
kubectl get serviceaccount -n guardstack
```

### Useful Commands

```bash
# Restart deployment
kubectl rollout restart deployment guardstack-api -n guardstack

# Scale manually
kubectl scale deployment guardstack-api --replicas=5 -n guardstack

# View resource usage
kubectl top pods -n guardstack

# Port forward for debugging
kubectl port-forward svc/guardstack-api 8000:8000 -n guardstack
```

## Upgrades

### Helm Upgrade

```bash
# Update values
helm upgrade guardstack guardstack/guardstack \
  --namespace guardstack \
  --values values-production.yaml \
  --wait

# Rollback if needed
helm rollback guardstack -n guardstack
```

### Database Migrations

```bash
# Migrations run automatically, but can be done manually:
kubectl exec -it deployment/guardstack-api -n guardstack -- \
  alembic upgrade head
```

## Security Hardening

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: guardstack-network-policy
  namespace: guardstack
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: guardstack
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8000
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: guardstack
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
      ports:
        - protocol: TCP
          port: 443
```

### Pod Security

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000

containerSecurityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL
```
