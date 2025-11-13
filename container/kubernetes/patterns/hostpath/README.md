# Pattern 1: HostPath Deployment

## Overview

Deployment pattern untuk single-node atau dedicated monitoring node dimana Suricata sudah berjalan di host OS.

**Karakteristik:**
- ✅ Simple setup
- ✅ Langsung akses filesystem host
- ✅ Cocok untuk RKE2 single-node atau dedicated node
- ⚠️ Pod harus jalan di node yang sama dengan Suricata
- ⚠️ Tidak bisa di-scale horizontal

## Architecture

```
┌─────────────────────────────────────────┐
│  RKE2 Node (Labeled: suricata=enabled)  │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Host OS                          │ │
│  │  ├─ Suricata Process              │ │
│  │  ├─ /var/log/suricata/            │ │
│  │  └─ /etc/suricata/                │ │
│  └───────────────┬───────────────────┘ │
│                  │ hostPath mount       │
│  ┌───────────────▼───────────────────┐ │
│  │  Dashboard Pod                    │ │
│  │  (nodeSelector: suricata=enabled) │ │
│  │  └─ Read-only access to logs      │ │
│  └───────────────┬───────────────────┘ │
│                  │                      │
│  ┌───────────────▼───────────────────┐ │
│  │  PostgreSQL Pod (StatefulSet)     │ │
│  │  └─ PVC: local-path storage       │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## Prerequisites

### 1. Label Node

Label node yang menjalankan Suricata:

```bash
# Check node name
kubectl get nodes

# Label node
kubectl label nodes <node-name> suricata=enabled

# Verify label
kubectl get nodes --show-labels | grep suricata
```

### 2. Verify Suricata Paths

Pastikan path-path berikut exist di node:

```bash
# Login ke node
ssh <node-ip>

# Check Suricata installation
ls -la /var/log/suricata/eve.json
ls -la /etc/suricata/suricata.yaml
ls -la /etc/suricata/rules/

# Check permissions (dashboard runs as uid 1000)
stat /var/log/suricata/
```

### 3. Fix Permissions (if needed)

Jika dashboard tidak bisa baca logs:

```bash
# Option 1: Make logs readable by all
sudo chmod -R o+r /var/log/suricata/
sudo chmod o+x /var/log/suricata/

# Option 2: Change ownership to uid 1000
sudo chown -R 1000:1000 /var/log/suricata/

# Option 3: Add to group
sudo usermod -aG suricata 1000
```

## Deployment

### Step 1: Build and Push Image

```bash
# Build image
cd ../../../  # Back to repo root
docker build -f container/Dockerfile -t your-registry/suricata-dashboard:latest .

# Push to registry
docker push your-registry/suricata-dashboard:latest

# Update image in deployment.yaml
# Edit: container/kubernetes/patterns/hostpath/deployment.yaml
# Change: image: ghcr.io/yourusername/suricata-dashboard:latest
```

### Step 2: Configure Secret

```bash
# Create secret with your password
kubectl create secret generic dashboard-secrets \
  --from-literal=DB_PASSWORD='your-secure-password' \
  --namespace=suricata-monitoring \
  --dry-run=client -o yaml | kubectl apply -f -
```

### Step 3: Update Ingress Hostname

Edit `ingress.yaml` dan ubah hostname:

```yaml
spec:
  rules:
  - host: suricata.yourdomain.com  # Change this!
```

### Step 4: Deploy

```bash
cd container/kubernetes/patterns/hostpath

# Deploy using kubectl
kubectl apply -k .

# Or using kustomize directly
kustomize build . | kubectl apply -f -
```

### Step 5: Verify Deployment

```bash
# Check all resources
kubectl get all -n suricata-monitoring

# Check pods
kubectl get pods -n suricata-monitoring -o wide

# Check if pod is on correct node
kubectl get pods -n suricata-monitoring -l app=suricata-dashboard -o wide

# Check logs
kubectl logs -n suricata-monitoring -l app=suricata-dashboard -f

# Check PostgreSQL
kubectl logs -n suricata-monitoring -l app=postgres
```

### Step 6: Access Dashboard

```bash
# Get ingress IP
kubectl get ingress -n suricata-monitoring

# Add to /etc/hosts (if using .local domain)
echo "192.168.1.100 suricata-dashboard.local" | sudo tee -a /etc/hosts

# Access via browser
http://suricata-dashboard.local
```

## Configuration

### Storage Class

RKE2 default menggunakan `local-path` storage class:

```bash
# Check available storage classes
kubectl get storageclass

