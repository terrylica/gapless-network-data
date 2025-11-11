#!/usr/bin/env bash
#
# Oracle Cloud Deployment Script
#
# Deploys MotherDuck monitoring to Oracle Cloud VM via SCP.
# Requires SSH key configured for VM access.

set -euo pipefail

# ================================================================================
# Configuration
# ================================================================================

VM_NAME="${OCI_VM_NAME:-motherduck-monitor}"
VM_REGION="${OCI_REGION:-us-ashburn-1}"
SSH_USER="${SSH_USER:-opc}"  # Default Oracle Linux user
SSH_KEY="${SSH_KEY:-$HOME/.ssh/motherduck-monitor}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE_DIR="/home/$SSH_USER"

# ================================================================================
# Helper Functions
# ================================================================================

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[ERROR] $*" >&2
    exit 1
}

check_prerequisites() {
    log "Checking prerequisites..."

    # Check OCI CLI installed
    if ! command -v oci &> /dev/null; then
        error "OCI CLI not installed. Install: brew install oci-cli"
    fi

    # Check SSH key exists
    if [[ ! -f "$SSH_KEY" ]]; then
        error "SSH key not found: $SSH_KEY"
    fi

    # Check required files exist
    if [[ ! -f "$SCRIPT_DIR/motherduck_monitor.py" ]]; then
        error "Monitoring script not found: $SCRIPT_DIR/motherduck_monitor.py"
    fi

    log "✅ Prerequisites OK"
}

get_vm_public_ip() {
    log "Getting VM public IP..."

    # Get VM OCID
    VM_OCID=$(oci compute instance list \
        --compartment-id "$(oci iam compartment list --query 'data[0].id' --raw-output)" \
        --display-name "$VM_NAME" \
        --lifecycle-state RUNNING \
        --query 'data[0].id' \
        --raw-output 2>/dev/null)

    if [[ -z "$VM_OCID" ]]; then
        error "VM not found: $VM_NAME (ensure VM is running)"
    fi

    # Get VNIC attachment
    VNIC_ID=$(oci compute vnic-attachment list \
        --compartment-id "$(oci iam compartment list --query 'data[0].id' --raw-output)" \
        --instance-id "$VM_OCID" \
        --query 'data[0]."vnic-id"' \
        --raw-output)

    # Get public IP
    PUBLIC_IP=$(oci network vnic get \
        --vnic-id "$VNIC_ID" \
        --query 'data."public-ip"' \
        --raw-output)

    if [[ -z "$PUBLIC_IP" ]]; then
        error "Public IP not found for VM: $VM_NAME"
    fi

    log "✅ VM Public IP: $PUBLIC_IP"
    echo "$PUBLIC_IP"
}

# ================================================================================
# Deployment Steps
# ================================================================================

deploy_scripts() {
    local vm_ip="$1"

    log "Deploying scripts to VM: $vm_ip"

    # SCP monitoring script
    log "  Uploading motherduck_monitor.py..."
    scp -i "$SSH_KEY" \
        "$SCRIPT_DIR/motherduck_monitor.py" \
        "$SSH_USER@$vm_ip:$REMOTE_DIR/"

    # SCP keep-alive script
    log "  Uploading keep_alive.sh..."
    scp -i "$SSH_KEY" \
        "$SCRIPT_DIR/keep_alive.sh" \
        "$SSH_USER@$vm_ip:$REMOTE_DIR/"

    # Make scripts executable
    ssh -i "$SSH_KEY" "$SSH_USER@$vm_ip" << 'EOF'
chmod +x ~/motherduck_monitor.py
chmod +x ~/keep_alive.sh
EOF

    log "✅ Scripts deployed"
}

install_dependencies() {
    local vm_ip="$1"

    log "Installing dependencies on VM..."

    # Install uv (Python package manager)
    ssh -i "$SSH_KEY" "$SSH_USER@$vm_ip" << 'EOF'
if ! command -v uv &> /dev/null; then
    echo "  Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "  ✅ uv already installed"
fi
EOF

    log "✅ Dependencies installed"
}

configure_environment() {
    local vm_ip="$1"

    log "Configuring environment variables..."

    # Fetch secret OCIDs from OCI Vault
    log "  Fetching secret OCIDs..."

    # Note: This requires secrets to already exist in OCI Vault
    # Run migrate_secrets.py first to create secrets

    ssh -i "$SSH_KEY" "$SSH_USER@$vm_ip" << 'EOF'
# Create environment file for cron
cat > ~/.env-motherduck << 'ENVEOF'
# MotherDuck configuration
MD_DATABASE=ethereum_mainnet
MD_TABLE=blocks

# Gap detection thresholds
GAP_THRESHOLD_SECONDS=15
TIME_WINDOW_START_DAYS=365
TIME_WINDOW_END_MINUTES=3
STALE_THRESHOLD_SECONDS=300

# OCI Secret OCIDs (set by migrate_secrets.py)
# SECRET_MOTHERDUCK_TOKEN_OCID=ocid1.vaultsecret.oc1...
# SECRET_HEALTHCHECKS_API_KEY_OCID=ocid1.vaultsecret.oc1...
# SECRET_PUSHOVER_TOKEN_OCID=ocid1.vaultsecret.oc1...
# SECRET_PUSHOVER_USER_OCID=ocid1.vaultsecret.oc1...

# Healthchecks.io ping URL
# HEALTHCHECKS_PING_URL=https://hc-ping.com/...
ENVEOF

echo "✅ Environment file created: ~/.env-motherduck"
echo "⚠️  Edit ~/.env-motherduck to add secret OCIDs"
EOF

    log "✅ Environment configured"
}

