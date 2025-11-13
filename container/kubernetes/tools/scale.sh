#!/bin/bash

# Kubernetes Scaling Tool

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }

NAMESPACE="suricata-monitoring"
DEPLOYMENT="suricata-dashboard"
REPLICAS=""

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Scale Kubernetes deployment replicas.

OPTIONS:
    -n, --namespace NAMESPACE   Namespace (default: suricata-monitoring)
    -d, --deployment NAME       Deployment name (default: suricata-dashboard)
    -r, --replicas NUM          Number of replicas
    --status                    Show current scale status
    -h, --help                  Show this help message

EXAMPLES:
    # Scale to 3 replicas
    $0 --replicas 3

    # Scale down to 1
    $0 -r 1

    # Show current status
    $0 --status

EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -d|--deployment)
                DEPLOYMENT="$2"
                shift 2
                ;;
            -r|--replicas)
                REPLICAS="$2"
                shift 2
                ;;
            --status)
                show_status
                exit 0
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

    if [ -z "$REPLICAS" ]; then
        print_error "Number of replicas required"
        show_usage
        exit 1
    fi
}

check_prerequisites() {
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found"
        exit 1
    fi

    if ! kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" &> /dev/null; then
        print_error "Deployment '$DEPLOYMENT' not found in namespace '$NAMESPACE'"
        exit 1
    fi

    # Check if deployment supports scaling
    KIND=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.kind}')
    if [ "$KIND" == "DaemonSet" ]; then
        print_error "Cannot scale DaemonSet. DaemonSet runs one pod per node automatically."
        exit 1
    fi
}

show_status() {
    print_info "Current scale status:"
    echo ""

    CURRENT=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
    READY=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
    AVAILABLE=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.status.availableReplicas}')

    echo "  Desired:   $CURRENT"
    echo "  Ready:     $READY"
    echo "  Available: $AVAILABLE"

    echo ""
    print_info "Pods:"
    kubectl get pods -n "$NAMESPACE" -l app=suricata-dashboard -o wide
}

perform_scale() {
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Kubernetes Scaling Tool               ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""

    # Show current status
    CURRENT=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
    print_info "Current replicas: $CURRENT"
    print_info "Target replicas: $REPLICAS"
    echo ""

    # Validate replica count
    if ! [[ "$REPLICAS" =~ ^[0-9]+$ ]]; then
        print_error "Invalid replica count: $REPLICAS"
        exit 1
    fi

    if [ "$REPLICAS" -eq 0 ]; then
        print_warning "Scaling to 0 will make the service unavailable!"
        read -p "Are you sure? (y/n): " confirm
        if [[ ! $confirm =~ ^[Yy]$ ]]; then
            print_info "Scaling cancelled"
            exit 0
        fi
    fi

    # Perform scaling
    print_info "Scaling deployment..."

    if kubectl scale deployment "$DEPLOYMENT" --replicas="$REPLICAS" -n "$NAMESPACE"; then
        print_success "Scaling initiated"
    else
        print_error "Scaling failed"
        exit 1
    fi

    echo ""

    # Wait for scaling to complete
    print_info "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod \
        -l app=suricata-dashboard \
        -n "$NAMESPACE" \
        --timeout=300s 2>/dev/null || true

    echo ""
    print_success "Scaling completed!"

    # Show new status
    echo ""
    print_info "New status:"
    show_status

    echo ""
    print_info "Next steps:"
    echo "  - Monitor pods: kubectl get pods -n $NAMESPACE -w"
    echo "  - View logs: kubectl logs -f -n $NAMESPACE -l app=suricata-dashboard"
    echo "  - Check status: $0 --status"
}

main() {
    parse_args "$@"
    check_prerequisites
    perform_scale
}

main "$@"