# Should show:
# NAME                   PROVISIONER             RECLAIMPOLICY
# local-path (default)   rancher.io/local-path   Delete
```

Jika ingin pakai storage class lain, edit di `deployment.yaml`:

```yaml
persistentVolumeClaim:
  storageClassName: your-storage-class
```

### Resource Limits

Default resource limits:

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

Adjust sesuai kebutuhan di `deployment.yaml`.

### ConfigMap Customization

Edit ConfigMap di `../../base/configmap.yaml` untuk customize settings.

## Troubleshooting

### Pod tidak jalan di node yang benar

```bash
# Check pod events
kubectl describe pod -n suricata-monitoring -l app=suricata-dashboard

# Check node selector
kubectl get pod -n suricata-monitoring -l app=suricata-dashboard -o yaml | grep -A5 nodeSelector
```

### Permission denied reading logs

```bash
# Check from inside pod
kubectl exec -n suricata-monitoring -it <pod-name> -- ls -la /var/log/suricata/

# Check on node
ssh <node-ip>
ls -la /var/log/suricata/
stat /var/log/suricata/eve.json
```

Fix:
```bash
# On the node
sudo chmod -R o+rx /var/log/suricata/
```

### Dashboard tidak bisa connect ke PostgreSQL

```bash
# Check PostgreSQL status
kubectl get pods -n suricata-monitoring -l app=postgres

# Check PostgreSQL logs
kubectl logs -n suricata-monitoring -l app=postgres

# Test connection from dashboard pod
kubectl exec -n suricata-monitoring -it <dashboard-pod> -- \
  python -c "
from config import Config
print(f'DB Host: {Config.DB_HOST}')
print(f'DB Port: {Config.DB_PORT}')
"
```

### Ingress tidak work

```bash
# Check ingress controller
kubectl get pods -n kube-system | grep nginx

# Check ingress
kubectl describe ingress -n suricata-monitoring dashboard-ingress

# Check service
kubectl get svc -n suricata-monitoring dashboard-service

# Test from inside cluster
kubectl run -it --rm debug --image=nicolaka/netshoot -- \
  curl http://dashboard-service.suricata-monitoring.svc.cluster.local:5000/api/status
```

## Updates

### Update Application

```bash
# Build new image with tag
docker build -f container/Dockerfile -t your-registry/suricata-dashboard:v1.1.0 .
docker push your-registry/suricata-dashboard:v1.1.0

# Update deployment
kubectl set image deployment/suricata-dashboard \
  dashboard=your-registry/suricata-dashboard:v1.1.0 \
  -n suricata-monitoring

# Or edit deployment
kubectl edit deployment suricata-dashboard -n suricata-monitoring

# Rollout status
kubectl rollout status deployment/suricata-dashboard -n suricata-monitoring

# Rollback if needed
kubectl rollout undo deployment/suricata-dashboard -n suricata-monitoring
```

### Update ConfigMap

```bash
# Edit configmap
kubectl edit configmap dashboard-config -n suricata-monitoring

# Restart pods to apply changes
kubectl rollout restart deployment/suricata-dashboard -n suricata-monitoring
```

## Cleanup

```bash
# Delete all resources
kubectl delete -k .

# Or delete namespace (removes everything)
kubectl delete namespace suricata-monitoring

# Remove node label
kubectl label nodes <node-name> suricata-
```

## Security Notes

1. **Read-only mounts**: Suricata logs dan config di-mount read-only untuk security
2. **Non-root user**: Dashboard runs as uid 1000 (non-root)
3. **Secret management**: Gunakan sealed-secrets atau external secrets untuk production
4. **Network policies**: Consider adding NetworkPolicy untuk isolate traffic
5. **RBAC**: Create dedicated ServiceAccount jika perlu akses Kubernetes API

## Production Checklist

- [ ] Image pushed ke private registry
- [ ] Secret created dengan password yang kuat
- [ ] Node label applied
- [ ] Permissions di node sudah benar
- [ ] Ingress hostname configured
- [ ] TLS certificate configured (optional tapi recommended)
- [ ] Resource limits adjusted sesuai workload
- [ ] Backup strategy untuk PostgreSQL data
- [ ] Monitoring setup (Prometheus/Grafana)
- [ ] Log aggregation setup (Loki/ELK)

## Next Steps

- Setup TLS/HTTPS dengan cert-manager
- Configure NetworkPolicy
- Setup monitoring dengan Prometheus
- Setup backup untuk PostgreSQL
- Consider External Secrets Operator untuk secret management
