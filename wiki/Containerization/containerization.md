# Containerization - Suricata Dashboard

Complete containerization guide untuk Suricata Dashboard dengan support Docker dan Kubernetes.

## 📋 Overview

Suricata Dashboard dapat di-deploy menggunakan container technology untuk portabilitas, isolasi, dan orchestration yang lebih baik.

**Deployment Options:**
1. **Docker / Docker Compose** - Simple, single-host deployment
2. **Kubernetes / RKE2** - Production-grade, multi-node orchestration

---

## 🐳 Docker Deployment

Deploy menggunakan Docker Compose untuk single-host setup.

### Quick Start

```bash
cd container/docker
cp .env.example .env
# Edit .env file
docker-compose up -d
# Access: http://localhost:5000
```

### Architecture

```
┌────────────────────────────────────┐
│  Docker Host                       │
│  ┌──────────────────────────────┐ │
│  │  Dashboard Container         │ │
│  │  Port: 5000                  │ │
│  └─────────┬────────────────────┘ │
│            │                       │
│  ┌─────────▼────────────────────┐ │
│  │  PostgreSQL Container        │ │
│  │  Port: 5432 (internal)       │ │
│  └──────────────────────────────┘ │
└────────────────────────────────────┘
```

### Features

- ✅ Simple setup dengan docker-compose
- ✅ Production-ready Dockerfile
- ✅ Non-root user (security)
- ✅ Health checks included
- ✅ PostgreSQL database included
- ✅ Volume persistence
- ✅ Easy configuration via .env

### Use Cases

**Perfect for:**
- Single server deployment
- Development/testing
- Quick POC/demo
- Simple production setup
- No Kubernetes available

**Not ideal for:**
- Multi-node deployment
- High availability requirements
- Auto-scaling needs
- Complex orchestration

### 📖 Full Documentation

**→ [Docker Deployment Wiki](containerization-docker.md)**

Includes:
- Detailed installation guide
- Configuration reference
- Database operations
- Troubleshooting
- Best practices
- Migration guide

---

## ☸️ Kubernetes Deployment

Deploy di Kubernetes cluster (RKE2, K3s, EKS, GKE, AKS, dll.) dengan 4 deployment patterns.

### Deployment Patterns

#### Pattern 1: HostPath (Single Node)
**Use Case:** Suricata di host, dashboard mount logs via hostPath

```bash
cd container/kubernetes/patterns/hostpath
kubectl apply -k .
```

- ✅ Simple setup
- ✅ Low latency
- ⚠️ Single node only

---

#### Pattern 2: DaemonSet (Multi-Node)
**Use Case:** Suricata di multiple nodes, dashboard per node

```bash
cd container/kubernetes/patterns/daemonset
kubectl apply -k .
```

- ✅ Distributed monitoring
- ✅ High availability
- ⚠️ Independent dashboards

---

#### Pattern 3: NFS (Shared Storage)
**Use Case:** Centralized logs, scalable dashboard

```bash
cd container/kubernetes/patterns/nfs
kubectl apply -k .
```

- ✅ Horizontal scaling
- ✅ Load balancing
- ⚠️ Requires NFS server

---

#### Pattern 4: Sidecar (Containerized)
**Use Case:** Suricata + Dashboard dalam 1 pod

```bash
cd container/kubernetes/patterns/sidecar
kubectl apply -k .
```

- ✅ Fully portable
- ✅ No host dependency
- ⚠️ Needs privileges

---

### Pattern Selection Guide

| Scenario | Recommended Pattern |
|----------|---------------------|
| RKE2 single node | **HostPath** |
| RKE2 multi-node | **DaemonSet** |
| Production HA | **NFS** |
| POC/Demo | **Sidecar** |
| Cloud deployment | **NFS** or **Sidecar** |

### Features

- ✅ 4 flexible deployment patterns
- ✅ Kustomize support
- ✅ Resource limits & requests
- ✅ Liveness & readiness probes
- ✅ StatefulSet PostgreSQL
- ✅ Ingress configured
- ✅ RKE2 optimized
- ✅ Security best practices

### Use Cases

**Perfect for:**
- Production deployment
- High availability needs
- Multi-node clusters
- Auto-scaling requirements
- Advanced orchestration
- Cloud-native architecture

