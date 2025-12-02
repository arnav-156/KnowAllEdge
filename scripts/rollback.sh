#!/bin/bash
# =============================================================================
# Deployment Rollback Script
# Rolls back to a previous Docker image version
# =============================================================================

set -e  # Exit on error

# Configuration
REGISTRY="${REGISTRY:-ghcr.io}"
REPOSITORY="${REPOSITORY:-your-org/KNOWALLEDGE}"
MAX_VERSIONS=5

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in correct environment
check_environment() {
    if [ -z "$DEPLOYMENT_ENV" ]; then
        log_error "DEPLOYMENT_ENV not set. Set to 'staging' or 'production'"
        exit 1
    fi
    
    if [ "$DEPLOYMENT_ENV" != "staging" ] && [ "$DEPLOYMENT_ENV" != "production" ]; then
        log_error "DEPLOYMENT_ENV must be 'staging' or 'production'"
        exit 1
    fi
    
    log_info "Environment: $DEPLOYMENT_ENV"
}

# Get current deployment version
get_current_version() {
    if command -v kubectl &> /dev/null; then
        # Kubernetes deployment
        CURRENT_VERSION=$(kubectl get deployment KNOWALLEDGE-backend -n $DEPLOYMENT_ENV -o jsonpath='{.spec.template.spec.containers[0].image}' | cut -d':' -f2)
    elif command -v docker &> /dev/null; then
        # Docker Compose deployment
        CURRENT_VERSION=$(docker inspect KNOWALLEDGE-backend --format='{{.Config.Image}}' | cut -d':' -f2)
    else
        log_error "Neither kubectl nor docker found"
        exit 1
    fi
    
    log_info "Current version: $CURRENT_VERSION"
    echo "$CURRENT_VERSION"
}

