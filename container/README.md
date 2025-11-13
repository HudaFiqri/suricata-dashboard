# Suricata Dashboard - Container Deployment

Comprehensive containerization untuk Suricata Dashboard dengan support Docker dan Kubernetes.

## 📦 What's Inside

```
container/
├── docker/                      # Docker & Docker Compose
│   ├── Dockerfile              # Production-ready Docker image
│   ├── docker-compose.yml      # Compose stack (Dashboard + PostgreSQL)
│   ├── .dockerignore           # Build optimization
│   ├── .env.example            # Environment template
│   └── README.md               # Docker documentation
│
├── kubernetes/                  # Kubernetes manifests
│   ├── base/                   # Common resources
│   │   ├── namespace.yaml
│   │   ├── configmap.yaml
│   │   ├── secret.yaml
│   │   ├── postgres-statefulset.yaml
│   │   └── dashboard-service.yaml
│   │
│   ├── patterns/               # 4 Deployment patterns
│   │   ├── hostpath/          # Pattern 1: Single node with hostPath
│   │   ├── daemonset/         # Pattern 2: Multi-node distributed
│   │   ├── nfs/               # Pattern 3: Shared storage
│   │   └── sidecar/           # Pattern 4: Fully containerized
│   │
│   └── README.md               # Kubernetes documentation
│
├── WIKI.md                      # Complete wiki documentation
└── README.md                    # This file
```

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended for Testing)

```bash
cd docker/
cp .env.example .env
# Edit .env file
docker-compose up -d
```

**Access:** http://localhost:5000

**[Full Docker Documentation →](docker/README.md)**

---

### Option 2: Kubernetes/RKE2 (Production)

Choose deployment pattern based on your setup:

#### Pattern 1: HostPath (Single Node)
```bash
cd kubernetes/patterns/hostpath/
kubectl apply -k .
```

#### Pattern 2: DaemonSet (Multi-Node)
```bash
cd kubernetes/patterns/daemonset/
kubectl apply -k .
```

#### Pattern 3: NFS (Scalable)
```bash
cd kubernetes/patterns/nfs/
kubectl apply -k .
```

#### Pattern 4: Sidecar (Containerized Suricata)
```bash
cd kubernetes/patterns/sidecar/
kubectl apply -k .
```

**[Full Kubernetes Documentation →](kubernetes/README.md)**

---

## 🤔 Which Deployment Method?

### Docker Compose

**Use when:**
- ✅ Single server deployment
- ✅ Development/testing environment
- ✅ Quick POC/demo
- ✅ Simple setup preferred
- ✅ No Kubernetes cluster available

**Benefits:**
- Simple configuration
- Fast deployment
- Easy troubleshooting
- Lower resource requirements

**Limitations:**
- No high availability
- Manual scaling
- Single host only
- Basic orchestration

**[Docker Documentation →](docker/README.md)**

---

### Kubernetes

**Use when:**
- ✅ Production deployment
- ✅ Need high availability
- ✅ Multi-node cluster
- ✅ Want auto-scaling
- ✅ Advanced orchestration needed

**Benefits:**
- High availability
- Horizontal scaling
- Self-healing
- Advanced networking
- Service discovery
- Declarative configuration

**Deployment Patterns:**

| Pattern | Use Case | Complexity |
|---------|----------|------------|
| **HostPath** | Suricata on host, single node | ⭐ Simple |
| **DaemonSet** | Suricata on multiple nodes | ⭐⭐ Medium |
| **NFS** | Centralized logs, scalable | ⭐⭐⭐ Advanced |
| **Sidecar** | Fully containerized | ⭐⭐⭐ Advanced |

**[Kubernetes Documentation →](kubernetes/README.md)**

---

## 📋 Prerequisites

### For Docker

- Docker Engine 20.10+
- Docker Compose v2.0+
- 2GB RAM minimum
- 10GB disk space

### For Kubernetes

- Kubernetes 1.24+ (RKE2, K3s, etc.)
- kubectl configured
- 4GB RAM minimum per node
- 20GB disk space
- Container registry access

