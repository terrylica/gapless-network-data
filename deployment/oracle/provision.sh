#!/usr/bin/env bash
#
# Oracle Cloud Infrastructure Automated Provisioning
#
# Provisions complete MotherDuck monitoring infrastructure:
# - VCN + Subnet + Internet Gateway + Security Lists
# - VM.Standard.A1.Flex (1 OCPU, 6 GB ARM, Always Free)
# - SSH key pair
# - IAM policies for OCI Vault access
# - Keep-alive mechanism (prevents idle reclamation, no PAYG required)
#
# Prerequisites:
# - OCI CLI installed and configured (~/.oci/config)
# - Doppler secrets configured (MOTHERDUCK_TOKEN, etc.)
#
# Usage:
#   ./provision.sh              # Full provisioning
#   ./provision.sh network      # Network only
#   ./provision.sh vm           # VM only (requires network)
#   ./provision.sh iam          # IAM policies only
#   ./provision.sh status       # Check status

set -euo pipefail

# ================================================================================
# Configuration
# ================================================================================

# VM Configuration
VM_NAME="${OCI_VM_NAME:-motherduck-monitor}"
VM_SHAPE="VM.Standard.A1.Flex"
VM_OCPUS=1
VM_MEMORY_GB=6
VM_IMAGE_OS="Canonical Ubuntu"
VM_IMAGE_VERSION="22.04"
VM_BOOT_VOLUME_GB=50

# Network Configuration
VCN_NAME="motherduck-monitor-vcn"
VCN_CIDR="10.0.0.0/16"
SUBNET_NAME="motherduck-monitor-subnet"
SUBNET_CIDR="10.0.0.0/24"
INTERNET_GATEWAY_NAME="motherduck-monitor-igw"
ROUTE_TABLE_NAME="motherduck-monitor-rt"
SECURITY_LIST_NAME="motherduck-monitor-sl"

# SSH Configuration
SSH_KEY_PATH="${SSH_KEY:-$HOME/.ssh/motherduck-monitor}"
SSH_PUBLIC_KEY_PATH="${SSH_KEY_PATH}.pub"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ================================================================================
# Helper Functions
# ================================================================================

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
    exit 1
}

check_prerequisites() {
    log "Checking prerequisites..."

    # Check OCI CLI
    if ! command -v oci &> /dev/null; then
        error "OCI CLI not installed. Install: brew install oci-cli"
    fi

    # Check OCI config
    if [[ ! -f "$HOME/.oci/config" ]]; then
        error "OCI CLI not configured. Run: oci setup config"
    fi

    # Test OCI authentication
    if ! oci iam region list &> /dev/null; then
        error "OCI authentication failed. Check ~/.oci/config"
    fi

    # Check Doppler
    if ! command -v doppler &> /dev/null; then
        error "Doppler CLI not installed. Install: brew install dopplerhq/cli/doppler"
    fi

    log "✅ Prerequisites OK"
}

get_compartment_id() {
    # Get root compartment (tenancy) OCID
    oci iam compartment list --query 'data[0].id' --raw-output 2>/dev/null || \
        oci iam availability-domain list --query 'data[0]."compartment-id"' --raw-output
}

get_availability_domain() {
    # Get first availability domain in region
    oci iam availability-domain list --query 'data[0].name' --raw-output
}

# ================================================================================
# Network Provisioning
# ================================================================================

