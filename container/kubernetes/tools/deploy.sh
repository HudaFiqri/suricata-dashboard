#!/bin/bash

# Suricata Dashboard - Kubernetes Deployment Tool
# Interactive deployment script for all patterns

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_DIR="$(dirname "$SCRIPT_DIR")"
PATTERNS_DIR="$K8S_DIR/patterns"

# Functions
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Suricata Dashboard - K8s Deployer    ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found. Please install kubectl first."
        exit 1
    fi
    print_success "kubectl found: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"

    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster. Check your kubeconfig."
        exit 1
    fi
    print_success "Connected to cluster: $(kubectl config current-context)"

    # Check kustomize
    if kubectl kustomize --help &> /dev/null; then
        print_success "kustomize available (via kubectl)"
    else
        print_warning "kustomize not available, will use kubectl apply -k"
    fi

    echo ""
}

show_patterns() {
    echo -e "${BLUE}Available Deployment Patterns:${NC}"
    echo ""
    echo "  1) HostPath     - Single node with local Suricata"
    echo "  2) DaemonSet    - Multi-node distributed monitoring"
    echo "  3) NFS          - Shared storage, scalable"
    echo "  4) Sidecar      - Fully containerized (Suricata in pod)"
    echo ""
}

select_pattern() {
    while true; do
        show_patterns
        read -p "Select pattern (1-4): " pattern_choice

        case $pattern_choice in
            1)
                PATTERN="hostpath"
                PATTERN_NAME="HostPath"
                break
                ;;
            2)
                PATTERN="daemonset"
                PATTERN_NAME="DaemonSet"
                break
                ;;
            3)
                PATTERN="nfs"
                PATTERN_NAME="NFS"
                break
                ;;
            4)
                PATTERN="sidecar"
                PATTERN_NAME="Sidecar"
                break
                ;;
            *)
                print_error "Invalid choice. Please select 1-4."
                ;;
        esac
    done

    PATTERN_DIR="$PATTERNS_DIR/$PATTERN"

    if [ ! -d "$PATTERN_DIR" ]; then
        print_error "Pattern directory not found: $PATTERN_DIR"
        exit 1
    fi

    print_success "Selected pattern: $PATTERN_NAME"
    echo ""
}

check_pattern_prerequisites() {
    print_info "Checking pattern-specific prerequisites for $PATTERN_NAME..."

    case $PATTERN in
        hostpath|daemonset)
            # Check for labeled nodes
            LABELED_NODES=$(kubectl get nodes -l suricata=enabled --no-headers 2>/dev/null | wc -l)
            if [ "$LABELED_NODES" -eq 0 ]; then
                print_warning "No nodes labeled with 'suricata=enabled'"
                echo ""
                echo "Available nodes:"
                kubectl get nodes
                echo ""
                read -p "Do you want to label nodes now? (y/n): " label_choice
                if [[ $label_choice =~ ^[Yy]$ ]]; then
                    label_nodes
                else
                    print_warning "Continuing without labeling. Deployment may fail."
                fi
            else
                print_success "Found $LABELED_NODES node(s) with 'suricata=enabled' label"
            fi
            ;;
        nfs)
            print_warning "NFS pattern requires NFS server configuration"
            read -p "Have you configured NFS server? (y/n): " nfs_choice
            if [[ ! $nfs_choice =~ ^[Yy]$ ]]; then
                print_info "Please configure NFS server first. See pattern README."
                exit 0
            fi
            ;;
        sidecar)
            print_warning "Sidecar pattern requires privileged pods"
            # Check if namespace exists and has PSS labels
            if kubectl get namespace suricata-monitoring &> /dev/null; then
                PSS_ENFORCE=$(kubectl get namespace suricata-monitoring -o jsonpath='{.metadata.labels.pod-security\.kubernetes\.io/enforce}' 2>/dev/null)
                if [ "$PSS_ENFORCE" != "privileged" ]; then
                    print_warning "Namespace not labeled for privileged pods"
                    read -p "Add privileged PSS labels? (y/n): " pss_choice
                    if [[ $pss_choice =~ ^[Yy]$ ]]; then
                        kubectl label namespace suricata-monitoring \
                            pod-security.kubernetes.io/enforce=privileged \
                            pod-security.kubernetes.io/audit=privileged \
                            pod-security.kubernetes.io/warn=privileged \
                            --overwrite
                        print_success "PSS labels added"
                    fi
                fi
            fi
            ;;
    esac

    echo ""
}

