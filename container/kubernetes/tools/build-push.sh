#!/bin/bash

# Build and Push Docker Image for Kubernetes

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

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
DOCKERFILE="$REPO_ROOT/container/docker/Dockerfile"

# Default values
IMAGE_NAME="suricata-dashboard"
IMAGE_TAG="latest"
REGISTRY=""
PUSH=false
BUILD_ARGS=""

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Build and optionally push Docker image for Kubernetes deployment.

OPTIONS:
    -r, --registry REGISTRY    Container registry (e.g., ghcr.io/username, docker.io/username)
    -t, --tag TAG             Image tag (default: latest)
    -n, --name NAME           Image name (default: suricata-dashboard)
    -p, --push                Push image after build
    -b, --build-arg ARG       Pass build argument (can be used multiple times)
    --no-cache                Build without cache
    -h, --help                Show this help message

EXAMPLES:
    # Build only
    $0

    # Build and push to GitHub Container Registry
    $0 -r ghcr.io/username -t v1.0.0 -p

    # Build and push to Docker Hub
    $0 -r docker.io/username -p

    # Build with custom tag
    $0 -t dev-$(git rev-parse --short HEAD)

    # Build with build arguments
    $0 -b "BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')" -b "VERSION=1.0.0"

EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -r|--registry)
                REGISTRY="$2"
                shift 2
                ;;
            -t|--tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            -n|--name)
                IMAGE_NAME="$2"
                shift 2
                ;;
            -p|--push)
                PUSH=true
                shift
                ;;
            -b|--build-arg)
                BUILD_ARGS="$BUILD_ARGS --build-arg $2"
                shift 2
                ;;
            --no-cache)
                NO_CACHE="--no-cache"
                shift
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
    print_info "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker first."
        exit 1
    fi
    print_success "Docker found: $(docker --version)"

    if [ ! -f "$DOCKERFILE" ]; then
        print_error "Dockerfile not found: $DOCKERFILE"
        exit 1
    fi
    print_success "Dockerfile found"

    if [ "$PUSH" = true ] && [ -z "$REGISTRY" ]; then
        print_error "Registry required when using --push"
        exit 1
    fi

    echo ""
}

build_image() {
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE="$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
    else
        FULL_IMAGE="$IMAGE_NAME:$IMAGE_TAG"
    fi

    print_info "Building image: $FULL_IMAGE"
    echo ""

    cd "$REPO_ROOT"

    if docker build $NO_CACHE $BUILD_ARGS \
        -f "$DOCKERFILE" \
        -t "$FULL_IMAGE" \
        .; then
        print_success "Image built successfully!"
    else
        print_error "Build failed!"
        exit 1
    fi

    echo ""

    # Show image info
    print_info "Image details:"
    docker images "$FULL_IMAGE" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    echo ""
}

tag_additional() {
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE="$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"

        # Tag as latest if not already
        if [ "$IMAGE_TAG" != "latest" ]; then
            print_info "Tagging as latest..."
            docker tag "$FULL_IMAGE" "$REGISTRY/$IMAGE_NAME:latest"
            print_success "Tagged as $REGISTRY/$IMAGE_NAME:latest"
            echo ""
        fi

        # Tag with git commit if in git repo
        if git rev-parse --git-dir > /dev/null 2>&1; then
            GIT_SHA=$(git rev-parse --short HEAD)
            print_info "Tagging with git SHA: $GIT_SHA"
            docker tag "$FULL_IMAGE" "$REGISTRY/$IMAGE_NAME:$GIT_SHA"
            print_success "Tagged as $REGISTRY/$IMAGE_NAME:$GIT_SHA"
            echo ""
        fi
    fi
}

push_image() {
    if [ "$PUSH" = false ]; then
        return
    fi

    FULL_IMAGE="$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"

    print_info "Pushing image to registry..."
    echo ""

    # Check if logged in
    if ! docker info 2>&1 | grep -q "Username"; then
        print_warning "Not logged in to Docker registry"
        read -p "Do you want to login now? (y/n): " login_choice
        if [[ $login_choice =~ ^[Yy]$ ]]; then
            docker login "$REGISTRY"
        else
            print_error "Cannot push without authentication"
            exit 1
        fi
    fi

    # Push main tag
    if docker push "$FULL_IMAGE"; then
        print_success "Pushed: $FULL_IMAGE"
    else
        print_error "Push failed!"
        exit 1
    fi

    # Push latest if tagged
    if [ "$IMAGE_TAG" != "latest" ]; then
        if docker push "$REGISTRY/$IMAGE_NAME:latest"; then
            print_success "Pushed: $REGISTRY/$IMAGE_NAME:latest"
        fi
    fi

    # Push git SHA if tagged
    if git rev-parse --git-dir > /dev/null 2>&1; then
        GIT_SHA=$(git rev-parse --short HEAD)
        if docker push "$REGISTRY/$IMAGE_NAME:$GIT_SHA"; then
            print_success "Pushed: $REGISTRY/$IMAGE_NAME:$GIT_SHA"
        fi
    fi

    echo ""
}

show_next_steps() {
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE="$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
    else
        FULL_IMAGE="$IMAGE_NAME:$IMAGE_TAG"
    fi

    print_info "Next Steps:"
    echo ""

    if [ "$PUSH" = true ]; then
        echo "  1. Update Kubernetes manifests with new image:"
        echo "     Image: $FULL_IMAGE"
        echo ""
        echo "  2. Deploy to Kubernetes:"
        echo "     cd container/kubernetes/tools"
        echo "     ./deploy.sh"
        echo ""
        echo "  3. Or update existing deployment:"
        echo "     kubectl set image deployment/suricata-dashboard \\"
        echo "       dashboard=$FULL_IMAGE \\"
        echo "       -n suricata-monitoring"
    else
        echo "  1. Push image to registry:"
        echo "     $0 -r <registry> -t $IMAGE_TAG -p"
        echo ""
        echo "  2. Or use locally (minikube/kind):"
        echo "     # For minikube:"
        echo "     minikube image load $FULL_IMAGE"
        echo ""
        echo "     # For kind:"
        echo "     kind load docker-image $FULL_IMAGE"
    fi

    echo ""
}

show_summary() {
    print_success "Build completed!"
    echo ""
    print_info "Summary:"

    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE="$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
    else
        FULL_IMAGE="$IMAGE_NAME:$IMAGE_TAG"
    fi

    echo "  Image: $FULL_IMAGE"
    echo "  Size:  $(docker images $FULL_IMAGE --format '{{.Size}}')"

    if [ "$PUSH" = true ]; then
        echo "  Registry: $REGISTRY"
        echo "  Status: Pushed ✓"
    else
        echo "  Status: Built locally (not pushed)"
    fi

    echo ""
}

main() {
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Docker Build & Push Tool              ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""

    parse_args "$@"
    check_prerequisites
    build_image
    tag_additional
    push_image
    show_summary
    show_next_steps
}

main "$@"
