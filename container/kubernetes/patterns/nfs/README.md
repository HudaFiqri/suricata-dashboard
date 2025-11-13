# Pattern 3: NFS Shared Storage

## Overview

Deployment pattern dengan centralized storage via NFS. Dashboard dapat di-scale horizontal karena semua pods akses shared storage.

**Karakteristik:**
- ✅ Horizontal scaling (multiple replicas)
- ✅ Dashboard tidak tied ke specific node
- ✅ Centralized Suricata logs
- ✅ High availability
- ⚠️ Perlu NFS server setup
- ⚠️ Network latency consideration
- ⚠️ NFS server jadi SPOF (bisa di-HA)

## Architecture

```
┌─────────────────────────────────────────┐
│  NFS Server                             │
│  ├─ /exports/suricata/logs/             │
│  ├─ /exports/suricata/config/           │
│  ├─ /exports/suricata/rrd/              │
│  └─ /exports/k8s-pvs/                   │
└────────────┬────────────────────────────┘
             │ NFS Mount
             ├──────────┬──────────┐
┌────────────▼─────┐ ┌──▼─────┐ ┌──▼─────┐
│ Dashboard Pod 1  │ │ Pod 2  │ │ Pod 3  │
│ (Node 1)         │ │ (Node 2│ │ (Node 3│
└──────────────────┘ └────────┘ └────────┘
        │                 │          │
        └─────────┬───────┴──────────┘
                  │
        ┌─────────▼──────────┐
        │ PostgreSQL         │
        │ (StatefulSet)      │
        └────────────────────┘
```

## Prerequisites

### 1. NFS Server Setup

#### Option A: Dedicated NFS Server

```bash
# On NFS server (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y nfs-kernel-server

# Create export directories
sudo mkdir -p /exports/suricata/{logs,config,rrd}
sudo mkdir -p /exports/k8s-pvs

# Copy Suricata files (if Suricata on NFS server)
sudo cp -r /var/log/suricata/* /exports/suricata/logs/
sudo cp -r /etc/suricata/* /exports/suricata/config/

# Set permissions
sudo chown -R nobody:nogroup /exports/suricata/
sudo chmod -R 755 /exports/suricata/
sudo chmod -R 777 /exports/k8s-pvs/  # For dynamic provisioning

# Configure exports
sudo tee /etc/exports <<EOF
/exports/suricata/logs  *(ro,sync,no_subtree_check,no_root_squash)
/exports/suricata/config *(ro,sync,no_subtree_check,no_root_squash)
/exports/suricata/rrd   *(rw,sync,no_subtree_check,no_root_squash)
/exports/k8s-pvs        *(rw,sync,no_subtree_check,no_root_squash)
EOF

# Apply exports
sudo exportfs -ra

# Start NFS server
sudo systemctl enable nfs-kernel-server
sudo systemctl start nfs-kernel-server

# Verify exports
sudo exportfs -v
showmount -e localhost
```

#### Option B: TrueNAS/FreeNAS

1. Create datasets:
   - `tank/suricata/logs`
   - `tank/suricata/config`
   - `tank/suricata/rrd`
   - `tank/k8s-pvs`

2. Configure NFS shares:
   - Enable NFSv3 and NFSv4
   - Set permissions: read-only untuk logs/config, read-write untuk rrd/k8s-pvs
   - Add allowed networks/IPs

3. Test dari client:
```bash
showmount -e truenas-ip
```

### 2. Kubernetes Nodes NFS Client

Install NFS client tools pada semua K8s nodes:

```bash
# Ubuntu/Debian
sudo apt-get install -y nfs-common

# RHEL/CentOS
sudo yum install -y nfs-utils

# Test mount dari node
sudo mount -t nfs nfs-server.example.com:/exports/suricata/logs /mnt
ls -la /mnt
sudo umount /mnt
```

### 3. Test Network Connectivity

```bash
# From K8s nodes
ping nfs-server.example.com

# Test NFS ports
nc -zv nfs-server.example.com 2049
nc -zv nfs-server.example.com 111

# Verify mount works
sudo mount -t nfs -o ro nfs-server.example.com:/exports/suricata/logs /mnt
ls -la /mnt
sudo umount /mnt
```

## Deployment

### Method 1: Direct NFS Mounts (Simple)

#### Step 1: Update NFS Server Settings