label_nodes() {
    echo ""
    kubectl get nodes
    echo ""
    read -p "Enter node name(s) to label (space-separated): " nodes

    for node in $nodes; do
        if kubectl label nodes "$node" suricata=enabled --overwrite; then
            print_success "Labeled node: $node"
        else
            print_error "Failed to label node: $node"
        fi
    done
    echo ""
}

check_secret() {
    print_info "Checking for secret..."

    if kubectl get secret dashboard-secrets -n suricata-monitoring &> /dev/null; then
        print_success "Secret 'dashboard-secrets' already exists"
        read -p "Do you want to update it? (y/n): " update_secret
        if [[ ! $update_secret =~ ^[Yy]$ ]]; then
            return
        fi
    fi

    echo ""
    print_info "Creating secret for database password"
    read -sp "Enter database password (or press Enter to generate): " db_password
    echo ""

    if [ -z "$db_password" ]; then
        db_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        print_info "Generated password: $db_password"
        print_warning "Save this password in a secure location!"
    fi

    kubectl create secret generic dashboard-secrets \
        --from-literal=DB_PASSWORD="$db_password" \
        --namespace=suricata-monitoring \
        --dry-run=client -o yaml | kubectl apply -f -

    print_success "Secret created/updated"
    echo ""
}

check_configuration() {
    print_info "Checking configuration files..."

    # Check if deployment.yaml or daemonset.yaml exists
    if [ "$PATTERN" == "daemonset" ]; then
        CONFIG_FILE="$PATTERN_DIR/daemonset.yaml"
    else
        CONFIG_FILE="$PATTERN_DIR/deployment.yaml"
    fi

    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Configuration file not found: $CONFIG_FILE"
        exit 1
    fi

    # Check for placeholder values that need updating
    print_warning "Please ensure you've updated these values in deployment files:"
    echo "  - Container image registry"
    echo "  - NFS server (if using NFS pattern)"
    echo "  - Ingress hostname"
    echo ""

    read -p "Have you updated the configuration files? (y/n): " config_updated
    if [[ ! $config_updated =~ ^[Yy]$ ]]; then
        print_info "Please update configuration files in: $PATTERN_DIR"
        print_info "Then run this script again."
        exit 0
    fi

    print_success "Configuration check passed"
    echo ""
}

preview_deployment() {
    print_info "Preview of resources to be deployed:"
    echo ""

    cd "$PATTERN_DIR"
    kubectl kustomize . 2>/dev/null | grep -E "^kind:|^  name:" | head -20

    echo ""
    read -p "Proceed with deployment? (y/n): " proceed
    if [[ ! $proceed =~ ^[Yy]$ ]]; then
        print_info "Deployment cancelled"
        exit 0
    fi
    echo ""
}

deploy() {
    print_info "Deploying $PATTERN_NAME pattern..."
    echo ""

    cd "$PATTERN_DIR"

    if kubectl apply -k .; then
        print_success "Deployment successful!"
    else
        print_error "Deployment failed!"
        exit 1
    fi

    echo ""
}

wait_for_pods() {
    print_info "Waiting for pods to be ready..."
    echo ""

    kubectl wait --for=condition=ready pod \
        -l app=suricata-dashboard \
        -n suricata-monitoring \
        --timeout=300s 2>/dev/null || true

    kubectl wait --for=condition=ready pod \
        -l app=postgres \
        -n suricata-monitoring \
        --timeout=300s 2>/dev/null || true

    echo ""
}

