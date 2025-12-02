#!/bin/bash
# =============================================================================
# Kubernetes Deployment Rollback Script
# Uses kubectl rollout undo for quick rollbacks
# =============================================================================

set -e

# Configuration
NAMESPACE="${NAMESPACE:-default}"
DEPLOYMENT_NAME="${DEPLOYMENT_NAME:-KNOWALLEDGE-backend}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl not found. Please install kubectl."
    exit 1
fi

# Show rollout history
show_history() {
    log_info "Deployment history for $DEPLOYMENT_NAME:"
    kubectl rollout history deployment/$DEPLOYMENT_NAME -n $NAMESPACE
}

# Rollback to previous revision
rollback_previous() {
    log_info "Rolling back to previous revision..."
    kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE
    
    log_info "Waiting for rollout to complete..."
    kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=5m
    
    log_info "✅ Rollback to previous revision completed"
}

# Rollback to specific revision
rollback_to_revision() {
    local REVISION=$1
    
    log_info "Rolling back to revision $REVISION..."
    kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE --to-revision=$REVISION
    
    log_info "Waiting for rollout to complete..."
    kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=5m
    
    log_info "✅ Rollback to revision $REVISION completed"
}

# Main
main() {
    log_info "=== Kubernetes Rollback Script ==="
    
    # Show history
    show_history
    
    # Prompt for action
    echo ""
    read -p "Enter revision number to rollback to (or 'previous' for last revision, 'cancel' to abort): " SELECTION
    
    if [ "$SELECTION" = "cancel" ]; then
        log_info "Rollback cancelled"
        exit 0
    elif [ "$SELECTION" = "previous" ]; then
        rollback_previous
    elif [[ "$SELECTION" =~ ^[0-9]+$ ]]; then
        rollback_to_revision "$SELECTION"
    else
        log_error "Invalid selection"
        exit 1
    fi
}

main "$@"

# =============================================================================
# Usage:
# =============================================================================
#
# 1. Rollback with defaults:
#    ./k8s-rollback.sh
#
# 2. Rollback specific deployment:
#    DEPLOYMENT_NAME=KNOWALLEDGE-frontend NAMESPACE=production ./k8s-rollback.sh
#
# 3. Quick rollback to previous (non-interactive):
#    kubectl rollout undo deployment/KNOWALLEDGE-backend -n production
#
# =============================================================================
