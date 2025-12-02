#!/bin/bash
# =============================================================================
# Version Tagging Script
# Tags Docker images with version numbers and manages version history
# =============================================================================

set -e

# Configuration
REGISTRY="${REGISTRY:-ghcr.io}"
REPOSITORY="${REPOSITORY:-your-org/KNOWALLEDGE}"
MAX_VERSIONS=5

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get current version from git
get_current_version() {
    if git describe --tags --exact-match 2>/dev/null; then
        # On a tag
        VERSION=$(git describe --tags --exact-match)
    else
        # Not on a tag, use branch and short SHA
        BRANCH=$(git rev-parse --abbrev-ref HEAD)
        SHA=$(git rev-parse --short HEAD)
        VERSION="${BRANCH}-${SHA}"
    fi
    echo "$VERSION"
}

# Tag images
tag_images() {
    local VERSION=$1
    local COMMIT_SHA=$(git rev-parse --short HEAD)
    local TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    
    log_info "Tagging images with version: $VERSION"
    
    # Tag backend image
    log_info "Tagging backend image..."
    docker tag KNOWALLEDGE-backend:latest "$REGISTRY/$REPOSITORY/backend:$VERSION"
    docker tag KNOWALLEDGE-backend:latest "$REGISTRY/$REPOSITORY/backend:$COMMIT_SHA"
    docker tag KNOWALLEDGE-backend:latest "$REGISTRY/$REPOSITORY/backend:latest"
    
    # Tag frontend image
    log_info "Tagging frontend image..."
    docker tag KNOWALLEDGE-frontend:latest "$REGISTRY/$REPOSITORY/frontend:$VERSION"
    docker tag KNOWALLEDGE-frontend:latest "$REGISTRY/$REPOSITORY/frontend:$COMMIT_SHA"
    docker tag KNOWALLEDGE-frontend:latest "$REGISTRY/$REPOSITORY/frontend:latest"
    
    log_info "Images tagged successfully"
}

# Push images
push_images() {
    local VERSION=$1
    local COMMIT_SHA=$(git rev-parse --short HEAD)
    
    log_info "Pushing images to registry..."
    
    # Push backend
    docker push "$REGISTRY/$REPOSITORY/backend:$VERSION"
    docker push "$REGISTRY/$REPOSITORY/backend:$COMMIT_SHA"
    docker push "$REGISTRY/$REPOSITORY/backend:latest"
    
    # Push frontend
    docker push "$REGISTRY/$REPOSITORY/frontend:$VERSION"
    docker push "$REGISTRY/$REPOSITORY/frontend:$COMMIT_SHA"
    docker push "$REGISTRY/$REPOSITORY/frontend:latest"
    
    log_info "Images pushed successfully"
}

# List versions
list_versions() {
    log_info "Listing recent versions..."
    
    if command -v crane &> /dev/null; then
        log_info "Backend versions:"
        crane ls "$REGISTRY/$REPOSITORY/backend" | grep -E '^v[0-9]' | tail -n 10
        
        log_info "Frontend versions:"
        crane ls "$REGISTRY/$REPOSITORY/frontend" | grep -E '^v[0-9]' | tail -n 10
    else
        log_warn "crane not installed. Install with: go install github.com/google/go-containerregistry/cmd/crane@latest"
    fi
}

# Cleanup old versions
cleanup_old_versions() {
    log_info "Cleaning up old versions (keeping last $MAX_VERSIONS)..."
    
    if command -v crane &> /dev/null; then
        # Get all version tags
        BACKEND_VERSIONS=$(crane ls "$REGISTRY/$REPOSITORY/backend" | grep -E '^v[0-9]' | sort -V)
        FRONTEND_VERSIONS=$(crane ls "$REGISTRY/$REPOSITORY/frontend" | grep -E '^v[0-9]' | sort -V)
        
        # Count versions
        BACKEND_COUNT=$(echo "$BACKEND_VERSIONS" | wc -l)
        FRONTEND_COUNT=$(echo "$FRONTEND_VERSIONS" | wc -l)
        
        # Delete old backend versions
        if [ "$BACKEND_COUNT" -gt "$MAX_VERSIONS" ]; then
            TO_DELETE=$((BACKEND_COUNT - MAX_VERSIONS))
            echo "$BACKEND_VERSIONS" | head -n $TO_DELETE | while read -r VERSION; do
                log_info "Deleting old backend version: $VERSION"
                crane delete "$REGISTRY/$REPOSITORY/backend:$VERSION" || true
            done
        fi
        
        # Delete old frontend versions
        if [ "$FRONTEND_COUNT" -gt "$MAX_VERSIONS" ]; then
            TO_DELETE=$((FRONTEND_COUNT - MAX_VERSIONS))
            echo "$FRONTEND_VERSIONS" | head -n $TO_DELETE | while read -r VERSION; do
                log_info "Deleting old frontend version: $VERSION"
                crane delete "$REGISTRY/$REPOSITORY/frontend:$VERSION" || true
            done
        fi
        
        log_info "Cleanup completed"
    else
        log_warn "Skipping cleanup (crane not installed)"
    fi
}

# Create version file
create_version_file() {
    local VERSION=$1
    local COMMIT_SHA=$(git rev-parse HEAD)
    local COMMIT_SHORT=$(git rev-parse --short HEAD)
    local BRANCH=$(git rev-parse --abbrev-ref HEAD)
    local TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    cat > version.json <<EOF
{
  "version": "$VERSION",
  "commit": "$COMMIT_SHA",
  "commit_short": "$COMMIT_SHORT",
  "branch": "$BRANCH",
  "build_time": "$TIMESTAMP",
  "registry": "$REGISTRY/$REPOSITORY"
}
EOF
    
    log_info "Version file created: version.json"
}

# Main
main() {
    log_info "=== Version Tagging Script ==="
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not in a git repository"
        exit 1
    fi
    
    # Get version
    if [ -n "$VERSION" ]; then
        log_info "Using provided version: $VERSION"
    else
        VERSION=$(get_current_version)
        log_info "Detected version: $VERSION"
    fi
    
    # Validate version format (should be vX.Y.Z or branch-sha)
    if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] && [[ ! "$VERSION" =~ ^[a-z]+-[a-f0-9]+$ ]]; then
        log_warn "Version format doesn't match expected patterns (vX.Y.Z or branch-sha)"
        read -p "Continue anyway? (yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            exit 1
        fi
    fi
    
    # Tag images
    tag_images "$VERSION"
    
    # Push images
    if [ "$PUSH" = "true" ] || [ "$PUSH" = "1" ]; then
        push_images "$VERSION"
        
        # Cleanup old versions
        cleanup_old_versions
    else
        log_info "Skipping push (set PUSH=true to push images)"
    fi
    
    # Create version file
    create_version_file "$VERSION"
    
    # List versions
    list_versions
    
    log_info "✅ Version tagging completed: $VERSION"
}

main "$@"

# =============================================================================
# Usage:
# =============================================================================
#
# 1. Tag with auto-detected version:
#    ./tag-version.sh
#
# 2. Tag with specific version:
#    VERSION=v1.2.3 ./tag-version.sh
#
# 3. Tag and push:
#    VERSION=v1.2.3 PUSH=true ./tag-version.sh
#
# 4. With custom registry:
#    REGISTRY=docker.io REPOSITORY=myorg/myapp VERSION=v1.0.0 PUSH=true ./tag-version.sh
#
# =============================================================================
# Prerequisites:
# =============================================================================
#
# - docker (required)
# - git (required)
# - crane (optional, for cleanup): go install github.com/google/go-containerregistry/cmd/crane@latest
#
# =============================================================================