provision_network() {
    log "========================================
log "Provisioning Network Infrastructure"
    log "========================================"

    COMPARTMENT_ID=$(get_compartment_id)
    log "Compartment ID: $COMPARTMENT_ID"

    # Step 1: Create VCN
    log "Creating VCN: $VCN_NAME ($VCN_CIDR)"
    VCN_ID=$(oci network vcn list \
        --compartment-id "$COMPARTMENT_ID" \
        --display-name "$VCN_NAME" \
        --query 'data[0].id' \
        --raw-output 2>/dev/null || echo "")

    if [[ -z "$VCN_ID" ]]; then
        VCN_ID=$(oci network vcn create \
            --compartment-id "$COMPARTMENT_ID" \
            --display-name "$VCN_NAME" \
            --cidr-block "$VCN_CIDR" \
            --wait-for-state AVAILABLE \
            --query 'data.id' \
            --raw-output)
        log "✅ VCN created: $VCN_ID"
    else
        log "✅ VCN already exists: $VCN_ID"
    fi

    # Step 2: Create Internet Gateway
    log "Creating Internet Gateway: $INTERNET_GATEWAY_NAME"
    IGW_ID=$(oci network internet-gateway list \
        --compartment-id "$COMPARTMENT_ID" \
        --vcn-id "$VCN_ID" \
        --display-name "$INTERNET_GATEWAY_NAME" \
        --query 'data[0].id' \
        --raw-output 2>/dev/null || echo "")

    if [[ -z "$IGW_ID" ]]; then
        IGW_ID=$(oci network internet-gateway create \
            --compartment-id "$COMPARTMENT_ID" \
            --vcn-id "$VCN_ID" \
            --display-name "$INTERNET_GATEWAY_NAME" \
            --is-enabled true \
            --wait-for-state AVAILABLE \
            --query 'data.id' \
            --raw-output)
        log "✅ Internet Gateway created: $IGW_ID"
    else
        log "✅ Internet Gateway already exists: $IGW_ID"
    fi

    # Step 3: Update default route table
    log "Updating default route table"
    DEFAULT_RT_ID=$(oci network vcn get \
        --vcn-id "$VCN_ID" \
        --query 'data."default-route-table-id"' \
        --raw-output)

    oci network route-table update \
        --rt-id "$DEFAULT_RT_ID" \
        --route-rules "[{\"destination\":\"0.0.0.0/0\",\"networkEntityId\":\"$IGW_ID\"}]" \
        --force \
        > /dev/null 2>&1 || true

    log "✅ Route table updated"

    # Step 4: Update default security list (allow SSH + HTTPS egress)
    log "Updating default security list"
    DEFAULT_SL_ID=$(oci network vcn get \
        --vcn-id "$VCN_ID" \
        --query 'data."default-security-list-id"' \
        --raw-output)

    # Ingress: Allow SSH from anywhere (port 22)
    INGRESS_RULES='[
        {
            "protocol": "6",
            "source": "0.0.0.0/0",
            "tcpOptions": {
                "destinationPortRange": {
                    "min": 22,
                    "max": 22
                }
            }
        }
    ]'

    # Egress: Allow all traffic (required for MotherDuck, Healthchecks.io, Pushover)
    EGRESS_RULES='[
        {
            "protocol": "all",
            "destination": "0.0.0.0/0"
        }
    ]'

    oci network security-list update \
        --security-list-id "$DEFAULT_SL_ID" \
        --ingress-security-rules "$INGRESS_RULES" \
        --egress-security-rules "$EGRESS_RULES" \
        --force \
        > /dev/null 2>&1 || true

    log "✅ Security list updated"

    # Step 5: Create Subnet
    log "Creating Subnet: $SUBNET_NAME ($SUBNET_CIDR)"
    SUBNET_ID=$(oci network subnet list \
        --compartment-id "$COMPARTMENT_ID" \
        --vcn-id "$VCN_ID" \
        --display-name "$SUBNET_NAME" \
        --query 'data[0].id' \
        --raw-output 2>/dev/null || echo "")

    if [[ -z "$SUBNET_ID" ]]; then
        AVAILABILITY_DOMAIN=$(get_availability_domain)

        SUBNET_ID=$(oci network subnet create \
            --compartment-id "$COMPARTMENT_ID" \
            --vcn-id "$VCN_ID" \
            --display-name "$SUBNET_NAME" \
            --cidr-block "$SUBNET_CIDR" \
            --availability-domain "$AVAILABILITY_DOMAIN" \
            --wait-for-state AVAILABLE \
            --query 'data.id' \
            --raw-output)
        log "✅ Subnet created: $SUBNET_ID"
    else
        log "✅ Subnet already exists: $SUBNET_ID"
    fi

    log ""
    log "Network provisioning complete!"
    log "  VCN ID: $VCN_ID"
    log "  Subnet ID: $SUBNET_ID"
    log "  Internet Gateway ID: $IGW_ID"
}