# List available versions
list_versions() {
    log_info "Fetching available versions..."
    
    # Get last 5 versions from container registry
    if command -v crane &> /dev/null; then
        # Using crane (Google's container registry tool)
        VERSIONS=$(crane ls "$REGISTRY/$REPOSITORY/backend" | tail -n $MAX_VERSIONS)
    elif command -v skopeo &> /dev/null; then
        # Using skopeo
        VERSIONS=$(skopeo list-tags docker://"$REGISTRY/$REPOSITORY/backend" | jq -r '.Tags[]' | tail -n $MAX_VERSIONS)
    else
        log_warn "Neither crane nor skopeo found. Listing from local images..."
        VERSIONS=$(docker images "$REGISTRY/$REPOSITORY/backend" --format "{{.Tag}}" | head -n $MAX_VERSIONS)
    fi
    
    echo "$VERSIONS"
}

# Rollback to specific version
rollback_to_version() {
    local TARGET_VERSION=$1
    
    log_info "Rolling back to version: $TARGET_VERSION"
    
    # Create backup of current deployment
    log_info "Creating backup of current deployment..."
    if command -v kubectl &> /dev/null; then
        kubectl get deployment KNOWALLEDGE-backend -n $DEPLOYMENT_ENV -o yaml > "backup-deployment-$(date +%Y%m%d-%H%M%S).yaml"
    fi
    
    # Perform rollback
    if command -v kubectl &> /dev/null; then
        # Kubernetes rollback
        log_info "Updating Kubernetes deployment..."
        
        kubectl set image deployment/KNOWALLEDGE-backend \
            backend="$REGISTRY/$REPOSITORY/backend:$TARGET_VERSION" \
            -n $DEPLOYMENT_ENV
        
        kubectl set image deployment/KNOWALLEDGE-frontend \
            frontend="$REGISTRY/$REPOSITORY/frontend:$TARGET_VERSION" \
            -n $DEPLOYMENT_ENV
        
        # Wait for rollout
        log_info "Waiting for rollout to complete..."
        kubectl rollout status deployment/KNOWALLEDGE-backend -n $DEPLOYMENT_ENV --timeout=5m
        kubectl rollout status deployment/KNOWALLEDGE-frontend -n $DEPLOYMENT_ENV --timeout=5m
        
    elif command -v docker-compose &> /dev/null; then
        # Docker Compose rollback
        log_info "Updating Docker Compose deployment..."
        
        export BACKEND_IMAGE="$REGISTRY/$REPOSITORY/backend:$TARGET_VERSION"
        export FRONTEND_IMAGE="$REGISTRY/$REPOSITORY/frontend:$TARGET_VERSION"
        
        docker-compose pull
        docker-compose up -d --no-deps backend frontend
        
        # Wait for health check
        log_info "Waiting for services to be healthy..."
        sleep 10
        
        if ! docker-compose ps | grep -q "Up (healthy)"; then
            log_error "Services failed health check"
            return 1
        fi
    else
        log_error "No deployment tool found"
        exit 1
    fi
    
    log_info "Rollback completed successfully"
}

# Verify rollback
verify_rollback() {
    local TARGET_VERSION=$1
    
    log_info "Verifying rollback..."
    
    # Check health endpoint
    if [ "$DEPLOYMENT_ENV" = "production" ]; then
        HEALTH_URL="https://KNOWALLEDGE.com/health"
    else
        HEALTH_URL="https://staging.KNOWALLEDGE.com/health"
    fi
    
    HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL")
    
    if [ "$HEALTH_STATUS" = "200" ]; then
        log_info "Health check passed (HTTP $HEALTH_STATUS)"
    else
        log_error "Health check failed (HTTP $HEALTH_STATUS)"
        return 1
    fi
    
    # Verify version
    CURRENT_VERSION=$(get_current_version)
    if [ "$CURRENT_VERSION" = "$TARGET_VERSION" ]; then
        log_info "Version verified: $CURRENT_VERSION"
    else
        log_error "Version mismatch. Expected: $TARGET_VERSION, Got: $CURRENT_VERSION"
        return 1
    fi
    
    log_info "Rollback verification successful"
}

# Cleanup old versions
cleanup_old_versions() {
    log_info "Cleaning up old versions (keeping last $MAX_VERSIONS)..."
    
    if command -v kubectl &> /dev/null; then
        # Keep last N replica sets
        kubectl delete replicaset -n $DEPLOYMENT_ENV \
            $(kubectl get replicaset -n $DEPLOYMENT_ENV --sort-by=.metadata.creationTimestamp -o name | head -n -$MAX_VERSIONS) \
            2>/dev/null || true
    fi
    
    # Cleanup old Docker images
    if command -v docker &> /dev/null; then
        docker images "$REGISTRY/$REPOSITORY/backend" --format "{{.Tag}}" | \
            tail -n +$(($MAX_VERSIONS + 1)) | \
            xargs -I {} docker rmi "$REGISTRY/$REPOSITORY/backend:{}" 2>/dev/null || true
    fi
    
    log_info "Cleanup completed"
}

# Main script
main() {
    log_info "=== Deployment Rollback Script ==="
    
    # Check environment
    check_environment
    
    # Get current version
    CURRENT_VERSION=$(get_current_version)
    
    # List available versions
    log_info "Available versions:"
    VERSIONS=$(list_versions)
    echo "$VERSIONS" | nl
    
    # Prompt for target version
    if [ -z "$TARGET_VERSION" ]; then
        echo ""
        read -p "Enter version number to rollback to (or 'cancel' to abort): " SELECTION
        
        if [ "$SELECTION" = "cancel" ]; then
            log_info "Rollback cancelled"
            exit 0
        fi
        
        TARGET_VERSION=$(echo "$VERSIONS" | sed -n "${SELECTION}p")
        
        if [ -z "$TARGET_VERSION" ]; then
            log_error "Invalid selection"
            exit 1
        fi
    fi
    
    # Confirm rollback
    log_warn "About to rollback from $CURRENT_VERSION to $TARGET_VERSION"
    read -p "Are you sure? (yes/no): " CONFIRM
    
    if [ "$CONFIRM" != "yes" ]; then
        log_info "Rollback cancelled"
        exit 0
    fi
    
    # Perform rollback
    if rollback_to_version "$TARGET_VERSION"; then
        # Verify rollback
        if verify_rollback "$TARGET_VERSION"; then
            log_info "✅ Rollback successful!"
            
            # Cleanup old versions
            cleanup_old_versions
            
            # Send notification
            if [ -n "$SLACK_WEBHOOK" ]; then
                curl -X POST "$SLACK_WEBHOOK" \
                    -H 'Content-Type: application/json' \
                    -d "{\"text\":\"✅ Rollback successful: $CURRENT_VERSION → $TARGET_VERSION ($DEPLOYMENT_ENV)\"}"
            fi
        else
            log_error "❌ Rollback verification failed"
            exit 1
        fi
    else
        log_error "❌ Rollback failed"
        exit 1
    fi
}

# Run main function
main "$@"

# =============================================================================
# Usage Examples:
# =============================================================================
#
# 1. Interactive rollback (prompts for version):
#    DEPLOYMENT_ENV=staging ./rollback.sh
#
# 2. Rollback to specific version:
#    DEPLOYMENT_ENV=production TARGET_VERSION=v1.2.3 ./rollback.sh
#
# 3. With custom registry:
#    REGISTRY=docker.io REPOSITORY=myorg/myapp DEPLOYMENT_ENV=staging ./rollback.sh
#
# =============================================================================
# Prerequisites:
# =============================================================================
#
# - kubectl (for Kubernetes deployments)
# - docker and docker-compose (for Docker deployments)
# - crane or skopeo (optional, for listing registry versions)
# - curl (for health checks)
# - jq (optional, for JSON parsing)
#
# Environment Variables:
# - DEPLOYMENT_ENV: 'staging' or 'production' (required)
# - TARGET_VERSION: Version to rollback to (optional, will prompt if not set)
# - REGISTRY: Container registry URL (default: ghcr.io)
# - REPOSITORY: Repository name (default: your-org/KNOWALLEDGE)
# - SLACK_WEBHOOK: Slack webhook for notifications (optional)
#
# =============================================================================
