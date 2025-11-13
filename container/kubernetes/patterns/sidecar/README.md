# Pattern 4: Sidecar Deployment

## Overview

Fully containerized solution dimana Suricata dan Dashboard berjalan dalam pod yang sama. Suricata container capture traffic dan Dashboard container membaca logs nya via shared volume.

**Karakteristik:**
- ✅ Fully containerized (portable)
- ✅ Easy deployment (single unit)
- ✅ Tight coupling (lifecycle sama)
- ✅ Shared volumes (low latency)
- ⚠️ Perlu privileges untuk packet capture
- ⚠️ Host network mode (untuk capture)
- ⚠️ Resource intensive (2 containers per pod)
- ⚠️ Suricata restart affects dashboard

## Architecture

```
┌──────────────────────────────────────────────┐
│  Pod: suricata-stack                         │
│                                              │
│  ┌────────────────────┐                     │
│  │ Suricata Container │                     │
│  │  - Capture traffic │                     │
│  │  - Write eve.json  │                     │
│  │  - CAP_NET_RAW     │                     │
│  └─────────┬──────────┘                     │
│            │ shared volume                   │
│            │ (emptyDir)                      │
│  ┌─────────▼──────────┐                     │
│  │ Dashboard Container│                     │
│  │  - Read eve.json   │                     │
│  │  - Serve web UI    │                     │
│  │  - Port: 5000      │                     │
│  └────────────────────┘                     │
│                                              │
│  Volumes:                                    │
│  ├─ suricata-logs (emptyDir, shared)        │
│  ├─ suricata-config (PVC)                   │
│  ├─ suricata-rules (PVC)                    │
│  ├─ dashboard-data (PVC)                    │
│  └─ dashboard-rrd (PVC)                     │
└──────────────────────────────────────────────┘
```

## Use Cases

### 1. Portable IDS
Deploy complete IDS stack anywhere dalam cluster.

### 2. Development/Testing
Easy setup untuk testing Suricata rules.

### 3. Cloud-Native Deployment
Full containerized solution tanpa dependency ke host.

### 4. POC/Demo
Quick demo Suricata + Dashboard.

## Prerequisites

### 1. Network Access

Pod perlu akses ke network interface untuk capture:

```bash
# Check available interfaces di node
kubectl get nodes -o wide

# Verify network plugin support
kubectl get pods -n kube-system | grep -E "calico|flannel|cilium"
```

### 2. Security Policy

Cluster harus allow privileged pods atau specific capabilities:

```bash
# Check Pod Security Standards
kubectl get ns suricata-monitoring -o yaml | grep -A5 labels

# If using PSS, label namespace:
kubectl label namespace suricata-monitoring \
  pod-security.kubernetes.io/enforce=privileged \
  pod-security.kubernetes.io/audit=privileged \
  pod-security.kubernetes.io/warn=privileged
```

### 3. Node Resources

Pastikan node punya resource cukup:

```bash
# Suricata: ~512MB-2GB RAM, 0.5-2 CPU
# Dashboard: ~256MB-512MB RAM, 0.25-0.5 CPU
# Total per pod: ~768MB-2.5GB RAM, 0.75-2.5 CPU

kubectl top nodes
kubectl describe nodes | grep -A5 "Allocated resources"
```

## Deployment

### Step 1: Configure Network Interface

Edit `deployment.yaml` dan set interface:

```yaml
containers:
- name: suricata
  command:
  - suricata
  - -c
  - /etc/suricata/suricata.yaml
  - -i
  - eth0  # Change this to your interface!
```

**Common interfaces:**
- `eth0` - Default Ethernet (most common)
- `ens0`, `ens3` - Predictable naming
- `any` - Listen on all interfaces (less efficient)

**Check from pod:**
```bash
kubectl run -it --rm netshoot --image=nicolaka/netshoot -- ip link show
```

### Step 2: Choose Security Mode

#### Option A: Specific Capabilities (Recommended)

```yaml
securityContext:
  capabilities:
    add:
    - NET_ADMIN
    - NET_RAW
    - SYS_NICE
```

#### Option B: Privileged Mode (Less Secure)

```yaml
securityContext:
  privileged: true
```

Update `deployment.yaml` accordingly.

### Step 3: Configure Storage

Default menggunakan `local-path` storage class (RKE2 default).

Jika mau pakai storage class lain:

```yaml
persistentVolumeClaim:
  storageClassName: your-storage-class  # Change this
```

### Step 4: Build Images (if needed)

```bash
# Dashboard image (already covered)
cd ../../../
docker build -f container/Dockerfile -t your-registry/suricata-dashboard:latest .
docker push your-registry/suricata-dashboard:latest

# Suricata image (using official)
# No build needed, uses: jasonish/suricata:latest
```

### Step 5: Deploy