# ================================================================================
# SSH Key Generation
# ================================================================================

generate_ssh_key() {
    log "Generating SSH key pair..."

    if [[ -f "$SSH_KEY_PATH" ]]; then
        log "✅ SSH key already exists: $SSH_KEY_PATH"
        return
    fi

    ssh-keygen -t ed25519 -f "$SSH_KEY_PATH" -N "" -C "motherduck-monitor@oci"
    log "✅ SSH key generated: $SSH_KEY_PATH"
}

# ================================================================================
# VM Provisioning
# ================================================================================

provision_vm() {
    log "========================================"
    log "Provisioning VM"
    log "========================================"

    COMPARTMENT_ID=$(get_compartment_id)
    AVAILABILITY_DOMAIN=$(get_availability_domain)

    # Get VCN and Subnet IDs
    VCN_ID=$(oci network vcn list \
        --compartment-id "$COMPARTMENT_ID" \
        --display-name "$VCN_NAME" \
        --query 'data[0].id' \
        --raw-output 2>/dev/null)

    if [[ -z "$VCN_ID" ]]; then
        error "VCN not found. Run: ./provision.sh network"
    fi

    SUBNET_ID=$(oci network subnet list \
        --compartment-id "$COMPARTMENT_ID" \
        --vcn-id "$VCN_ID" \
        --display-name "$SUBNET_NAME" \
        --query 'data[0].id' \
        --raw-output 2>/dev/null)

    if [[ -z "$SUBNET_ID" ]]; then
        error "Subnet not found. Run: ./provision.sh network"
    fi

    # Check if SSH key exists
    if [[ ! -f "$SSH_PUBLIC_KEY_PATH" ]]; then
        generate_ssh_key
    fi

    # Check if VM already exists
    log "Checking if VM exists: $VM_NAME"
    EXISTING_VM_ID=$(oci compute instance list \
        --compartment-id "$COMPARTMENT_ID" \
        --display-name "$VM_NAME" \
        --lifecycle-state RUNNING \
        --query 'data[0].id' \
        --raw-output 2>/dev/null || echo "")

    if [[ -n "$EXISTING_VM_ID" ]]; then
        log "✅ VM already exists: $EXISTING_VM_ID"
        get_vm_details "$EXISTING_VM_ID"
        return
    fi

    # Get Ubuntu 22.04 image ID
    log "Finding Ubuntu 22.04 image..."
    IMAGE_ID=$(oci compute image list \
        --compartment-id "$COMPARTMENT_ID" \
        --operating-system "$VM_IMAGE_OS" \
        --operating-system-version "$VM_IMAGE_VERSION" \
        --shape "$VM_SHAPE" \
        --sort-by TIMECREATED \
        --sort-order DESC \
        --limit 1 \
        --query 'data[0].id' \
        --raw-output)

    if [[ -z "$IMAGE_ID" ]]; then
        error "Ubuntu 22.04 image not found for shape $VM_SHAPE"
    fi

    log "✅ Image found: $IMAGE_ID"

    # Create VM
    log "Creating VM: $VM_NAME"
    log "  Shape: $VM_SHAPE ($VM_OCPUS OCPU, ${VM_MEMORY_GB}GB RAM)"
    log "  Availability Domain: $AVAILABILITY_DOMAIN"

    VM_ID=$(oci compute instance launch \
        --compartment-id "$COMPARTMENT_ID" \
        --availability-domain "$AVAILABILITY_DOMAIN" \
        --shape "$VM_SHAPE" \
        --shape-config "{\"ocpus\":$VM_OCPUS,\"memoryInGBs\":$VM_MEMORY_GB}" \
        --display-name "$VM_NAME" \
        --image-id "$IMAGE_ID" \
        --subnet-id "$SUBNET_ID" \
        --assign-public-ip true \
        --ssh-authorized-keys-file "$SSH_PUBLIC_KEY_PATH" \
        --boot-volume-size-in-gbs "$VM_BOOT_VOLUME_GB" \
        --wait-for-state RUNNING \
        --query 'data.id' \
        --raw-output)

    log "✅ VM created: $VM_ID"

    # Wait for VM to be fully ready
    log "Waiting for VM to be fully ready..."
    sleep 30

    get_vm_details "$VM_ID"
}

