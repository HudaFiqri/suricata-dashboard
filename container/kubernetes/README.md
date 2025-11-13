# Suricata Dashboard - Kubernetes Deployment

Comprehensive Kubernetes deployment configurations untuk Suricata Dashboard dengan multiple deployment patterns.

## 📋 Overview

Repository ini menyediakan **4 deployment patterns** berbeda untuk deploy Suricata Dashboard di Kubernetes (termasuk RKE2) sesuai dengan use case dan infrastructure setup Anda.

## 🎯 Deployment Patterns

### Pattern 1: HostPath (Single/Dedicated Node)

**Use Case:** Suricata runs di host, dashboard baca logs via hostPath mount

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

**[View Full Documentation →](patterns/hostpath/README.md)**

---

### Pattern 2: DaemonSet (Multi-Node Distributed)

**Use Case:** Suricata di beberapa nodes, setiap node perlu dashboard sendiri

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
- ⚠️ Needs aggregation layer

**[View Full Documentation →](patterns/daemonset/README.md)**

---

### Pattern 3: NFS Shared Storage (Scalable)

**Use Case:** Centralized Suricata logs via NFS, dashboard scalable

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
- ✅ Not tied to nodes
- ⚠️ Requires NFS setup
- ⚠️ Network latency

**[View Full Documentation →](patterns/nfs/README.md)**

---

### Pattern 4: Sidecar (Fully Containerized)

**Use Case:** Suricata + Dashboard dalam 1 pod, fully portable

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

**[View Full Documentation →](patterns/sidecar/README.md)**

---

## 🤔 Which Pattern Should I Use?

### Decision Tree

```
Q: Is Suricata already running on host OS?
├─ YES
│  ├─ Q: Single node or multiple nodes?
│  │  ├─ Single/Dedicated → Use Pattern 1: HostPath
│  │  └─ Multiple nodes → Use Pattern 2: DaemonSet
│  └─ Q: Do you have NFS/shared storage?
│     └─ Yes → Consider Pattern 3: NFS
└─ NO (want fully containerized)
   └─ Use Pattern 4: Sidecar
```

### Quick Recommendations

| Scenario | Pattern | Why |
|----------|---------|-----|
| Single RKE2 node, Suricata on host | **HostPath** | Simplest setup |
| Multiple RKE2 nodes, Suricata on each | **DaemonSet** | Distributed monitoring |
| Want to scale dashboard replicas | **NFS** | Horizontal scaling |
| POC/Testing/Development | **Sidecar** | Easy setup |
| Cloud deployment (EKS/GKE/AKS) | **NFS** or **Sidecar** | Flexibility |
| High security environment | **HostPath** | Less attack surface |
| Multi-tenant edge nodes | **DaemonSet** | Per-node isolation |

## 📦 Directory Structure

```
kubernetes/
├── README.md                    # This file
├── base/                        # Common resources
│   ├── namespace.yaml          # Namespace definition
│   ├── configmap.yaml          # Application config
│   ├── secret.yaml             # Secret template
│   ├── postgres-statefulset.yaml  # Database
│   └── dashboard-service.yaml  # Service
│
├── patterns/                    # Deployment patterns
│   ├── hostpath/               # Pattern 1
│   │   ├── README.md
│   │   ├── deployment.yaml
│   │   ├── ingress.yaml
│   │   └── kustomization.yaml
│   │
│   ├── daemonset/              # Pattern 2
│   │   ├── README.md
│   │   ├── daemonset.yaml
│   │   └── kustomization.yaml
│   │
│   ├── nfs/                    # Pattern 3
│   │   ├── README.md
│   │   ├── deployment.yaml
│   │   ├── nfs-provisioner.yaml
│   │   ├── ingress.yaml
│   │   └── kustomization.yaml
│   │
│   └── sidecar/                # Pattern 4
│       ├── README.md
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── ingress.yaml
│       └── kustomization.yaml
│
└── overlays/                    # Environment overlays (optional)
    ├── development/
    └── production/
```

## 🚀 Quick Start

### Prerequisites

1. **Kubernetes Cluster**
   - RKE2, K3s, or any CNCF-compliant cluster
   - kubectl configured