```bash
cd container/kubernetes/patterns/sidecar

# Create namespace with PSS labels (if needed)
kubectl label namespace suricata-monitoring \
  pod-security.kubernetes.io/enforce=privileged \
  --overwrite

# Deploy
kubectl apply -k .
```

### Step 6: Verify

```bash
# Check pod
kubectl get pods -n suricata-monitoring -l app=suricata-stack -o wide

# Should show READY 2/2 (both containers running)

# Check Suricata logs
kubectl logs -n suricata-monitoring -l app=suricata-stack -c suricata --tail=50

# Check Dashboard logs
kubectl logs -n suricata-monitoring -l app=suricata-stack -c dashboard --tail=50

# Exec into Suricata container
kubectl exec -n suricata-monitoring <pod-name> -c suricata -it -- bash

# Inside container, check:
ps aux | grep suricata
cat /var/log/suricata/eve.json | head
suricata --version
```

## Access Dashboard

### Option 1: NodePort

```bash
# Get node IP
kubectl get nodes -o wide

# Access
http://<node-ip>:30500
```

### Option 2: Port-Forward

```bash
kubectl port-forward -n suricata-monitoring <pod-name> 5000:5000

# Access
http://localhost:5000
```

### Option 3: Ingress

```bash
# Add to /etc/hosts
echo "192.168.1.100 suricata.local" | sudo tee -a /etc/hosts

# Access
http://suricata.local
```

## Configuration

### Suricata Configuration

#### Update via ConfigMap

Create ConfigMap dengan Suricata config:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: suricata-config
  namespace: suricata-monitoring
data:
  suricata.yaml: |
    # Your Suricata configuration here
    %YAML 1.1
    ---
    vars:
      address-groups:
        HOME_NET: "[192.168.0.0/16,10.0.0.0/8]"
    # ... rest of config
```

Mount di pod:

```yaml
volumes:
- name: suricata-config
  configMap:
    name: suricata-config
```

#### Update Rules

```bash
# Exec into Suricata container
kubectl exec -n suricata-monitoring <pod-name> -c suricata -it -- bash

# Update rules
suricata-update

# Reload Suricata
kill -USR2 $(cat /var/run/suricata.pid)

# Or restart pod
kubectl delete pod <pod-name> -n suricata-monitoring
```

### Dashboard Configuration

Edit ConfigMap di `../../base/configmap.yaml` kemudian:

```bash
kubectl apply -k .
kubectl rollout restart deployment/suricata-stack -n suricata-monitoring
```

## Scaling Considerations

### Horizontal Scaling

**Possible** tapi dengan caveats:

```yaml
spec:
  replicas: 2  # Multiple pods
```

**Considerations:**
- Each pod captures independent traffic
- Perlu load balancing upstream (router/switch mirroring)
- Useful untuk high-traffic environments
- Database shared across all pods

### Vertical Scaling

Adjust resources per pod:

```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "4000m"
```

## Monitoring

### Container Logs

```bash
# Stream both containers
kubectl logs -n suricata-monitoring <pod-name> -c suricata -f
kubectl logs -n suricata-monitoring <pod-name> -c dashboard -f

# Or use stern
stern -n suricata-monitoring suricata-stack
```

### Resource Usage

```bash
# Pod resources
kubectl top pod -n suricata-monitoring

# Container breakdown (requires metrics-server)
kubectl top pod -n suricata-monitoring --containers
```

### Suricata Stats

```bash
# Check stats.log
kubectl exec -n suricata-monitoring <pod-name> -c suricata -- \
  tail -f /var/log/suricata/stats.log

# Check eve.json for stats events
kubectl exec -n suricata-monitoring <pod-name> -c suricata -- \
  grep '"event_type":"stats"' /var/log/suricata/eve.json | tail -n1 | jq
```

## Troubleshooting

### Suricata Not Capturing

```bash
# Check capabilities
kubectl exec -n suricata-monitoring <pod-name> -c suricata -- \
  capsh --print

# Should show: cap_net_admin, cap_net_raw

# Check interface
kubectl exec -n suricata-monitoring <pod-name> -c suricata -- \
  ip link show

# Check if Suricata process running
kubectl exec -n suricata-monitoring <pod-name> -c suricata -- \
  ps aux | grep suricata

# Check Suricata errors
kubectl logs -n suricata-monitoring <pod-name> -c suricata | grep -i error
```

### Permission Denied Errors

```bash
# Check PSS labels on namespace
kubectl get ns suricata-monitoring -o yaml | grep pod-security

# Should be 'privileged' or have exceptions

# Add PSS labels
kubectl label namespace suricata-monitoring \
  pod-security.kubernetes.io/enforce=privileged \
  pod-security.kubernetes.io/audit=privileged \
  pod-security.kubernetes.io/warn=privileged \
  --overwrite
```

### Dashboard Can't Read Logs

```bash
# Check shared volume
kubectl exec -n suricata-monitoring <pod-name> -c dashboard -- \
  ls -la /var/log/suricata/

