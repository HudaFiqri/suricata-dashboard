#!/bin/bash

# Quick Deploy - No prompts, just deploy!
# Usage: ./quick-deploy.sh [pattern] [options]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_DIR="$(dirname "$SCRIPT_DIR")"
PATTERNS_DIR="$K8S_DIR/patterns"

# Default values
PATTERN="hostpath"
SKIP_SECRET=false
SKIP_LABELS=false
DB_PASSWORD=""

show_usage() {
    cat << EOF
Quick Deploy - Deploy Kubernetes pattern instantly!

Usage: $0 [PATTERN] [OPTIONS]

PATTERNS:
    hostpath    Single node with local Suricata (default)
    daemonset   Multi-node distributed monitoring
    nfs         Shared storage, scalable
    sidecar     Fully containerized

OPTIONS:
    --skip-secret       Skip secret creation
    --skip-labels       Skip node labeling
    --password PASS     Database password (auto-generated if not provided)
    -h, --help          Show this help

EXAMPLES:
    # Quick deploy hostpath
    $0

    # Deploy daemonset
    $0 daemonset

    # Deploy NFS with custom password
    $0 nfs --password mySecurePassword

    # Deploy sidecar, skip secret (already exists)
    $0 sidecar --skip-secret

EOF
}

parse_args() {
    # First arg is pattern if not starting with --
    if [[ $# -gt 0 && ! "$1" =~ ^-- ]]; then
        PATTERN="$1"
        shift
    fi

    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-secret)
                SKIP_SECRET=true
                shift
                ;;
            --skip-labels)
                SKIP_LABELS=true
                shift
                ;;
            --password)
                DB_PASSWORD="$2"
                shift 2
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Validate pattern
    if [[ ! -d "$PATTERNS_DIR/$PATTERN" ]]; then
        print_error "Invalid pattern: $PATTERN"
        print_info "Available: hostpath, daemonset, nfs, sidecar"
        exit 1
    fi
}

quick_check() {
    # Quick kubectl check
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found!"
        exit 1
    fi

    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to cluster!"
        exit 1
    fi

    print_success "Connected to: $(kubectl config current-context)"
}

create_secret() {
    if [ "$SKIP_SECRET" = true ]; then
        print_info "Skipping secret creation"
        return
    fi

    print_info "Creating secret..."

    # Generate password if not provided
    if [ -z "$DB_PASSWORD" ]; then
        DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        print_info "Generated password: $DB_PASSWORD"
    fi

    kubectl create secret generic dashboard-secrets \
        --from-literal=DB_PASSWORD="$DB_PASSWORD" \
        --namespace=suricata-monitoring \
        --dry-run=client -o yaml | kubectl apply -f - > /dev/null 2>&1

    print_success "Secret created"
}

label_nodes() {
    if [ "$SKIP_LABELS" = true ]; then
        print_info "Skipping node labeling"
        return
    fi

    if [[ "$PATTERN" != "hostpath" && "$PATTERN" != "daemonset" ]]; then
        return
    fi

    # Check if any nodes already labeled
    LABELED=$(kubectl get nodes -l suricata=enabled --no-headers 2>/dev/null | wc -l)
    if [ "$LABELED" -gt 0 ]; then
        print_success "$LABELED node(s) already labeled"
        return
    fi

    print_info "Labeling first available node..."
    FIRST_NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
    kubectl label nodes "$FIRST_NODE" suricata=enabled --overwrite > /dev/null 2>&1
    print_success "Labeled node: $FIRST_NODE"
}

setup_pss() {
    if [ "$PATTERN" != "sidecar" ]; then
        return
    fi

    print_info "Setting up Pod Security Standards for sidecar..."
    kubectl create namespace suricata-monitoring --dry-run=client -o yaml | kubectl apply -f - > /dev/null 2>&1
    kubectl label namespace suricata-monitoring \
        pod-security.kubernetes.io/enforce=privileged \
        pod-security.kubernetes.io/audit=privileged \
        pod-security.kubernetes.io/warn=privileged \
        --overwrite > /dev/null 2>&1
    print_success "PSS labels configured"
}

deploy_pattern() {
    print_info "Deploying $PATTERN pattern..."

    cd "$PATTERNS_DIR/$PATTERN"

    if kubectl apply -k . > /dev/null 2>&1; then
        print_success "Deployment applied!"
    else
        print_error "Deployment failed!"
        exit 1
    fi
}

wait_pods() {
    print_info "Waiting for pods..."

    # Wait max 2 minutes
    timeout 120 bash -c '
        while true; do
            READY=$(kubectl get pods -n suricata-monitoring -l app=suricata-dashboard --no-headers 2>/dev/null | grep "Running" | wc -l)
            if [ "$READY" -gt 0 ]; then
                exit 0
            fi
            sleep 2
        done
    ' 2>/dev/null || true

    print_success "Pods started"
}

show_access() {
    print_success "Deployment complete!"
    echo ""
    print_info "Access dashboard:"
    echo ""

    # Try to get service info
    SVC_TYPE=$(kubectl get svc dashboard-service -n suricata-monitoring -o jsonpath='{.spec.type}' 2>/dev/null || echo "ClusterIP")

    case $SVC_TYPE in
        NodePort)
            NODE_PORT=$(kubectl get svc dashboard-service -n suricata-monitoring -o jsonpath='{.spec.ports[0].nodePort}')
            NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' | awk '{print $1}')
            echo "  URL: http://${NODE_IP}:${NODE_PORT}"
            ;;
        LoadBalancer)
            echo "  Waiting for LoadBalancer IP..."
            echo "  Check: kubectl get svc dashboard-service -n suricata-monitoring"
            ;;
        *)
            echo "  Port-forward: kubectl port-forward -n suricata-monitoring svc/dashboard-service 5000:5000"
            echo "  Then open: http://localhost:5000"
            ;;
    esac

    echo ""
    print_info "Quick commands:"
    echo "  Logs:   kubectl logs -f -n suricata-monitoring -l app=suricata-dashboard"
    echo "  Status: kubectl get pods -n suricata-monitoring -o wide"
    echo "  Delete: kubectl delete -k $PATTERNS_DIR/$PATTERN/"
}

main() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  Quick Deploy - Suricata Dashboard${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    parse_args "$@"

    print_info "Pattern: $PATTERN"
    echo ""

    quick_check
    create_secret
    setup_pss
    label_nodes
    deploy_pattern
    wait_pods
    show_access
}

main "$@"