get_vm_details() {
    local vm_id="$1"

    # Get VNIC attachment
    COMPARTMENT_ID=$(get_compartment_id)
    VNIC_ID=$(oci compute vnic-attachment list \
        --compartment-id "$COMPARTMENT_ID" \
        --instance-id "$vm_id" \
        --query 'data[0]."vnic-id"' \
        --raw-output)

    # Get public IP
    PUBLIC_IP=$(oci network vnic get \
        --vnic-id "$VNIC_ID" \
        --query 'data."public-ip"' \
        --raw-output)

    log ""
    log "VM Details:"
    log "  VM ID: $vm_id"
    log "  Public IP: $PUBLIC_IP"
    log "  SSH Command: ssh -i $SSH_KEY_PATH opc@$PUBLIC_IP"
    log ""

    # Save to file for easy access
    cat > "$HOME/.oci/motherduck-monitor-vm.env" <<EOF
VM_ID=$vm_id
VM_NAME=$VM_NAME
VM_PUBLIC_IP=$PUBLIC_IP
SSH_KEY=$SSH_KEY_PATH
SSH_USER=opc
EOF

    log "✅ VM details saved to ~/.oci/motherduck-monitor-vm.env"
}

# ================================================================================
# IAM Policies
# ================================================================================

provision_iam_policies() {
    log "========================================"
    log "Provisioning IAM Policies"
    log "========================================"

    COMPARTMENT_ID=$(get_compartment_id)

    # Policy: Allow VM to read secrets from OCI Vault
    POLICY_NAME="motherduck-monitor-secrets-access"
    log "Creating IAM policy: $POLICY_NAME"

    # Check if policy exists
    EXISTING_POLICY_ID=$(oci iam policy list \
        --compartment-id "$COMPARTMENT_ID" \
        --name "$POLICY_NAME" \
        --query 'data[0].id' \
        --raw-output 2>/dev/null || echo "")

    if [[ -n "$EXISTING_POLICY_ID" ]]; then
        log "✅ IAM policy already exists: $EXISTING_POLICY_ID"
        return
    fi

    # Create policy allowing any instance to read secrets
    POLICY_STATEMENTS="[
        \"Allow any-user to read secret-bundles in compartment id $COMPARTMENT_ID where request.principal.type='instance'\",
        \"Allow any-user to read secrets in compartment id $COMPARTMENT_ID where request.principal.type='instance'\"
    ]"

    POLICY_ID=$(oci iam policy create \
        --compartment-id "$COMPARTMENT_ID" \
        --name "$POLICY_NAME" \
        --description "Allow motherduck-monitor VM to read secrets from OCI Vault" \
        --statements "$POLICY_STATEMENTS" \
        --query 'data.id' \
        --raw-output)

    log "✅ IAM policy created: $POLICY_ID"
}

# ================================================================================
# Keep-Alive Information
# ================================================================================

show_keep_alive_info() {
    log "========================================"
    log "Keep-Alive Mechanism (No PAYG Required)"
    log "========================================"

    log "Oracle reclaims idle VMs with <20% CPU/network/memory for 7 consecutive days."
    log "This deployment includes keep_alive.sh to prevent reclamation."
    log ""
    log "Keep-Alive Strategy:"
    log "  - Runs every hour via cron"
    log "  - Uses ~25% CPU for 30 seconds"
    log "  - Maintains >20% threshold to prevent reclamation"
    log "  - Cost: $0 (within Always Free Tier limits)"
    log ""
    log "Configuration:"
    log "  - Script: ~/keep_alive.sh on VM"
    log "  - Schedule: 0 * * * * (hourly)"
    log "  - Logs: ~/keep_alive.log"
    log ""
    log "Alternative: Upgrade to PAYG to avoid reclamation risk entirely"
    log "  (No charges for Always Free resources)"
    log ""
}

