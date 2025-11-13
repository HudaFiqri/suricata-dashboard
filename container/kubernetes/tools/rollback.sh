#!/bin/bash

# Kubernetes Deployment Rollback Tool

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
REVISION=""

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Rollback Kubernetes deployment to previous version.

OPTIONS:
    -n, --namespace NAMESPACE   Namespace (default: suricata-monitoring)
    -d, --deployment NAME       Deployment name (default: suricata-dashboard)
    -r, --revision NUM          Rollback to specific revision
    --history                   Show rollout history
    --status                    Show rollout status
    -h, --help                  Show this help message

EXAMPLES:
    # Rollback to previous version
    $0

    # Rollback to specific revision
    $0 --revision 3

    # Show rollout history
    $0 --history

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
            -r|--revision)
                REVISION="$2"
                shift 2
                ;;
            --history)
                show_history
                exit 0
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
}

show_history() {
    print_info "Rollout history for $DEPLOYMENT:"
    echo ""
    kubectl rollout history deployment/"$DEPLOYMENT" -n "$NAMESPACE"
    echo ""

    # Show current revision
    CURRENT_REV=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.metadata.annotations.deployment\.kubernetes\.io/revision}')
    print_info "Current revision: $CURRENT_REV"
}

show_status() {
    print_info "Rollout status for $DEPLOYMENT:"
    echo ""
    kubectl rollout status deployment/"$DEPLOYMENT" -n "$NAMESPACE"
    echo ""

    print_info "Pod status:"
    kubectl get pods -n "$NAMESPACE" -l app=suricata-dashboard -o wide
}

perform_rollback() {
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Kubernetes Rollback Tool              ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""

    # Show current history
    print_info "Current rollout history:"
    echo ""
    kubectl rollout history deployment/"$DEPLOYMENT" -n "$NAMESPACE"
    echo ""

    # Get current revision
    CURRENT_REV=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.metadata.annotations.deployment\.kubernetes\.io/revision}')
    print_info "Current revision: $CURRENT_REV"
    echo ""

    # Confirm rollback
    if [ -n "$REVISION" ]; then
        print_warning "Rolling back to revision $REVISION"
    else
        print_warning "Rolling back to previous revision"
    fi

    read -p "Are you sure you want to rollback? (y/n): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_info "Rollback cancelled"
        exit 0
    fi

    echo ""

    # Perform rollback
    print_info "Performing rollback..."

    if [ -n "$REVISION" ]; then
        CMD="kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE --to-revision=$REVISION"
    else
        CMD="kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE"
    fi

    if $CMD; then
        print_success "Rollback initiated"
    else
        print_error "Rollback failed"
        exit 1
    fi

    echo ""

    # Wait for rollback to complete
    print_info "Waiting for rollback to complete..."
    kubectl rollout status deployment/"$DEPLOYMENT" -n "$NAMESPACE" --timeout=5m

    echo ""
    print_success "Rollback completed!"

    # Show new status
    echo ""
    NEW_REV=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.metadata.annotations.deployment\.kubernetes\.io/revision}')
    print_info "New revision: $NEW_REV"

    echo ""
    print_info "Pod status:"
    kubectl get pods -n "$NAMESPACE" -l app=suricata-dashboard -o wide

    echo ""
    print_info "Next steps:"
    echo "  - Monitor logs: kubectl logs -f -n $NAMESPACE -l app=suricata-dashboard"
    echo "  - Check status: $0 --status"
    echo "  - View history: $0 --history"
}

main() {
    parse_args "$@"
    check_prerequisites
    perform_rollback
}

main "$@"