test_manual_execution() {
    local vm_ip="$1"

    log "Testing manual execution..."

    ssh -i "$SSH_KEY" "$SSH_USER@$vm_ip" << 'EOF'
cd ~
export PATH="$HOME/.local/bin:$PATH"
source ~/.env-motherduck

echo "Running motherduck_monitor.py..."
uv run motherduck_monitor.py || true

echo "✅ Manual execution test complete"
echo "Check output above for errors"
EOF

    log "✅ Manual test complete"
}

configure_cron() {
    local vm_ip="$1"

    log "Configuring cron job..."

    ssh -i "$SSH_KEY" "$SSH_USER@$vm_ip" << 'EOF'
# Add cron job (every 3 hours)
CRON_ENTRY="0 */3 * * * cd ~ && source ~/.env-motherduck && ~/.local/bin/uv run ~/motherduck_monitor.py >> ~/monitor.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -F "motherduck_monitor.py" > /dev/null; then
    echo "✅ Cron job already exists"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "✅ Cron job added"
fi

# Display crontab
echo "Current crontab:"
crontab -l
EOF

    log "✅ Cron configured"
}

configure_keep_alive() {
    local vm_ip="$1"

    log "Configuring keep-alive mechanism..."

    ssh -i "$SSH_KEY" "$SSH_USER@$vm_ip" << 'EOF'
# Install stress-ng for precise CPU control (optional, fallback to dd+sha256sum if unavailable)
if ! command -v stress-ng &> /dev/null; then
    echo "  Installing stress-ng for CPU control..."
    sudo apt-get update -qq
    sudo apt-get install -y stress-ng 2>&1 | grep -v "^Reading"
    echo "  ✅ stress-ng installed"
else
    echo "  ✅ stress-ng already installed"
fi

# Add keep-alive cron job (every hour)
KEEP_ALIVE_ENTRY="0 * * * * ~/keep_alive.sh >> ~/keep_alive.log 2>&1"

# Check if keep-alive cron job already exists
if crontab -l 2>/dev/null | grep -F "keep_alive.sh" > /dev/null; then
    echo "✅ Keep-alive cron job already exists"
else
    # Add keep-alive cron job
    (crontab -l 2>/dev/null; echo "$KEEP_ALIVE_ENTRY") | crontab -
    echo "✅ Keep-alive cron job added"
fi

# Display crontab
echo "Current crontab:"
crontab -l
EOF

    log "✅ Keep-alive configured"
}

# ================================================================================
# Main Deployment Flow
# ================================================================================

main() {
    log "=" 80
    log "Oracle Cloud MotherDuck Monitor Deployment"
    log "=" 80

    check_prerequisites

    # Get VM public IP
    VM_IP=$(get_vm_public_ip)

    # Deploy
    deploy_scripts "$VM_IP"
    install_dependencies "$VM_IP"
    configure_environment "$VM_IP"

    log ""
    log "✅ Deployment complete"
    log ""
    log "Next steps:"
    log "  1. Edit ~/.env-motherduck on VM to add secret OCIDs:"
    log "     ssh -i $SSH_KEY $SSH_USER@$VM_IP"
    log "     vi ~/.env-motherduck"
    log ""
    log "  2. Test manual execution:"
    log "     ./deploy.sh test"
    log ""
    log "  3. Configure cron:"
    log "     ./deploy.sh cron"
    log ""
    log "  4. Configure keep-alive mechanism (prevents idle reclamation):"
    log "     ./deploy.sh keep-alive"
}

# Handle subcommands
case "${1:-deploy}" in
    deploy)
        main
        ;;
    test)
        VM_IP=$(get_vm_public_ip)
        test_manual_execution "$VM_IP"
        ;;
    cron)
        VM_IP=$(get_vm_public_ip)
        configure_cron "$VM_IP"
        ;;
    keep-alive)
        VM_IP=$(get_vm_public_ip)
        configure_keep_alive "$VM_IP"
        ;;
    *)
        echo "Usage: $0 {deploy|test|cron|keep-alive}"
        exit 1
        ;;
esac
