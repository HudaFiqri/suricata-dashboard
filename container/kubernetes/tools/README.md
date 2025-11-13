# Kubernetes Deployment Tools

Automated deployment tools untuk Suricata Dashboard di Kubernetes - **simple & straightforward!**

## 🚀 Quick Start - Langsung Deploy!

```bash
cd tools

# Deploy langsung - tanpa banyak prompt
./quick-deploy.sh

# Atau pilih pattern specific
./quick-deploy.sh daemonset
./quick-deploy.sh nfs
./quick-deploy.sh sidecar
```

**That's it!** Script akan auto:
- ✅ Check prerequisites
- ✅ Create secret (auto-generated password)
- ✅ Label nodes (if needed)
- ✅ Setup PSS (if sidecar)
- ✅ Deploy pattern
- ✅ Wait for pods
- ✅ Show access info

---

## 📋 Available Tools

### 1. **quick-deploy.sh** ⭐ (Recommended)
**One-liner deployment** - minimal interaction, just works!

```bash
# Deploy dengan defaults
./quick-deploy.sh

# Deploy specific pattern
./quick-deploy.sh hostpath
./quick-deploy.sh daemonset
./quick-deploy.sh nfs
./quick-deploy.sh sidecar

# Custom password
./quick-deploy.sh --password mySecurePass

# Skip secret creation (already exists)
./quick-deploy.sh --skip-secret

# Skip node labeling (already labeled)
./quick-deploy.sh daemonset --skip-labels
```

**Options:**
```
--skip-secret       Skip secret creation
--skip-labels       Skip node labeling
--password PASS     Custom database password
-h, --help          Show help
```

---

### 2. **deploy.sh** (Interactive)
**Full interactive wizard** dengan guidance di setiap step.

```bash
./deploy.sh
```

**Features:**
- Step-by-step guidance
- Pattern selection menu
- Configuration validation
- Deployment preview
- Detailed status info

Use this jika:
- First time deployment
- Want to understand each step
- Need configuration help

---

### 3. **build-push.sh** (Image Builder)
Build dan push Docker images.

```bash
# Build only
./build-push.sh

# Build and push
./build-push.sh -r ghcr.io/username -t v1.0.0 -p

# Build with custom tag
./build-push.sh -t dev-$(git rev-parse --short HEAD)
```

**Common usage:**
```bash
# GitHub Container Registry
./build-push.sh -r ghcr.io/yourusername -t latest -p

# Docker Hub
./build-push.sh -r docker.io/yourusername -t v1.0.0 -p

# Private registry
./build-push.sh -r registry.company.com/team -t latest -p
```

---

### 4. **rollback.sh** (Rollback Tool)
Rollback deployment ke versi sebelumnya.

```bash
# Rollback to previous
./rollback.sh

# Rollback to specific revision
./rollback.sh --revision 3

# Show history first
./rollback.sh --history
```

---

### 5. **scale.sh** (Scaling Tool)
Scale replicas up/down.

```bash
# Scale to 3 replicas
./scale.sh --replicas 3

# Check current status
./scale.sh --status
```

**Note:** Cannot scale DaemonSet (automatically runs one pod per labeled node)

---

## 🎯 Common Workflows

### First Time Deployment

```bash
# Option A: Quick (Recommended)
./quick-deploy.sh

# Option B: Interactive
./deploy.sh
```

### Update Deployment

```bash
# 1. Build new image
./build-push.sh -r ghcr.io/user -t v1.1.0 -p

# 2. Update deployment
kubectl set image deployment/suricata-dashboard \
  dashboard=ghcr.io/user/suricata-dashboard:v1.1.0 \
  -n suricata-monitoring

# 3. Check status
kubectl get pods -n suricata-monitoring -w
```

### Rollback if Issues

```bash
# Quick rollback
./rollback.sh

# Or to specific version
./rollback.sh --revision 2
```

### Scale Up/Down

```bash
# Scale to 5 replicas
./scale.sh --replicas 5

# Scale to 1
./scale.sh --replicas 1
```

---

## 🛠️ Manual Deployment (Without Scripts)

Jika prefer manual:

```bash
# 1. Create namespace
kubectl create namespace suricata-monitoring

# 2. Create secret
kubectl create secret generic dashboard-secrets \
  --from-literal=DB_PASSWORD='your-password' \
  --namespace=suricata-monitoring

# 3. Label nodes (for hostpath/daemonset)
kubectl label nodes <node-name> suricata=enabled

# 4. Deploy pattern
cd ../patterns/hostpath
kubectl apply -k .

# 5. Check status
kubectl get pods -n suricata-monitoring -o wide
```

---

## 📊 Monitoring & Management

### View Logs

```bash
# Stream dashboard logs
kubectl logs -f -n suricata-monitoring -l app=suricata-dashboard

# All pods
kubectl logs -f -n suricata-monitoring --all-containers=true

# Previous logs (if pod crashed)
kubectl logs -n suricata-monitoring <pod-name> --previous
```

### Check Status

```bash
# All resources
kubectl get all -n suricata-monitoring

# Pods with details
kubectl get pods -n suricata-monitoring -o wide

# Events
kubectl get events -n suricata-monitoring --sort-by='.lastTimestamp'

# Describe pod
kubectl describe pod <pod-name> -n suricata-monitoring
```

### Port Forward (Local Access)

```bash
# Forward dashboard
kubectl port-forward -n suricata-monitoring svc/dashboard-service 5000:5000

# Access at: http://localhost:5000

# Forward database (for debugging)
kubectl port-forward -n suricata-monitoring svc/postgres-service 5432:5432
```

### Get Shell in Pod

```bash
# Dashboard pod
POD=$(kubectl get pod -n suricata-monitoring -l app=suricata-dashboard -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it -n suricata-monitoring $POD -- bash

# Database pod
kubectl exec -it -n suricata-monitoring postgres-0 -- bash
```

### Resource Usage

```bash
# Pod resources
kubectl top pods -n suricata-monitoring

# Container breakdown
kubectl top pods -n suricata-monitoring --containers

# Node resources
kubectl top nodes
```

---

## 💾 Database Operations

### Backup

```bash
# Backup database
kubectl exec -n suricata-monitoring postgres-0 -- \
  pg_dump -U suricata suricata > backup_$(date +%Y%m%d).sql

# Compressed backup
kubectl exec -n suricata-monitoring postgres-0 -- \
  pg_dump -U suricata suricata | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore

```bash
# Restore from backup
kubectl exec -i -n suricata-monitoring postgres-0 -- \
  psql -U suricata suricata < backup.sql

# From compressed
gunzip -c backup.sql.gz | \
  kubectl exec -i -n suricata-monitoring postgres-0 -- \
  psql -U suricata suricata
```

### PostgreSQL Shell

```bash
kubectl exec -it -n suricata-monitoring postgres-0 -- \
  psql -U suricata

# Run query
kubectl exec -n suricata-monitoring postgres-0 -- \
  psql -U suricata -c "SELECT COUNT(*) FROM alerts;"
```

---

## 🧹 Cleanup

### Remove Deployment

```bash
# Delete specific pattern
cd ../patterns/hostpath
kubectl delete -k .

# Or delete entire namespace
kubectl delete namespace suricata-monitoring
```

### Clean Failed Pods

```bash
kubectl delete pods -n suricata-monitoring --field-selector status.phase=Failed
```

### Remove Node Labels

```bash
kubectl label nodes <node-name> suricata-
```

---

## 🐛 Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n suricata-monitoring

# Check events
kubectl get events -n suricata-monitoring --sort-by='.lastTimestamp'

# Describe pod
kubectl describe pod <pod-name> -n suricata-monitoring

# Check logs
kubectl logs <pod-name> -n suricata-monitoring
```

### ImagePullBackOff

```bash
# Verify image exists
docker pull ghcr.io/user/suricata-dashboard:tag

# Create imagePullSecret if needed
kubectl create secret docker-registry regcred \
  --docker-server=ghcr.io \
  --docker-username=user \
  --docker-password=token \
  --namespace=suricata-monitoring

# Add to deployment:
# imagePullSecrets:
# - name: regcred
```

### CrashLoopBackOff