Edit `deployment.yaml` dan ubah NFS server:

```yaml
volumes:
- name: suricata-logs-nfs
  nfs:
    server: 192.168.1.100  # Your NFS server IP/hostname
    path: /exports/suricata/logs
    readOnly: true
```

#### Step 2: Deploy

```bash
cd container/kubernetes/patterns/nfs

# Edit deployment.yaml first!
# Update all NFS server references

# Deploy
kubectl apply -k .
```

#### Step 3: Verify

```bash
# Check pods
kubectl get pods -n suricata-monitoring -o wide

# Check NFS mounts inside pod
kubectl exec -n suricata-monitoring <pod-name> -- df -h
kubectl exec -n suricata-monitoring <pod-name> -- ls -la /var/log/suricata/
```

### Method 2: Dynamic Provisioning (Advanced)

#### Step 1: Install NFS Provisioner

```bash
# Edit nfs-provisioner.yaml
# Update NFS_SERVER and NFS_PATH

# Deploy provisioner
kubectl apply -f nfs-provisioner.yaml

# Verify provisioner
kubectl get pods -n suricata-monitoring -l app=nfs-client-provisioner
kubectl get storageclass nfs-client
```

#### Step 2: Update Kustomization

Edit `kustomization.yaml`, uncomment:

```yaml
resources:
- nfs-provisioner.yaml
```

#### Step 3: Deploy

```bash
kubectl apply -k .
```

### Method 3: Helm (Recommended for Production)

```bash
# Add NFS provisioner helm repo
helm repo add nfs-subdir-external-provisioner \
  https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner/

# Install NFS provisioner
helm install nfs-provisioner \
  nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
  --namespace suricata-monitoring \
  --create-namespace \
  --set nfs.server=nfs-server.example.com \
  --set nfs.path=/exports/k8s-pvs \
  --set storageClass.name=nfs-client

# Verify
kubectl get storageclass nfs-client
```

Then deploy dashboard:

```bash
kubectl apply -k .
```

## Scaling

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: dashboard-hpa
  namespace: suricata-monitoring
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: suricata-dashboard
  minReplicas: 2
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

Apply:

```bash
kubectl apply -f hpa.yaml
kubectl get hpa -n suricata-monitoring -w
```

### Manual Scaling

```bash
# Scale up
kubectl scale deployment suricata-dashboard --replicas=5 -n suricata-monitoring

# Scale down
kubectl scale deployment suricata-dashboard --replicas=2 -n suricata-monitoring

# Check status
kubectl get deployment suricata-dashboard -n suricata-monitoring
```

## Load Balancing

### Session Affinity

Ingress sudah configured dengan cookie-based session affinity:

```yaml
annotations:
  nginx.ingress.kubernetes.io/affinity: "cookie"
  nginx.ingress.kubernetes.io/session-cookie-name: "dashboard-route"
```

User akan always di-route ke same pod selama cookie valid.

### Without Session Affinity

Jika aplikasi fully stateless, bisa remove session affinity untuk better load distribution.

## High Availability

### NFS Server HA (Optional)

**Option A: DRBD + Pacemaker**

```bash
# Two NFS servers dengan DRBD replication
# Pacemaker manages failover
# Virtual IP untuk client access
```

**Option B: GlusterFS**

```bash
# Deploy GlusterFS cluster
# NFS-Ganesha untuk NFS access layer
# Replication across nodes
```

**Option C: Cloud NFS**

- AWS EFS
- Azure Files
- GCP Filestore

### PostgreSQL HA

Deploy PostgreSQL dengan replication:

```yaml
# Use PostgreSQL operator
# Or cloud managed: RDS, Cloud SQL, Azure Database
```

## Monitoring

### NFS Performance

```bash
# Monitor NFS stats on server
nfsstat -s

# Monitor on clients
nfsstat -c

# Check mount options
mount | grep nfs
```

### Dashboard Metrics

```bash
# Check replica status
kubectl get deployment suricata-dashboard -n suricata-monitoring

# Monitor pod distribution
kubectl get pods -n suricata-monitoring -o wide

# Resource usage
kubectl top pods -n suricata-monitoring
```

## Troubleshooting

### NFS Mount Fails