# ================================================================================
# Status Check
# ================================================================================

check_status() {
    log "========================================"
    log "Infrastructure Status"
    log "========================================"

    COMPARTMENT_ID=$(get_compartment_id)

    # Check VCN
    VCN_ID=$(oci network vcn list \
        --compartment-id "$COMPARTMENT_ID" \
        --display-name "$VCN_NAME" \
        --query 'data[0].id' \
        --raw-output 2>/dev/null || echo "")

    if [[ -n "$VCN_ID" ]]; then
        log "✅ VCN: $VCN_NAME ($VCN_ID)"
    else
        log "❌ VCN: Not found"
    fi

    # Check VM
    VM_ID=$(oci compute instance list \
        --compartment-id "$COMPARTMENT_ID" \
        --display-name "$VM_NAME" \
        --lifecycle-state RUNNING \
        --query 'data[0].id' \
        --raw-output 2>/dev/null || echo "")

    if [[ -n "$VM_ID" ]]; then
        log "✅ VM: $VM_NAME ($VM_ID)"
        get_vm_details "$VM_ID"
    else
        log "❌ VM: Not found or not running"
    fi

    # Check IAM policy
    POLICY_ID=$(oci iam policy list \
        --compartment-id "$COMPARTMENT_ID" \
        --name "motherduck-monitor-secrets-access" \
        --query 'data[0].id' \
        --raw-output 2>/dev/null || echo "")

    if [[ -n "$POLICY_ID" ]]; then
        log "✅ IAM Policy: motherduck-monitor-secrets-access ($POLICY_ID)"
    else
        log "❌ IAM Policy: Not found"
    fi

    # Check SSH key
    if [[ -f "$SSH_KEY_PATH" ]]; then
        log "✅ SSH Key: $SSH_KEY_PATH"
    else
        log "❌ SSH Key: Not found"
    fi

    log ""
}

# ================================================================================
# Main Orchestration
# ================================================================================

full_provision() {
    log "========================================"
    log "Full Infrastructure Provisioning"
    log "========================================"
    log ""

    check_prerequisites
    echo ""

    provision_network
    echo ""

    generate_ssh_key
    echo ""

    provision_vm
    echo ""

    provision_iam_policies
    echo ""

    show_keep_alive_info
    echo ""

    log "========================================"
    log "Provisioning Complete!"
    log "========================================"
    log ""
    log "Next steps:"
    log "  1. Migrate secrets: cd deployment/oracle && uv run migrate_secrets.py"
    log "  2. Deploy monitoring: ./deploy.sh deploy"
    log "  3. Configure secrets on VM: vi ~/.env-motherduck"
    log "  4. Test: ./deploy.sh test"
    log "  5. Configure monitoring cron: ./deploy.sh cron"
    log "  6. Configure keep-alive: ./deploy.sh keep-alive"
    log ""
}

# ================================================================================
# CLI Interface
# ================================================================================

case "${1:-full}" in
    full)
        full_provision
        ;;
    network)
        check_prerequisites
        provision_network
        ;;
    ssh-key)
        generate_ssh_key
        ;;
    vm)
        check_prerequisites
        provision_vm
        ;;
    iam)
        check_prerequisites
        provision_iam_policies
        ;;
    keep-alive-info)
        show_keep_alive_info
        ;;
    status)
        check_prerequisites
        check_status
        ;;
    *)
        echo "Usage: $0 {full|network|ssh-key|vm|iam|keep-alive-info|status}"
        echo ""
        echo "Commands:"
        echo "  full            - Full infrastructure provisioning (default)"
        echo "  network         - Provision network only (VCN, subnet, gateway)"
        echo "  ssh-key         - Generate SSH key pair"
        echo "  vm              - Provision VM only (requires network)"
        echo "  iam             - Provision IAM policies only"
        echo "  keep-alive-info - Show keep-alive mechanism information"
        echo "  status          - Check infrastructure status"
        exit 1
        ;;
esac