### Common Requirements

- Suricata installed (unless using sidecar pattern)
- PostgreSQL or MySQL (included in deployments)
- Network access to Suricata logs

---

## 🏗️ Architecture Comparison

### Docker Compose Architecture

```
┌────────────────────────────────────┐
│  Docker Host                       │
│                                    │
│  ┌──────────────────────────────┐ │
│  │  Docker Network              │ │
│  │                              │ │
│  │  ┌────────┐    ┌──────────┐ │ │
│  │  │Dashboard│◄───┤PostgreSQL│ │ │
│  │  │ :5000  │    │  :5432   │ │ │
│  │  └───▲────┘    └──────────┘ │ │
│  │      │                       │ │
│  └──────┼───────────────────────┘ │
│         │                         │
│  ┌──────▼─────────────────────┐  │
│  │  Host Volumes (Bind Mount) │  │
│  │  /var/log/suricata         │  │
│  │  /etc/suricata             │  │
│  └────────────────────────────┘  │
└────────────────────────────────────┘
```

### Kubernetes Architecture (Example: HostPath)

```
┌────────────────────────────────────────┐
│  Kubernetes Cluster                    │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │  Namespace: suricata-monitoring  │ │
│  │                                  │ │
│  │  ┌────────────┐  ┌────────────┐ │ │
│  │  │ Dashboard  │  │ PostgreSQL │ │ │
│  │  │    Pod     │◄─┤ StatefulSet│ │ │
│  │  └─────┬──────┘  └────────────┘ │ │
│  │        │                         │ │
│  │  ┌─────▼──────┐                 │ │
│  │  │  Ingress   │                 │ │
│  │  └────────────┘                 │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │  Persistent Volumes              │ │
│  │  - Database (PVC)                │ │
│  │  - App data (PVC)                │ │
│  │  - Suricata logs (hostPath)      │ │
│  └──────────────────────────────────┘ │
└────────────────────────────────────────┘
```

---

## 🔐 Security Considerations

### Docker

- ✅ Non-root user (uid 1000)
- ✅ Read-only Suricata mounts
- ✅ Network isolation
- ⚠️ Secure .env file permissions
- ⚠️ Use secrets management in production

### Kubernetes

- ✅ RBAC policies
- ✅ NetworkPolicy support
- ✅ Pod Security Standards
- ✅ Secret encryption
- ✅ Service mesh ready
- ⚠️ Use Sealed Secrets or External Secrets Operator

**Security Checklist:**
- [ ] Change default passwords
- [ ] Use HTTPS/TLS
- [ ] Restrict network access
- [ ] Regular security updates
- [ ] Audit logs enabled
- [ ] Backup encryption

---

## 📊 Performance & Scaling

### Docker Compose

**Scaling:**
```bash
# Scale dashboard replicas (manual)
docker-compose up -d --scale dashboard=3
```

**Resource Limits:**
```yaml
services:
  dashboard:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
```

### Kubernetes

**Horizontal Pod Autoscaler:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: dashboard-hpa
spec:
  scaleTargetRef:
    kind: Deployment
    name: suricata-dashboard
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Vertical Pod Autoscaler:**
Automatically adjust resource requests/limits.

---

## 🔧 Configuration Management

### Docker

Environment variables via `.env` file:
```ini
FLASK_PORT=5000
DB_PASSWORD=changeme
SURICATA_LOG_DIR=/var/log/suricata
```

### Kubernetes

ConfigMaps and Secrets:
```bash
# ConfigMap for non-sensitive config
kubectl create configmap dashboard-config \
  --from-file=config.yaml

# Secret for sensitive data
kubectl create secret generic dashboard-secrets \
  --from-literal=DB_PASSWORD='secure-password'
```

---

## 🧪 Testing & Development

### Local Development with Docker

```bash
cd docker/
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Kubernetes Development

```bash
# Use minikube or kind for local testing
minikube start