show_deployment_status() {
    print_info "Deployment Status:"
    echo ""

    echo "Pods:"
    kubectl get pods -n suricata-monitoring -o wide
    echo ""

    echo "Services:"
    kubectl get svc -n suricata-monitoring
    echo ""

    if kubectl get ingress -n suricata-monitoring &> /dev/null; then
        echo "Ingress:"
        kubectl get ingress -n suricata-monitoring
        echo ""
    fi
}

show_access_info() {
    print_success "Deployment completed!"
    echo ""
    print_info "Access Information:"
    echo ""

    # Get service info
    SVC_TYPE=$(kubectl get svc dashboard-service -n suricata-monitoring -o jsonpath='{.spec.type}' 2>/dev/null || echo "ClusterIP")

    case $SVC_TYPE in
        NodePort)
            NODE_PORT=$(kubectl get svc dashboard-service -n suricata-monitoring -o jsonpath='{.spec.ports[0].nodePort}')
            NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}' | awk '{print $1}')
            if [ -z "$NODE_IP" ]; then
                NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' | awk '{print $1}')
            fi
            echo "  URL: http://${NODE_IP}:${NODE_PORT}"
            ;;
        LoadBalancer)
            EXTERNAL_IP=$(kubectl get svc dashboard-service -n suricata-monitoring -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
            if [ -n "$EXTERNAL_IP" ]; then
                echo "  URL: http://${EXTERNAL_IP}:5000"
            else
                print_warning "LoadBalancer IP pending..."
                echo "  Check with: kubectl get svc dashboard-service -n suricata-monitoring"
            fi
            ;;
        *)
            # Check for ingress
            if kubectl get ingress -n suricata-monitoring &> /dev/null; then
                INGRESS_HOST=$(kubectl get ingress -n suricata-monitoring -o jsonpath='{.items[0].spec.rules[0].host}')
                echo "  URL: http://${INGRESS_HOST}"
                echo ""
                print_info "Add to /etc/hosts if using .local domain:"
                INGRESS_IP=$(kubectl get ingress -n suricata-monitoring -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>/dev/null)
                if [ -n "$INGRESS_IP" ]; then
                    echo "  ${INGRESS_IP} ${INGRESS_HOST}"
                fi
            else
                echo "  Port-forward: kubectl port-forward -n suricata-monitoring svc/dashboard-service 5000:5000"
                echo "  Then access: http://localhost:5000"
            fi
            ;;
    esac

    echo ""
    print_info "Useful Commands:"
    echo "  View logs:   kubectl logs -f -n suricata-monitoring -l app=suricata-dashboard"
    echo "  Get pods:    kubectl get pods -n suricata-monitoring -o wide"
    echo "  Describe:    kubectl describe pod -n suricata-monitoring <pod-name>"
    echo "  Port-forward: kubectl port-forward -n suricata-monitoring svc/dashboard-service 5000:5000"
    echo ""
}

show_next_steps() {
    print_info "Next Steps:"
    echo ""
    echo "  1. Verify pods are running:"
    echo "     kubectl get pods -n suricata-monitoring -w"
    echo ""
    echo "  2. Check logs if there are issues:"
    echo "     kubectl logs -n suricata-monitoring -l app=suricata-dashboard"
    echo ""
    echo "  3. Access the dashboard using the URL above"
    echo ""
    echo "  4. Monitor the deployment:"
    echo "     kubectl get events -n suricata-monitoring --sort-by='.lastTimestamp'"
    echo ""
}

# Main execution
main() {
    print_header

    # Check prerequisites
    check_prerequisites

    # Select pattern
    select_pattern

    # Check pattern-specific prerequisites
    check_pattern_prerequisites

    # Check/create secret
    check_secret

    # Check configuration
    check_configuration

    # Preview deployment
    preview_deployment

    # Deploy
    deploy

    # Wait for pods
    wait_for_pods

    # Show status
    show_deployment_status

    # Show access info
    show_access_info

    # Show next steps
    show_next_steps
}

# Run main
main