```bash
# Check from pod
kubectl describe pod <pod-name> -n suricata-monitoring

# Common errors:
# - "mount.nfs: Connection refused" -> NFS server not running
# - "mount.nfs: access denied" -> Export permissions issue
# - "mount.nfs: No route to host" -> Network/firewall issue

# Debug
kubectl run -it --rm debug --image=nicolaka/netshoot -- bash
# Inside debug pod:
showmount -e nfs-server.example.com
mount -t nfs nfs-server.example.com:/exports/suricata/logs /mnt
```

### Slow Performance

```bash
# Check NFS mount options
kubectl exec -n suricata-monitoring <pod-name> -- mount | grep nfs

# Recommended mount options:
# - vers=4 (NFSv4)
# - rsize=1048576,wsize=1048576 (large read/write buffers)
# - hard (don't give up on errors)
# - timeo=600 (longer timeout)

# Update in deployment.yaml:
nfs:
  server: nfs-server.example.com
  path: /exports/suricata/logs
  readOnly: true
  # Add mount options (requires NFSv4):
  # mountOptions:
  #   - vers=4
  #   - rsize=1048576
  #   - wsize=1048576
```

### Split Brain (Multiple Replicas Writing)

Jika multiple pods menulis ke same files:

```bash
# RRD files corruption possible jika tidak ada file locking

# Solution 1: Use NFS file locking
# - Ensure rpc.lockd running on NFS server
# - Use hard mounts

# Solution 2: Application-level locking
# - Implement leader election
# - Only one pod writes RRD

# Solution 3: Pod affinity
# - Pin specific tasks to specific pods
```

### Permission Denied

```bash
# Check UID/GID in pod
kubectl exec -n suricata-monitoring <pod-name> -- id

# Should be uid=1000

# Check NFS export options
# On NFS server:
sudo exportfs -v

# Should NOT have root_squash for uid/gid mapping to work
# Use: no_root_squash or all_squash,anonuid=1000,anongid=1000
```

## Performance Tuning

### NFS Server

```bash
# Increase NFS threads
sudo sed -i 's/RPCNFSDCOUNT=8/RPCNFSDCOUNT=32/' /etc/default/nfs-kernel-server
sudo systemctl restart nfs-kernel-server

# Async vs Sync
# async = faster but data loss risk on crash
# sync = safer but slower
# Recommended: sync for logs (read-only anyway), async for RRD if acceptable
```

### Network

```bash
# Use jumbo frames jika network support
# Set MTU to 9000 on network interfaces

# QoS for NFS traffic
# Prioritize NFS traffic (port 2049)
```

### Caching

```bash
# Enable client-side caching
# Mount options: ac,acregmin=3,acregmax=60
```

## Security

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
  - to:  # Allow NFS
    - ipBlock:
        cidr: 192.168.1.0/24  # Your NFS subnet
    ports:
    - protocol: TCP
      port: 2049
```

### NFS Kerberos (Enterprise)

```bash
# Setup Kerberos for NFS authentication
# Requires KDC infrastructure
# More secure than IP-based access control
```

## Backup Strategy

### NFS Server Backups

```bash
# Snapshot-based (ZFS/Btrfs)
zfs snapshot tank/suricata@daily

# rsync-based
rsync -av /exports/suricata/ backup-server:/backup/suricata/

# Database dumps
kubectl exec -n suricata-monitoring <postgres-pod> -- \
  pg_dump -U suricata suricata | gzip > backup.sql.gz
```

## Cleanup

```bash
kubectl delete -k .

# On NFS server
sudo systemctl stop nfs-kernel-server
sudo umount /exports/suricata/*
sudo rm -rf /exports/suricata/
```

## Production Checklist

- [ ] NFS server HA configured
- [ ] NFS client tools on all nodes
- [ ] Network tested (latency, bandwidth)
- [ ] Export permissions configured correctly
- [ ] Mount options optimized
- [ ] Firewall rules allow NFS traffic
- [ ] Backup strategy implemented
- [ ] Monitoring setup for NFS
- [ ] Session affinity configured (if needed)
- [ ] HPA tested and tuned
- [ ] NetworkPolicy applied
- [ ] TLS/HTTPS configured

## Next Steps

- Setup Prometheus metrics for NFS performance
- Implement automated backup/restore
- Configure alerting for NFS issues
- Consider service mesh (Istio/Linkerd)
- Setup distributed tracing