# Deploy to local cluster
kubectl apply -k kubernetes/patterns/hostpath/

# Port-forward for access
kubectl port-forward svc/dashboard-service 5000:5000
```

---

## 📈 Monitoring & Observability

### Docker

**Logs:**
```bash
docker-compose logs -f dashboard
docker-compose logs -f postgres
```

**Metrics:**
```bash
docker stats
```

**Health Checks:**
```bash
docker-compose ps
curl http://localhost:5000/api/status
```

### Kubernetes

**Logs:**
```bash
kubectl logs -f deployment/suricata-dashboard -n suricata-monitoring
stern -n suricata-monitoring suricata  # Multi-pod logs
```

**Metrics (Prometheus):**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: dashboard-metrics
spec:
  selector:
    matchLabels:
      app: suricata-dashboard
```

**Tracing (Jaeger/Tempo):**
Integration via OpenTelemetry

---

## 🔄 CI/CD Integration

### Build Pipeline

```yaml
# .github/workflows/build.yml
name: Build Container Image

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: |
          docker build -f container/docker/Dockerfile \
            -t ghcr.io/${{ github.repository }}:${{ github.sha }} .

      - name: Push image
        run: |
          docker push ghcr.io/${{ github.repository }}:${{ github.sha }}
```

### Deployment Pipeline

```yaml
# Deploy to Kubernetes
- name: Deploy to K8s
  run: |
    kubectl set image deployment/suricata-dashboard \
      dashboard=ghcr.io/${{ github.repository }}:${{ github.sha }} \
      -n suricata-monitoring
```

---

## 📚 Additional Documentation

### Docker
- [Docker Quick Start](docker/README.md)
- [Docker Compose Reference](docker/docker-compose.yml)
- [Environment Variables](docker/.env.example)

### Kubernetes
- [Kubernetes Overview](kubernetes/README.md)
- [Pattern 1: HostPath](kubernetes/patterns/hostpath/README.md)
- [Pattern 2: DaemonSet](kubernetes/patterns/daemonset/README.md)
- [Pattern 3: NFS](kubernetes/patterns/nfs/README.md)
- [Pattern 4: Sidecar](kubernetes/patterns/sidecar/README.md)

### Wiki
- [Complete Wiki Documentation](WIKI.md)

---

## 🆘 Troubleshooting

### Common Issues

| Issue | Docker Solution | Kubernetes Solution |
|-------|----------------|---------------------|
| Cannot connect to DB | Check `docker-compose ps` | Check `kubectl get pods` |
| Logs not visible | Check volume mounts | Check hostPath permissions |
| Port already in use | Change `FLASK_PORT` in .env | Change NodePort in service |
| Out of memory | Increase Docker memory | Adjust resource limits |
| Image pull fails | Check registry auth | Create imagePullSecret |

### Debug Commands

**Docker:**
```bash
docker-compose logs -f
docker exec -it <container> bash
docker inspect <container>
```

**Kubernetes:**
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name> -f
kubectl exec -it <pod-name> -- bash
kubectl get events --sort-by='.lastTimestamp'
```

---

## 🎓 Best Practices

### Development
- Use docker-compose for local development
- Version control all configurations
- Use .env files (never commit secrets!)
- Test locally before deploying

### Staging
- Use Kubernetes with dev overlay
- Test scaling and failover
- Validate monitoring and alerts
- Load testing

### Production
- Use Kubernetes with prod overlay
- Implement proper secret management
- Enable monitoring and logging
- Setup automated backups
- Document runbooks
- Configure alerting
- Implement disaster recovery

---

## 🔗 Links

- [Main Project README](../README.md)
- [Docker Hub](https://hub.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/)
- [RKE2 Documentation](https://docs.rke2.io/)
- [Suricata Documentation](https://suricata.readthedocs.io/)

---

## 📝 License

Educational and defensive security purposes only.

---

**Need Help?**
- Check pattern-specific READMEs
- Review troubleshooting sections
- Open an issue on GitHub
- Consult the wiki documentation