**Not ideal for:**
- Simple single-host setup
- Quick testing
- Minimal infrastructure
- Learning/POC (Docker easier)

### 📖 Full Documentation

**→ [Kubernetes Deployment Wiki](containerization-kubernetes.md)**

Includes:
- Pattern selection guide
- Detailed setup per pattern
- RKE2-specific instructions
- Security configuration
- Monitoring & logging
- Troubleshooting
- Production checklist

---

## 🤔 Docker vs Kubernetes

### When to Use Docker

✅ **Use Docker when:**
- Single server deployment
- Development/testing
- Quick setup needed
- Simple architecture
- No HA requirements
- Team not familiar with K8s

### When to Use Kubernetes

✅ **Use Kubernetes when:**
- Production environment
- Multi-node cluster
- High availability needed
- Auto-scaling required
- Complex networking
- Team experienced with K8s
- Cloud deployment

### Comparison Table

| Feature | Docker | Kubernetes |
|---------|--------|------------|
| **Setup Complexity** | ⭐ Simple | ⭐⭐⭐ Complex |
| **Deployment Time** | Minutes | 30-60 minutes |
| **High Availability** | ❌ No | ✅ Yes |
| **Auto-scaling** | ❌ No | ✅ Yes |
| **Self-healing** | ⚠️ Basic | ✅ Advanced |
| **Load Balancing** | Manual | ✅ Built-in |
| **Resource Limits** | ✅ Yes | ✅ Advanced |
| **Rolling Updates** | Manual | ✅ Automatic |
| **Multi-node** | ❌ No | ✅ Yes |
| **Monitoring** | Basic | ✅ Advanced |
| **Best For** | Dev/Test | Production |

---

## 📦 What's Included

### Container Directory Structure

```
container/
├── README.md                    # Overview & comparison
│
├── docker/                      # Docker deployment
│   ├── Dockerfile              # Production image
│   ├── docker-compose.yml      # Compose stack
│   ├── .dockerignore           # Build optimization
│   ├── .env.example            # Config template
│   └── README.md               # Docker docs
│
└── kubernetes/                  # K8s deployment
    ├── README.md               # K8s overview
    │
    ├── base/                   # Common resources
    │   ├── namespace.yaml
    │   ├── configmap.yaml
    │   ├── secret.yaml
    │   ├── postgres-statefulset.yaml
    │   └── dashboard-service.yaml
    │
    └── patterns/               # 4 patterns
        ├── hostpath/          # Single node
        ├── daemonset/         # Multi-node
        ├── nfs/               # Shared storage
        └── sidecar/           # Containerized
```

---

## 🚀 Quick Links

### Documentation
- **[Docker Wiki →](containerization-docker.md)** - Complete Docker guide
- **[Kubernetes Wiki →](containerization-kubernetes.md)** - Complete K8s guide

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
- 4GB RAM per node
- 20GB disk space
- Container registry access

### Common Requirements
- Suricata installed (unless using sidecar)
- PostgreSQL or MySQL (included)
- Network access to Suricata logs

---

## 🔒 Security Considerations

### Docker Security
- ✅ Non-root container user
- ✅ Read-only mounts for Suricata
- ✅ Network isolation
- ✅ Secret management via .env
- ⚠️ Secure .env permissions

### Kubernetes Security
- ✅ RBAC policies
- ✅ NetworkPolicy support
- ✅ Pod Security Standards
- ✅ Secret encryption
- ✅ Service mesh ready
- ✅ Sealed Secrets support

**Security Checklist:**
- [ ] Change default passwords
- [ ] Use HTTPS/TLS
- [ ] Restrict network access
- [ ] Regular security updates
- [ ] Audit logs enabled
- [ ] Backup encryption

---

## 📝 Changelog

- **2024-12**: Initial containerization documentation
- Split into Docker and Kubernetes wikis
- Added 4 Kubernetes patterns
- RKE2-specific optimizations
- Security best practices
- Production checklists

---

**Last Updated:** 2024-12
**Maintainer:** Suricata Dashboard Team

**Quick Navigation:**
- [Docker Deployment →](containerization-docker.md)
- [Kubernetes Deployment →](containerization-kubernetes.md)