```bash
# Check previous logs
kubectl logs <pod-name> -n suricata-monitoring --previous

# Common causes:
# - Database not ready -> wait for postgres pod
# - Config error -> check configmap
# - Missing secret -> create secret
```

### Permission Denied (Sidecar)

```bash
# Add PSS labels
kubectl label namespace suricata-monitoring \
  pod-security.kubernetes.io/enforce=privileged \
  --overwrite
```

### Cannot Connect to Service

```bash
# Test from inside cluster
kubectl run -it --rm test --image=curlimages/curl -- \
  curl http://dashboard-service.suricata-monitoring:5000/api/status

# Check endpoints
kubectl get endpoints -n suricata-monitoring

# Check service
kubectl describe svc dashboard-service -n suricata-monitoring
```

---

## 🔐 Security Tips

### Secret Management

```bash
# Generate strong password
PASSWORD=$(openssl rand -base64 32)

# Create secret
kubectl create secret generic dashboard-secrets \
  --from-literal=DB_PASSWORD="$PASSWORD" \
  --namespace=suricata-monitoring
```

**Production:** Use sealed-secrets or external-secrets operator

```bash
# Install sealed-secrets
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Create sealed secret
kubectl create secret generic dashboard-secrets \
  --from-literal=DB_PASSWORD='prod-pass' \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > sealed-secret.yaml

kubectl apply -f sealed-secret.yaml
```

### RBAC

Create least-privilege service account:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dashboard-sa
  namespace: suricata-monitoring
```

---

## 📚 Additional Resources

### Pattern Documentation
- [HostPath Pattern](../patterns/hostpath/README.md)
- [DaemonSet Pattern](../patterns/daemonset/README.md)
- [NFS Pattern](../patterns/nfs/README.md)
- [Sidecar Pattern](../patterns/sidecar/README.md)

### Wikis
- [Kubernetes Deployment Wiki](../../../wiki/containerization-kubernetes.md)
- [Main Containerization Wiki](../../../wiki/containerization.md)

### Official Docs
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [RKE2 Documentation](https://docs.rke2.io/)

---

## 💡 Quick Tips

### Useful Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
alias k='kubectl'
alias kn='kubectl config set-context --current --namespace'
alias kgp='kubectl get pods'
alias kl='kubectl logs'
alias klf='kubectl logs -f'

# Suricata specific
alias suri='kubectl get all -n suricata-monitoring'
alias suri-logs='kubectl logs -f -n suricata-monitoring -l app=suricata-dashboard'
alias suri-shell='kubectl exec -it -n suricata-monitoring $(kubectl get pod -n suricata-monitoring -l app=suricata-dashboard -o jsonpath="{.items[0].metadata.name}") -- bash'
```

### Watch Commands

```bash
# Watch pods
watch kubectl get pods -n suricata-monitoring

# Watch with color
watch -c kubectl get pods -n suricata-monitoring -o wide
```

### Stern for Multi-Pod Logs

```bash
# Install stern
brew install stern  # macOS
# or download from https://github.com/stern/stern

# Use stern
stern -n suricata-monitoring suricata-dashboard
```

---

## ✅ Quick Reference

```bash
# DEPLOYMENT
./quick-deploy.sh                      # Quick deploy (recommended)
./deploy.sh                            # Interactive deploy

# BUILD & PUSH
./build-push.sh -r ghcr.io/user -p    # Build and push

# OPERATIONS
kubectl logs -f -n suricata-monitoring -l app=suricata-dashboard
kubectl get pods -n suricata-monitoring -o wide
kubectl port-forward -n suricata-monitoring svc/dashboard-service 5000:5000

# SCALING
./scale.sh --replicas 3               # Scale to 3

# ROLLBACK
./rollback.sh                          # Rollback to previous
./rollback.sh --revision 2             # Rollback to rev 2

# DATABASE
kubectl exec -n suricata-monitoring postgres-0 -- pg_dump -U suricata suricata > backup.sql

# CLEANUP
kubectl delete -k ../patterns/hostpath/
kubectl delete namespace suricata-monitoring
```

---

**Last Updated:** 2024-12
**Maintainer:** Suricata Dashboard Team
