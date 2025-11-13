# Pattern 2: DaemonSet Deployment

## Overview

Deployment pattern untuk multi-node cluster dimana Suricata berjalan di beberapa atau semua node. Setiap node akan memiliki instance dashboard sendiri yang monitor Suricata lokal.

**Karakteristik:**
- ✅ Distributed monitoring (1 dashboard per node)
- ✅ High availability (multiple instances)
- ✅ Node-local metrics dan logs
- ✅ Automatic pod scheduling ke node baru
- ⚠️ Setiap dashboard independent
- ⚠️ Perlu aggregation layer jika mau centralized view

## Architecture

```
┌─────────────────────────────────────┐
│  RKE2 Node 1 (suricata=enabled)     │
│  ├─ Suricata Process                │
│  ├─ /var/log/suricata/              │
│  └─ Dashboard Pod (DaemonSet)       │
│     └─ NodePort: 30500              │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  RKE2 Node 2 (suricata=enabled)     │
│  ├─ Suricata Process                │
│  ├─ /var/log/suricata/              │
│  └─ Dashboard Pod (DaemonSet)       │
│     └─ NodePort: 30500              │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  RKE2 Node 3 (suricata=enabled)     │
│  ├─ Suricata Process                │
│  ├─ /var/log/suricata/              │
│  └─ Dashboard Pod (DaemonSet)       │
│     └─ NodePort: 30500              │
└─────────────────────────────────────┘

         ⬇ All connect to
┌─────────────────────────────────────┐
│  PostgreSQL (StatefulSet)           │
│  └─ Shared database for all nodes   │
└─────────────────────────────────────┘
```

## Use Cases

### 1. Edge Monitoring
Setiap edge node monitor traffic lokalnya sendiri.

### 2. Multi-Tenant
Setiap node serve tenant yang berbeda.

### 3. Distributed IDS
Deploy Suricata di multiple choke points.

### 4. High Traffic Networks
Distribute load across multiple nodes.

## Prerequisites

### 1. Label Nodes

Label semua nodes yang menjalankan Suricata:

```bash
# List all nodes
kubectl get nodes

# Label nodes yang ada Suricata
kubectl label nodes node1 suricata=enabled
kubectl label nodes node2 suricata=enabled
kubectl label nodes node3 suricata=enabled

# Or label all nodes at once
kubectl label nodes --all suricata=enabled

# Verify labels
kubectl get nodes -l suricata=enabled --show-labels
```

### 2. Setup Suricata on Each Node

Pastikan Suricata dan paths nya exist di setiap node:

```bash
# SSH ke setiap node dan verify
for node in node1 node2 node3; do
  echo "Checking $node..."
  ssh $node "ls -la /var/log/suricata/eve.json && ls -la /etc/suricata/"
done
```

### 3. Create Host Directories

Create directories untuk persistent storage di setiap node:

```bash
# On each node
sudo mkdir -p /var/lib/suricata-dashboard/{data,logs,rrd}
sudo chown -R 1000:1000 /var/lib/suricata-dashboard/
sudo chmod -R 755 /var/lib/suricata-dashboard/
```

## Deployment

### Step 1: Build and Push Image

```bash
cd ../../../  # Back to repo root
docker build -f container/Dockerfile -t your-registry/suricata-dashboard:latest .
docker push your-registry/suricata-dashboard:latest
```

### Step 2: Configure Secret

```bash
kubectl create secret generic dashboard-secrets \
  --from-literal=DB_PASSWORD='your-secure-password' \
  --namespace=suricata-monitoring
```

### Step 3: Deploy

```bash
cd container/kubernetes/patterns/daemonset

# Deploy
kubectl apply -k .

# Or
kustomize build . | kubectl apply -f -
```

### Step 4: Verify Deployment