2. **Tools**
   ```bash
   # Check kubectl
   kubectl version

   # Install kustomize (optional but recommended)
   kubectl kustomize --help

   # Or standalone kustomize
   curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
   ```

3. **Access to Container Registry**
   ```bash
   # Build and push dashboard image
   docker build -f ../Dockerfile -t your-registry/suricata-dashboard:latest ../../
   docker push your-registry/suricata-dashboard:latest
   ```

### Deployment Steps (Generic)

1. **Choose Pattern** based on your use case

2. **Update Configuration**
   ```bash
   cd patterns/<pattern-name>/

   # Edit deployment files
   # Update:
   # - Image registry
   # - NFS server (if using NFS pattern)
   # - Node labels (if using hostpath/daemonset)
   # - Ingress hostname
   ```

3. **Create Secret**
   ```bash
   kubectl create secret generic dashboard-secrets \
     --from-literal=DB_PASSWORD='your-secure-password' \
     --namespace=suricata-monitoring
   ```

4. **Deploy**
   ```bash
   # Using kubectl with kustomize
   kubectl apply -k .

   # Or using kustomize separately
   kustomize build . | kubectl apply -f -
   ```

5. **Verify**
   ```bash
   kubectl get all -n suricata-monitoring
   kubectl get pods -n suricata-monitoring -o wide
   kubectl logs -n suricata-monitoring -l app=suricata-dashboard -f
   ```

6. **Access Dashboard**
   ```bash
   # Get ingress/service info
   kubectl get ingress,svc -n suricata-monitoring

   # Or port-forward for quick access
   kubectl port-forward -n suricata-monitoring svc/dashboard-service 5000:5000
   # Access: http://localhost:5000
   ```

## 🔧 Configuration

### Base Configuration

File: `base/configmap.yaml`

```yaml
data:
  FLASK_HOST: "0.0.0.0"
  FLASK_PORT: "5000"
  DASHBOARD_NAME: "Suricata Dashboard"
  DB_TYPE: "postgresql"
  DB_HOST: "postgres-service"
  DB_PORT: "5432"
  # ... more settings
```

Edit untuk customize dashboard behavior.

### Secrets Management

**Development:**
```bash
kubectl create secret generic dashboard-secrets \
  --from-literal=DB_PASSWORD='devpassword' \
  --namespace=suricata-monitoring
```

**Production (Recommended):**

#### Option 1: Sealed Secrets
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

#### Option 2: External Secrets Operator
```bash
# Use with Vault, AWS Secrets Manager, etc.
# See: https://external-secrets.io/
```

### Storage Classes

Default menggunakan `local-path` (RKE2 default):

```yaml
storageClassName: local-path
```

**Available options for RKE2:**
- `local-path` - Local node storage (default)
- `longhorn` - Distributed block storage (if installed)
- Custom storage classes

Check available:
```bash
kubectl get storageclass
```

## 🔒 Security

### Pod Security Standards

Untuk patterns yang butuh privileges (sidecar):

```bash
kubectl label namespace suricata-monitoring \
  pod-security.kubernetes.io/enforce=privileged \
  pod-security.kubernetes.io/audit=privileged \
  pod-security.kubernetes.io/warn=privileged
```

### Network Policies

Example NetworkPolicy:

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

Jika dashboard perlu access Kubernetes API:

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

## 📊 Monitoring & Observability

### Prometheus Integration

Add ServiceMonitor (if Prometheus Operator installed):

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

### Logging

**Option 1: Built-in kubectl**
```bash
kubectl logs -n suricata-monitoring -l app=suricata-dashboard --tail=100 -f
```

**Option 2: Stern (multi-pod logs)**
```bash
# Install stern: https://github.com/stern/stern
stern -n suricata-monitoring suricata-dashboard
```

**Option 3: Loki/Grafana Stack**
```bash
# Deploy Loki stack
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack \
  --namespace=monitoring \
  --create-namespace \
  --set grafana.enabled=true
```

### Tracing (Advanced)

Integrate dengan Jaeger/Tempo untuk distributed tracing.

## 🔄 Updates & Maintenance