# Check if eve.json exists and has data
kubectl exec -n suricata-monitoring <pod-name> -c dashboard -- \
  tail -f /var/log/suricata/eve.json

# Check volume mounts
kubectl describe pod <pod-name> -n suricata-monitoring | grep -A10 Mounts
```

### Pod Keeps Restarting

```bash
# Check events
kubectl describe pod <pod-name> -n suricata-monitoring

# Common causes:
# 1. OOMKilled - Increase memory limits
# 2. CrashLoopBackOff - Check container logs
# 3. Network interface not found - Update interface name
# 4. Permission denied - Check security context

# Check previous logs
kubectl logs -n suricata-monitoring <pod-name> -c suricata --previous
```

### High Resource Usage

```bash
# Check current usage
kubectl top pod <pod-name> -n suricata-monitoring --containers

# Tune Suricata:
# - Reduce thread count
# - Adjust buffer sizes
# - Limit pcap size
# - Disable unnecessary features

# Edit suricata.yaml via ConfigMap
```

## Performance Tuning

### Suricata

```yaml
# In suricata.yaml ConfigMap
threading:
  set-cpu-affinity: yes
  cpu-affinity:
    - management-cpu-set:
        cpu: [ 0 ]
    - receive-cpu-set:
        cpu: [ 1,2 ]
    - worker-cpu-set:
        cpu: [ 1,2,3,4 ]

af-packet:
  - interface: eth0
    cluster-type: cluster_flow
    defrag: yes
    use-mmap: yes
    mmap-locked: yes
    ring-size: 2048
    block-size: 32768
```

### Dashboard

```yaml
env:
- name: TRAFFIC_AGGREGATION_INTERVAL
  value: "600"  # 10 minutes untuk reduce CPU
- name: DB_STORE_TIME
  value: "120"  # 2 minutes untuk reduce DB writes
```

## Security Hardening

### 1. Read-Only Root Filesystem

```yaml
securityContext:
  readOnlyRootFilesystem: true

# Add writable volumes for logs
volumeMounts:
- name: tmp
  mountPath: /tmp
- name: var-run
  mountPath: /var/run
```

### 2. Drop Unnecessary Capabilities

```yaml
securityContext:
  capabilities:
    drop:
    - ALL
    add:
    - NET_ADMIN
    - NET_RAW
    - SYS_NICE  # Only if needed
```

### 3. Non-Root Users

Dashboard already runs as uid 1000. Untuk Suricata:

```yaml
securityContext:
  runAsUser: 1000
  runAsGroup: 1000
```

**Note:** Might conflict dengan packet capture requirements.

### 4. NetworkPolicy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: suricata-stack-netpol
spec:
  podSelector:
    matchLabels:
      app: suricata-stack
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
  - to:  # Allow DNS
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
```

## Updates

### Update Suricata

```bash
# Update image version
kubectl set image deployment/suricata-stack \
  suricata=jasonish/suricata:7.0.0 \
  -n suricata-monitoring

# Or edit deployment
kubectl edit deployment suricata-stack -n suricata-monitoring
```

### Update Dashboard

```bash
kubectl set image deployment/suricata-stack \
  dashboard=your-registry/suricata-dashboard:v1.1.0 \
  -n suricata-monitoring
```

### Update Configuration

```bash
# Edit ConfigMap
kubectl edit configmap dashboard-config -n suricata-monitoring

# Restart deployment
kubectl rollout restart deployment/suricata-stack -n suricata-monitoring
```

## Cleanup

```bash
kubectl delete -k .

# Or delete namespace
kubectl delete namespace suricata-monitoring
```

## Production Checklist

- [ ] PSS labels configured on namespace
- [ ] Security context properly configured
- [ ] Resource limits tuned for traffic volume
- [ ] Network interface verified
- [ ] Persistent volumes configured with backups
- [ ] Monitoring and alerting setup
- [ ] Log rotation configured
- [ ] NetworkPolicy applied
- [ ] Ingress with TLS configured
- [ ] Regular rule updates scheduled
- [ ] Disaster recovery plan documented

## Advanced Configurations

### AF_PACKET Clustering

For high-performance:

```yaml
suricata.yaml:
  af-packet:
    - interface: eth0
      cluster-id: 99
      cluster-type: cluster_flow
      defrag: yes
```

### Multiple Interfaces

```yaml
command:
- suricata
- -c
- /etc/suricata/suricata.yaml
- -i
- eth0
- -i
- eth1
```

### GPU Acceleration (Future)

Some Suricata builds support GPU acceleration untuk pattern matching.

## Next Steps

- Setup Prometheus metrics export dari Suricata
- Implement automated rule updates
- Configure alerting untuk critical events
- Setup distributed tracing
- Consider service mesh integration
- Implement blue/green deployments