```bash
# Check DaemonSet status
kubectl get daemonset -n suricata-monitoring

# Check pods - should be one per labeled node
kubectl get pods -n suricata-monitoring -o wide -l app=suricata-dashboard

# Should output:
# NAME                       READY   STATUS    NODE
# suricata-dashboard-abc123  1/1     Running   node1
# suricata-dashboard-def456  1/1     Running   node2
# suricata-dashboard-ghi789  1/1     Running   node3

# Check logs from specific node
kubectl logs -n suricata-monitoring -l app=suricata-dashboard --tail=50

# Check logs from specific pod
kubectl logs -n suricata-monitoring <pod-name> -f
```

## Access Dashboard

### Option 1: NodePort (Individual Nodes)

Access dashboard di setiap node via NodePort:

```bash
# Get node IPs
kubectl get nodes -o wide

# Access dashboard on each node
http://node1-ip:30500
http://node2-ip:30500
http://node3-ip:30500
```

### Option 2: Port-Forward (Development)

```bash
# Forward dari specific pod
kubectl port-forward -n suricata-monitoring <pod-name> 5000:5000

# Access
http://localhost:5000
```

### Option 3: LoadBalancer (Cloud)

Edit `daemonset.yaml` dan ubah service type:

```yaml
spec:
  type: LoadBalancer  # Change from NodePort
```

### Option 4: Ingress (Multiple Hosts)

Create ingress untuk setiap node:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dashboard-multi-ingress
spec:
  rules:
  - host: node1.suricata.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: dashboard-nodeport
            port:
              number: 5000
```

## Database Considerations

### Shared Database

Semua dashboard pods connect ke PostgreSQL yang sama:

**Pros:**
- Centralized data
- Query across all nodes
- Consistent retention policy

**Cons:**
- Single point of failure
- Database could be bottleneck

**Current setup**: Shared PostgreSQL (default)

### Per-Node Database (Alternative)

Deploy PostgreSQL sebagai DaemonSet juga:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: postgres-local
```

**Pros:**
- Node-local data
- No single point of failure
- Better performance (no network latency)

**Cons:**
- No centralized view
- More resource usage
- Complex backup strategy

## Storage Strategy

### Option 1: HostPath (Current Default)

```yaml
volumes:
- name: app-data
  hostPath:
    path: /var/lib/suricata-dashboard/data
    type: DirectoryOrCreate
```

**Pros:**
- Data persists across pod restarts
- Fast (local disk)

**Cons:**
- Pod tied to specific node
- Manual backup needed

### Option 2: EmptyDir

```yaml
volumes:
- name: app-data
  emptyDir: {}
```

**Pros:**
- Simple
- No persistence concerns

**Cons:**
- Data lost on pod restart
- Not suitable for production

### Option 3: Local PV

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: dashboard-data-node1
spec:
  capacity:
    storage: 5Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-storage
  local:
    path: /var/lib/suricata-dashboard/data
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - node1
```

## Scaling

### Add New Node

```bash
# Add new node to cluster (RKE2 specific)
# ... follow RKE2 node join process ...

# Label new node
kubectl label nodes new-node suricata=enabled

# DaemonSet automatically schedules pod to new node
kubectl get pods -n suricata-monitoring -o wide
```

### Remove Node from Monitoring

```bash
# Remove label - DaemonSet will delete pod
kubectl label nodes node-name suricata-

# Verify
kubectl get pods -n suricata-monitoring -o wide
```

### Update Node Selector

Edit DaemonSet to change targeting:

```bash
kubectl edit daemonset suricata-dashboard -n suricata-monitoring

# Change nodeSelector criteria
nodeSelector:
  suricata: enabled
  environment: production  # Add additional selector