### Rolling Updates

```bash
# Update image
kubectl set image deployment/suricata-dashboard \
  dashboard=your-registry/suricata-dashboard:v1.1.0 \
  -n suricata-monitoring

# Check rollout status
kubectl rollout status deployment/suricata-dashboard -n suricata-monitoring

# Rollback if needed
kubectl rollout undo deployment/suricata-dashboard -n suricata-monitoring
```

### Backup Database

```bash
# Backup PostgreSQL
kubectl exec -n suricata-monitoring -it postgres-0 -- \
  pg_dump -U suricata suricata | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore
gunzip -c backup_20231201.sql.gz | \
  kubectl exec -i -n suricata-monitoring postgres-0 -- \
  psql -U suricata suricata
```

### Cleanup

```bash
# Delete specific pattern
kubectl delete -k patterns/<pattern-name>/

# Delete entire namespace
kubectl delete namespace suricata-monitoring
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Pods Not Starting

```bash
# Check events
kubectl get events -n suricata-monitoring --sort-by='.lastTimestamp'

# Describe pod
kubectl describe pod <pod-name> -n suricata-monitoring

# Check logs
kubectl logs <pod-name> -n suricata-monitoring
```

#### 2. ImagePullBackOff

```bash
# Check image exists
docker pull your-registry/suricata-dashboard:latest

# Check imagePullSecrets if using private registry
kubectl create secret docker-registry regcred \
  --docker-server=your-registry \
  --docker-username=user \
  --docker-password=pass \
  --namespace=suricata-monitoring

# Add to deployment:
# imagePullSecrets:
# - name: regcred
```

#### 3. CrashLoopBackOff

```bash
# Check previous logs
kubectl logs <pod-name> -n suricata-monitoring --previous

# Common causes:
# - Database not ready -> check postgres pod
# - Configuration error -> check configmap
# - Missing dependencies -> rebuild image
```

#### 4. Service Not Accessible

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

### Debug Tools

```bash
# Deploy debug pod
kubectl run -it --rm debug --image=nicolaka/netshoot -- bash

# Inside debug pod:
# - Test DNS: nslookup dashboard-service.suricata-monitoring
# - Test connectivity: curl http://dashboard-service:5000
# - Check network: ip addr, ip route
```

## 📖 Additional Resources

### RKE2 Specific

- [RKE2 Documentation](https://docs.rke2.io/)
- [RKE2 Ingress Controller](https://docs.rke2.io/networking#nginx-ingress-controller)
- [RKE2 Storage](https://docs.rke2.io/storage)

### Kubernetes

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize](https://kustomize.io/)
- [Kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)

### Pattern-Specific

- [HostPath Volumes](https://kubernetes.io/docs/concepts/storage/volumes/#hostpath)
- [DaemonSets](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)
- [NFS Volumes](https://kubernetes.io/docs/concepts/storage/volumes/#nfs)
- [Sidecar Pattern](https://kubernetes.io/docs/concepts/workloads/pods/#workload-resources-for-managing-pods)

## 💬 Support

Jika mengalami issues:

1. Check pattern-specific README
2. Review troubleshooting section
3. Check Kubernetes events: `kubectl get events -n suricata-monitoring`
4. Open issue di GitHub repository

## 🎓 Best Practices Summary

### Production Deployment

- [ ] Use private container registry
- [ ] Implement proper secret management (Sealed Secrets/External Secrets)
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

### Development

- [ ] Use namespace isolation
- [ ] Port-forward untuk local access
- [ ] Keep configs in git (except secrets!)
- [ ] Use kustomize overlays untuk environments
- [ ] Tag images dengan versions
- [ ] Test rolling updates
- [ ] Document changes

## 📝 License

Educational and defensive security purposes only.

---

**Quick Links:**
- [Pattern 1: HostPath](patterns/hostpath/README.md)
- [Pattern 2: DaemonSet](patterns/daemonset/README.md)
- [Pattern 3: NFS](patterns/nfs/README.md)
- [Pattern 4: Sidecar](patterns/sidecar/README.md)
- [Main Project README](../../README.md)
- [Docker Deployment](../README.md)
