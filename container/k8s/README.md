# Kubernetes Deployment

Deploy Suricata Multi-Agent Dashboard on Kubernetes.

## Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Persistent volume provisioner (for databases)
- Ingress controller (nginx recommended)
- Optional: cert-manager for TLS

## Quick Deployment

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check status
kubectl get pods -n suricata
kubectl get svc -n suricata
```

## Step-by-Step Deployment

### 1. Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 2. Deploy PostgreSQL

```bash
kubectl apply -f k8s/postgresql.yaml

# Wait for ready
kubectl wait --for=condition=ready pod -l app=postgresql -n suricata --timeout=300s

# Verify
kubectl logs -n suricata statefulset/postgresql
```

### 3. Deploy MongoDB

```bash
kubectl apply -f k8s/mongodb.yaml

# Wait for ready
kubectl wait --for=condition=ready pod -l app=mongodb -n suricata --timeout=300s
```

### 4. Build and Push Dashboard Image

```bash
# Build image
docker build -t your-registry/suricata-dashboard:latest .

# Push to registry
docker push your-registry/suricata-dashboard:latest

# Update k8s/dashboard.yaml with your image
sed -i 's|suricata-dashboard:latest|your-registry/suricata-dashboard:latest|g' k8s/dashboard.yaml
```

### 5. Deploy Dashboard

```bash
kubectl apply -f k8s/dashboard.yaml

# Wait for ready
kubectl wait --for=condition=ready pod -l app=dashboard -n suricata --timeout=300s

# Check logs
kubectl logs -n suricata deployment/dashboard -f
```

### 6. Access Dashboard

**Via LoadBalancer:**
```bash
kubectl get svc dashboard -n suricata
# Access via EXTERNAL-IP
```

**Via Ingress:**
```bash
# Update k8s/dashboard.yaml with your domain
kubectl apply -f k8s/dashboard.yaml

# Access via https://suricata.example.com
```

**Via Port Forward (for testing):**
```bash
kubectl port-forward -n suricata svc/dashboard 5000:80

# Access at http://localhost:5000
```

## Post-Deployment

### Run Database Migrations

```bash
# Exec into dashboard pod
kubectl exec -it -n suricata deployment/dashboard -- bash

# Run migrations
cd /app && python bin/migrations/migrate.py up
```

### Create Admin User

```bash
kubectl exec -it -n suricata deployment/dashboard -- \
    python bin/create_user.py admin yourpassword admin
```

### Scale Dashboard

```bash
# Scale to 5 replicas
kubectl scale deployment dashboard -n suricata --replicas=5

# Autoscale
kubectl autoscale deployment dashboard -n suricata --min=3 --max=10 --cpu-percent=80
```

## Configuration

### Update Secrets

```bash
# Edit secrets
kubectl edit secret dashboard-secret -n suricata

# Or delete and recreate
kubectl delete secret dashboard-secret -n suricata
kubectl create secret generic dashboard-secret -n suricata \
    --from-literal=SECRET_KEY='your-secret-key' \
    --from-literal=JWT_SECRET_KEY='your-jwt-key' \
    --from-literal=POSTGRES_PASSWORD='your-postgres-password'
```

### Update ConfigMap

```bash
kubectl edit configmap dashboard-config -n suricata

# Restart pods to apply
kubectl rollout restart deployment dashboard -n suricata
```

## Monitoring

### Check Logs

```bash
# Dashboard logs
kubectl logs -n suricata deployment/dashboard -f

# PostgreSQL logs
kubectl logs -n suricata statefulset/postgresql -f

# MongoDB logs
kubectl logs -n suricata statefulset/mongodb -f

# All pods
kubectl logs -n suricata --all-containers=true -l app=dashboard -f
```

### Health Checks

```bash
# Dashboard health
kubectl exec -n suricata deployment/dashboard -- \
    curl http://localhost:5000/api/v1/health/full

# Database connections
kubectl get pods -n suricata -o wide
```

## Backup & Restore

### Backup PostgreSQL

```bash
# Exec into pod
kubectl exec -it -n suricata statefulset/postgresql -- bash

# Backup
pg_dump -U suricata suricata_dashboard > /tmp/backup.sql

# Copy from pod
kubectl cp suricata/postgresql-0:/tmp/backup.sql ./backup-$(date +%Y%m%d).sql
```

### Backup MongoDB

```bash
kubectl exec -it -n suricata statefulset/mongodb -- \
    mongodump --db suricata --out /tmp/backup

kubectl cp suricata/mongodb-0:/tmp/backup ./mongodb-backup-$(date +%Y%m%d)
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod -n suricata <pod-name>

# Check events
kubectl get events -n suricata --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# Test PostgreSQL
kubectl exec -it -n suricata deployment/dashboard -- \
    psql -h postgresql -U suricata -d suricata_dashboard

# Test MongoDB
kubectl exec -it -n suricata deployment/dashboard -- \
    mongosh mongodb://mongodb:27017/suricata
```

### Persistent Volume Issues

```bash
# Check PVCs
kubectl get pvc -n suricata

# Check PVs
kubectl get pv

# Describe PVC
kubectl describe pvc postgresql-pvc -n suricata
```

## Clean Up

```bash
# Delete all resources
kubectl delete namespace suricata

# Or delete individually
kubectl delete -f k8s/
```

## Production Recommendations

1. **Storage Class**: Use SSD-backed storage for databases
2. **Resource Limits**: Adjust based on load
3. **Secrets**: Use external secret management (Vault, etc.)
4. **TLS**: Enable TLS with cert-manager
5. **Monitoring**: Deploy Prometheus + Grafana
6. **Logging**: Use EFK/ELK stack
7. **Backup**: Automated daily backups
8. **High Availability**: Run 3+ dashboard replicas
9. **Network Policy**: Restrict pod-to-pod communication
10. **Security Context**: Run as non-root user

## Helm Chart (Optional)

For easier deployment, consider creating a Helm chart:

```bash
helm create suricata-dashboard
# Customize values.yaml
helm install suricata-dashboard ./suricata-dashboard -n suricata
```