```

## Monitoring & Aggregation

### Individual Node Monitoring

Access each dashboard directly to see node-specific metrics.

### Centralized Monitoring (Optional)

Setup aggregation layer dengan:

#### Option A: Prometheus + Grafana

```bash
# Each dashboard pod exports metrics
# Prometheus scrapes all pods
# Grafana aggregates views
```

#### Option B: Custom Aggregator

Deploy separate service yang query database:

```python
# Query traffic from all nodes
SELECT node_name, SUM(packets) FROM traffic_stats
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY node_name;
```

#### Option C: ELK Stack

Ship logs dari semua pods ke Elasticsearch:

```yaml
# Add sidecar or use daemonset fluentd
```

## Troubleshooting

### Pods not scheduling

```bash
# Check DaemonSet status
kubectl describe daemonset suricata-dashboard -n suricata-monitoring

# Check node labels
kubectl get nodes -l suricata=enabled

# Check node taints
kubectl describe nodes | grep -i taint
```

### Pods on wrong nodes

```bash
# Verify node selector
kubectl get daemonset suricata-dashboard -n suricata-monitoring -o yaml | grep -A5 nodeSelector

# Check pod placement
kubectl get pods -n suricata-monitoring -o wide
```

### Different behavior across nodes

```bash
# Compare configurations
for pod in $(kubectl get pods -n suricata-monitoring -l app=suricata-dashboard -o name); do
  echo "=== $pod ==="
  kubectl exec -n suricata-monitoring $pod -- env | sort
done

# Check Suricata versions on nodes
for node in node1 node2 node3; do
  echo "=== $node ==="
  ssh $node "suricata --version"
done
```

### Database connection issues

```bash
# Test from each pod
for pod in $(kubectl get pods -n suricata-monitoring -l app=suricata-dashboard -o name); do
  echo "Testing $pod..."
  kubectl exec -n suricata-monitoring $pod -- \
    python -c "from config import Config; print(Config.DB_HOST)"
done
```

## Updates

### Rolling Update

DaemonSet supports rolling updates:

```bash
# Update image
kubectl set image daemonset/suricata-dashboard \
  dashboard=your-registry/suricata-dashboard:v1.1.0 \
  -n suricata-monitoring

# Check rollout status
kubectl rollout status daemonset/suricata-dashboard -n suricata-monitoring

# Rollback if needed
kubectl rollout undo daemonset/suricata-dashboard -n suricata-monitoring
```

### Update Strategy

Configure update strategy in DaemonSet:

```yaml
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1  # Update one node at a time
```

## Cleanup

```bash
# Delete DaemonSet (pods on all nodes deleted)
kubectl delete -k .

# Or delete namespace
kubectl delete namespace suricata-monitoring

# Remove node labels
kubectl label nodes --all suricata-

# Cleanup host directories (on each node)
for node in node1 node2 node3; do
  ssh $node "sudo rm -rf /var/lib/suricata-dashboard/"
done
```

## Production Checklist

- [ ] All nodes labeled correctly
- [ ] Suricata verified on all nodes
- [ ] Host directories created with correct permissions
- [ ] Secret created with strong password
- [ ] Image pushed to private registry
- [ ] Resource limits tuned per node capacity
- [ ] Database HA configured (if shared)
- [ ] Monitoring setup (per-node metrics)
- [ ] Log aggregation configured
- [ ] Backup strategy for node-local data
- [ ] NetworkPolicy configured
- [ ] Update strategy tested

## Advanced Configurations

### Run on Control Plane Nodes

```yaml
tolerations:
- key: node-role.kubernetes.io/control-plane
  operator: Exists
  effect: NoSchedule
- key: node-role.kubernetes.io/master
  operator: Exists
  effect: NoSchedule
```

### Priority Class

```yaml
priorityClassName: system-node-critical
```

### Resource Guarantees

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Anti-Affinity (if needed)

Meskipun DaemonSet, bisa combine dengan affinity rules:

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: node-role.kubernetes.io/worker
          operator: Exists
```

## Next Steps

- Setup centralized monitoring dashboard
- Implement metrics aggregation
- Configure alerting per node
- Setup automated backup for node-local data
- Consider service mesh for better observability
