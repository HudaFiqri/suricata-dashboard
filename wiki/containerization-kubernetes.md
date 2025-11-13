# Kubernetes Deployment - Suricata Dashboard

Complete guide untuk deploy Suricata Dashboard di Kubernetes cluster (termasuk RKE2) dengan 4 deployment patterns berbeda.

## 📋 Daftar Isi
- [Overview](#overview)
- [Deployment Patterns](#deployment-patterns)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Pattern Selection Guide](#pattern-selection-guide)
- [Common Operations](#common-operations)
- [Security](#security)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Overview

### Tentang Kubernetes Deployment

Suricata Dashboard di Kubernetes memberikan:
- **High Availability**: Multiple replicas dengan self-healing
- **Scalability**: Horizontal dan vertical scaling
- **Orchestration**: Automated deployment, updates, rollback
- **Service Discovery**: Built-in networking dan load balancing
- **Resource Management**: Requests, limits, dan QoS
- **Declarative Configuration**: Infrastructure as Code

### Supported Platforms

- ✅ RKE2 (Rancher Kubernetes Engine 2)
- ✅ K3s
- ✅ Kubeadm
- ✅ EKS (Amazon)
- ✅ GKE (Google Cloud)
- ✅ AKS (Azure)
- ✅ Minikube / Kind (Development)

---

## Deployment Patterns

Kami menyediakan **4 patterns** berbeda sesuai dengan use case:

### Pattern 1: HostPath (Single/Dedicated Node)

**Use Case:** Suricata di host, dashboard mount logs via hostPath

```
┌─────────────────────────────┐
│  Node (suricata=enabled)    │
│  ├─ Suricata (host)         │
│  └─ Dashboard Pod           │
│     (hostPath mount)        │
└─────────────────────────────┘
```

**Characteristics:**
- ✅ Simple setup
- ✅ Direct filesystem access
- ✅ Low latency
- ⚠️ Pod tied to specific node
- ⚠️ Cannot scale horizontally

**Cocok untuk:**
- RKE2 single node
- Dedicated monitoring node
- Development/testing
- Simple production setup

**📖 [Full Documentation →](https://github.com/yourusername/suricata-dashboard/tree/main/container/kubernetes/patterns/hostpath)**

---

### Pattern 2: DaemonSet (Multi-Node Distributed)

**Use Case:** Suricata di multiple nodes, dashboard per node

```
┌──────────┐ ┌──────────┐ ┌──────────┐
│  Node 1  │ │  Node 2  │ │  Node 3  │
│ Suricata │ │ Suricata │ │ Suricata │
│ Dashboard│ │ Dashboard│ │ Dashboard│
└──────────┘ └──────────┘ └──────────┘
```

**Characteristics:**
- ✅ Distributed monitoring
- ✅ Auto-scaling dengan nodes
- ✅ High availability
- ⚠️ Independent dashboards
- ⚠️ Needs aggregation layer (optional)

**Cocok untuk:**
- Multi-node RKE2 cluster
- Edge monitoring
- Per-node traffic analysis
- Multi-tenant setup

**📖 [Full Documentation →](https://github.com/yourusername/suricata-dashboard/tree/main/container/kubernetes/patterns/daemonset)**

---

### Pattern 3: NFS (Shared Storage)

**Use Case:** Centralized logs via NFS, scalable dashboard

```
        ┌─────────────┐
        │ NFS Server  │
        │  (Logs)     │
        └──────┬──────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼──┐   ┌───▼──┐   ┌───▼──┐
│Dash 1│   │Dash 2│   │Dash 3│
└──────┘   └──────┘   └──────┘
```

**Characteristics:**
- ✅ Horizontal scaling
- ✅ Load balancing
- ✅ Not tied to specific nodes
- ⚠️ Requires NFS setup
- ⚠️ Network latency consideration

**Cocok untuk:**
- Production with HA
- Centralized logging
- Cloud deployment
- Need horizontal scaling

**📖 [Full Documentation →](https://github.com/yourusername/suricata-dashboard/tree/main/container/kubernetes/patterns/nfs)**

---

### Pattern 4: Sidecar (Fully Containerized)

**Use Case:** Suricata + Dashboard dalam 1 pod

```
┌────────────────────────────┐
│  Pod                       │
│  ┌──────────┐ ┌─────────┐ │
│  │ Suricata │ │Dashboard│ │
│  └────┬─────┘ └────┬────┘ │
│       └── shared ──┘      │
│         volume            │
└────────────────────────────┘
```

**Characteristics:**
- ✅ Fully containerized
- ✅ Portable anywhere
- ✅ Easy deployment
- ⚠️ Needs privileges
- ⚠️ Host network mode

**Cocok untuk:**
- POC/Demo
- Cloud-native deployment
- No host Suricata dependency
- Development/testing

**📖 [Full Documentation →](https://github.com/yourusername/suricata-dashboard/tree/main/container/kubernetes/patterns/sidecar)**

---

## Prerequisites

### Cluster Requirements

```bash
# Check Kubernetes version (1.24+)
kubectl version --short

# Check nodes
kubectl get nodes

# Check storage classes
kubectl get storageclass
```

### Required Tools

```bash
# kubectl
kubectl version

# kustomize (optional but recommended)
kubectl kustomize --help

# helm (optional)
helm version
```

### Container Registry

```bash
# Build and push image
docker build -f container/docker/Dockerfile -t registry.example.com/suricata-dashboard:latest .
docker push registry.example.com/suricata-dashboard:latest
```

---

## Quick Start

### Step 1: Choose Pattern

Pilih pattern based on use case (lihat [Pattern Selection Guide](#pattern-selection-guide))

### Step 2: Prepare Cluster

```bash
# For hostpath/daemonset: Label nodes
kubectl label nodes <node-name> suricata=enabled

# For NFS: Setup NFS server (see pattern docs)

# For sidecar: Enable privileged pods
kubectl label namespace suricata-monitoring \
  pod-security.kubernetes.io/enforce=privileged
```

### Step 3: Create Secret

```bash
kubectl create secret generic dashboard-secrets \
  --from-literal=DB_PASSWORD='your-secure-password' \
  --namespace=suricata-monitoring
```

### Step 4: Deploy

```bash
cd container/kubernetes/patterns/<pattern-name>/

# Edit configuration files
# - Update image registry
# - Update NFS server (if using NFS)
# - Update ingress hostname

# Deploy
kubectl apply -k .
```

### Step 5: Verify

```bash
# Check pods
kubectl get pods -n suricata-monitoring -o wide

# Check services
kubectl get svc,ingress -n suricata-monitoring

# Check logs
kubectl logs -n suricata-monitoring -l app=suricata-dashboard -f
```

### Step 6: Access

```bash
# Port-forward (quick access)
kubectl port-forward -n suricata-monitoring svc/dashboard-service 5000:5000

# Or via ingress
curl http://suricata-dashboard.local
```

---

## Pattern Selection Guide

### Decision Tree

```
Q: Is Suricata already running on host OS?
├─ YES
│  ├─ Q: Single node or multiple nodes?
│  │  ├─ Single/Dedicated → Pattern 1: HostPath
│  │  └─ Multiple nodes → Pattern 2: DaemonSet
│  └─ Q: Do you have NFS/shared storage?
│     └─ Yes → Pattern 3: NFS
└─ NO (want fully containerized)
   └─ Pattern 4: Sidecar
```

### Comparison Table

| Criteria | HostPath | DaemonSet | NFS | Sidecar |
|----------|----------|-----------|-----|---------|
| **Complexity** | ⭐ Simple | ⭐⭐ Medium | ⭐⭐⭐ Advanced | ⭐⭐⭐ Advanced |
| **Scalability** | ❌ No | ⚠️ Per-node | ✅ Yes | ⚠️ Limited |
| **HA** | ❌ No | ✅ Yes | ✅ Yes | ⚠️ Per-pod |
| **Setup Time** | Fast | Fast | Slow (NFS) | Fast |
| **Dependencies** | Suricata host | Suricata host | NFS server | None |
| **Best For** | Single node | Multi-node | Production | POC/Demo |

### Recommendations by Scenario

#### RKE2 Single Node
**→ Pattern 1: HostPath**
- Simplest setup
- Direct access to host Suricata
- No networking overhead

#### RKE2 Multi-Node Cluster
**→ Pattern 2: DaemonSet**
- Distributed monitoring
- Per-node dashboard
- High availability

#### Production with HA Requirements
**→ Pattern 3: NFS**
- Horizontal scaling
- Centralized data
- Load balancing

#### Cloud-Native / Containerized
**→ Pattern 4: Sidecar**
- No host dependencies
- Portable deployment
- Full isolation

---

## Common Operations

### Scaling

#### Horizontal Scaling (NFS/Sidecar only)

```bash
# Scale manually
kubectl scale deployment suricata-dashboard --replicas=3 -n suricata-monitoring

# Auto-scaling (HPA)
kubectl autoscale deployment suricata-dashboard \
  --min=2 --max=10 --cpu-percent=70 \
  -n suricata-monitoring
```

#### Vertical Scaling (All patterns)

```bash
# Edit resource limits
kubectl edit deployment suricata-dashboard -n suricata-monitoring

# Update:
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Updates & Rollouts

```bash
# Update image
kubectl set image deployment/suricata-dashboard \
  dashboard=registry.example.com/suricata-dashboard:v1.1.0 \
  -n suricata-monitoring

# Check rollout status
kubectl rollout status deployment/suricata-dashboard -n suricata-monitoring

# Rollback
kubectl rollout undo deployment/suricata-dashboard -n suricata-monitoring

# Rollout history
kubectl rollout history deployment/suricata-dashboard -n suricata-monitoring
```

### Configuration Updates

```bash
# Edit ConfigMap
kubectl edit configmap dashboard-config -n suricata-monitoring

# Restart pods to apply changes
kubectl rollout restart deployment/suricata-dashboard -n suricata-monitoring
```

### Database Operations

```bash
# Backup
kubectl exec -n suricata-monitoring postgres-0 -- \
  pg_dump -U suricata suricata | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore
gunzip -c backup.sql.gz | \
  kubectl exec -i -n suricata-monitoring postgres-0 -- \
  psql -U suricata suricata

# Access database
kubectl exec -n suricata-monitoring -it postgres-0 -- psql -U suricata
```

---

## Security

### Pod Security Standards

```bash
# Label namespace for privileged pods (sidecar pattern)
kubectl label namespace suricata-monitoring \
  pod-security.kubernetes.io/enforce=privileged \
  pod-security.kubernetes.io/audit=privileged \
  pod-security.kubernetes.io/warn=privileged
```

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: dashboard-netpol
  namespace: suricata-monitoring
spec:
  podSelector:
    matchLabels:
      app: suricata-dashboard
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
      port: 5000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

Apply:
```bash
kubectl apply -f networkpolicy.yaml
```

### RBAC

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dashboard-sa
  namespace: suricata-monitoring
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: dashboard-role
  namespace: suricata-monitoring
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dashboard-rolebinding
  namespace: suricata-monitoring
subjects:
- kind: ServiceAccount
  name: dashboard-sa
roleRef:
  kind: Role
  name: dashboard-role
  apiGroup: rbac.authorization.k8s.io
```

### Secrets Management

#### Sealed Secrets (Recommended)

```bash
# Install sealed-secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Create sealed secret
kubectl create secret generic dashboard-secrets \
  --from-literal=DB_PASSWORD='prodpassword' \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > sealed-secret.yaml

kubectl apply -f sealed-secret.yaml
```

#### External Secrets Operator

```bash
# Use with Vault, AWS Secrets Manager, etc.
# See: https://external-secrets.io/
```

### TLS/HTTPS

```bash
# Using cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Update Ingress with TLS
# See pattern-specific docs
```

---

## Monitoring

### Logs

```bash
# Stream logs
kubectl logs -f deployment/suricata-dashboard -n suricata-monitoring

# Multi-pod logs with stern
stern -n suricata-monitoring suricata-dashboard

# Previous logs
kubectl logs deployment/suricata-dashboard -n suricata-monitoring --previous
```

### Metrics

```bash
# Resource usage
kubectl top pods -n suricata-monitoring
kubectl top nodes

# Detailed pod metrics
kubectl top pod -n suricata-monitoring --containers
```

### Prometheus Integration

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: dashboard-metrics
  namespace: suricata-monitoring
spec:
  selector:
    matchLabels:
      app: suricata-dashboard
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

### Grafana Dashboards

Import dashboard untuk monitoring:
- Kubernetes pod metrics
- Application metrics
- Database performance
- Network traffic

---

## Troubleshooting

### Common Issues

#### Pods Not Starting

```bash
# Check events
kubectl get events -n suricata-monitoring --sort-by='.lastTimestamp'

# Describe pod
kubectl describe pod <pod-name> -n suricata-monitoring

# Check logs
kubectl logs <pod-name> -n suricata-monitoring
```

#### ImagePullBackOff

```bash
# Check image exists
docker pull registry.example.com/suricata-dashboard:latest

# Create imagePullSecret
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=pass \
  --namespace=suricata-monitoring

# Add to deployment
# imagePullSecrets:
# - name: regcred
```

#### CrashLoopBackOff

```bash
# Check previous logs
kubectl logs <pod-name> -n suricata-monitoring --previous

# Common causes:
# - Database not ready
# - Configuration error
# - Missing dependencies
```

#### Service Not Accessible

```bash
# Check service
kubectl get svc -n suricata-monitoring
kubectl describe svc dashboard-service -n suricata-monitoring

# Check endpoints
kubectl get endpoints -n suricata-monitoring

# Test from inside cluster
kubectl run -it --rm debug --image=nicolaka/netshoot -- \
  curl http://dashboard-service.suricata-monitoring.svc.cluster.local:5000/api/status
```

#### Permission Errors (Sidecar)

```bash
# Check PSS labels
kubectl get ns suricata-monitoring -o yaml | grep pod-security

# Add labels
kubectl label namespace suricata-monitoring \
  pod-security.kubernetes.io/enforce=privileged \
  --overwrite
```

#### NFS Mount Issues

```bash
# Test NFS from node
ssh <node-ip>
showmount -e nfs-server.example.com
mount -t nfs nfs-server.example.com:/export /mnt

# Check NFS client tools
# Ubuntu/Debian: apt-get install nfs-common
# RHEL/CentOS: yum install nfs-utils
```

### Debug Tools

```bash
# Deploy debug pod
kubectl run -it --rm debug --image=nicolaka/netshoot -- bash

# Inside debug pod:
# - Test DNS: nslookup dashboard-service.suricata-monitoring
# - Test connectivity: curl http://dashboard-service:5000
# - Check network: ip addr, ip route
```

---

## Best Practices

### Production Deployment

- [ ] Use private container registry
- [ ] Implement proper secret management
- [ ] Configure resource requests and limits
- [ ] Enable monitoring (Prometheus/Grafana)
- [ ] Setup log aggregation (Loki/ELK)
- [ ] Configure NetworkPolicy
- [ ] Enable RBAC
- [ ] Use TLS/HTTPS (cert-manager)
- [ ] Implement backup strategy
- [ ] Setup alerting
- [ ] Document runbooks
- [ ] Test disaster recovery

### RKE2 Specific

```bash
# Use local-path storage class (default in RKE2)
storageClassName: local-path

# Use nginx ingress (built-in RKE2)
kubernetes.io/ingress.class: nginx

# Check RKE2 services
kubectl get pods -n kube-system | grep -E "rke2|nginx"
```

### High Availability

```yaml
# Anti-affinity for dashboard pods
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - suricata-dashboard
        topologyKey: kubernetes.io/hostname

# PostgreSQL replication (optional)
# Use PostgreSQL operator or cloud managed DB
```

### Resource Optimization

```yaml
# Dashboard resources
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"

# PostgreSQL resources
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Backup Strategy

```bash
# Automated backup script
#!/bin/bash
kubectl exec -n suricata-monitoring postgres-0 -- \
  pg_dump -U suricata suricata | \
  gzip > /backups/dashboard_$(date +%Y%m%d_%H%M%S).sql.gz

# Retain last 7 days
find /backups -name "dashboard_*.sql.gz" -mtime +7 -delete
```

Run via CronJob:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: suricata-monitoring
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15-alpine
            command:
            - /bin/sh
            - -c
            - pg_dump -h postgres-service -U suricata suricata | gzip > /backup/db_$(date +%Y%m%d).sql.gz
            volumeMounts:
            - name: backup
              mountPath: /backup
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: dashboard-secrets
                  key: DB_PASSWORD
          volumes:
          - name: backup
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

---

## Resources

### Official Documentation
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [RKE2 Documentation](https://docs.rke2.io/)
- [Kustomize](https://kustomize.io/)
- [Kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)

### Pattern Documentation
- [Pattern 1: HostPath](https://github.com/yourusername/suricata-dashboard/tree/main/container/kubernetes/patterns/hostpath)
- [Pattern 2: DaemonSet](https://github.com/yourusername/suricata-dashboard/tree/main/container/kubernetes/patterns/daemonset)
- [Pattern 3: NFS](https://github.com/yourusername/suricata-dashboard/tree/main/container/kubernetes/patterns/nfs)
- [Pattern 4: Sidecar](https://github.com/yourusername/suricata-dashboard/tree/main/container/kubernetes/patterns/sidecar)

### Related Wikis
- [Main Containerization Wiki](containerization.md)
- [Docker Deployment Wiki](containerization-docker.md)

---

## Changelog

- **2024-12**: Initial Kubernetes deployment documentation
- Added 4 deployment patterns
- RKE2-specific instructions
- Security best practices
- Split from main containerization wiki

---

**Last Updated:** 2024-12
**Maintainer:** Suricata Dashboard Team

**See Also:**
- [Docker Deployment](containerization-docker.md)
- [Main Containerization Overview](containerization.md)
