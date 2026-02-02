#!/bin/bash

# Script to access Kubernetes from MacBook
# Supports two modes:
# 1. Direct access: MacBook -> kube-master (via vagrant ssh, if Vagrantfile is available)
# 2. Indirect access: MacBook -> my-ubuntu -> kube-master (via SSH tunnel)
# Also includes kubectl port-forward for Ingress services

# Access mode: "direct" (use vagrant ssh) or "indirect" (via my-ubuntu)
ACCESS_MODE="${ACCESS_MODE:-auto}"  # auto, direct, indirect

MY_UBUNTU_HOST="my-ubuntu"  # SSH hostname or IP (for indirect mode)
MY_UBUNTU_USER="${USER}"     # my-ubuntu username (modify if needed)
LOCAL_PORT="6443"            # Local port on MacBook
REMOTE_PORT="6443"           # Local port on my-ubuntu (kube-master tunnel port, indirect mode only)
KUBECONFIG_HOST_PATH="$HOME/.kube/my-ubuntu.config"
KUBECONFIG_VM_PATH="/root/.kube/config"
TUNNEL_PID_FILE="/tmp/k8s-ssh-tunnel-from-mac.pid"
SSH_TIMEOUT=10               # SSH connection timeout in seconds

# Direct access settings (Vagrant)
VAGRANT_DIR="$HOME/workspaces/tz-k8s-vagrant"

# Ingress port-forward settings
INGRESS_DEFAULT_NAMESPACE="default"
INGRESS_DEFAULT_SERVICE_NAME="ingress-nginx-controller"
INGRESS_HTTP_LOCAL_PORT="8080"
INGRESS_HTTPS_LOCAL_PORT="8443"
INGRESS_PID_FILE="/tmp/k8s-ingress-port-forward.pid"

export KUBECONFIG="$KUBECONFIG_HOST_PATH"

# Function: Detect access mode automatically
detect_access_mode() {
    if [ "$ACCESS_MODE" != "auto" ]; then
        echo "$ACCESS_MODE"
        return 0
    fi
    
    # Check if Vagrantfile exists and kube-master VM is accessible
    if [ -f "$VAGRANT_DIR/Vagrantfile" ]; then
        if command -v vagrant > /dev/null 2>&1; then
            # Check if kube-master VM exists and is accessible
            if (cd "$VAGRANT_DIR" && vagrant status kube-master 2>/dev/null | grep -q "running\|poweroff"); then
                echo "direct"
                return 0
            fi
        fi
    fi
    
    # Check if my-ubuntu is reachable
    if ssh -o ConnectTimeout=$SSH_TIMEOUT -o BatchMode=yes "$MY_UBUNTU_HOST" "echo 'OK'" > /dev/null 2>&1; then
        echo "indirect"
        return 0
    fi
    
    # Default to indirect if neither is clearly available
    echo "indirect"
}

# Function: Check if my-ubuntu host is reachable
check_host_connectivity() {
    echo "Checking connectivity to $MY_UBUNTU_HOST..."
    
    # Try SSH connection with timeout
    if ssh -o ConnectTimeout=$SSH_TIMEOUT -o BatchMode=yes "$MY_UBUNTU_HOST" "echo 'OK'" > /dev/null 2>&1; then
        echo "✓ $MY_UBUNTU_HOST is reachable via SSH"
        return 0
    else
        echo "✗ Error: Cannot connect to $MY_UBUNTU_HOST"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Check if the host is powered on: ping $MY_UBUNTU_HOST"
        echo "  2. Check SSH configuration: ssh -v $MY_UBUNTU_HOST"
        echo "  3. Verify network connectivity"
        echo "  4. Check SSH hostname/IP in ~/.ssh/config or /etc/hosts"
        return 1
    fi
}

# Function: Start SSH tunnel (direct mode: MacBook -> kube-master)
start_tunnel_direct() {
    echo "Starting SSH tunnel (MacBook -> kube-master, direct mode)..."
    
    # Check if tunnel already exists
    if [ -f "$TUNNEL_PID_FILE" ]; then
        OLD_PID=$(cat "$TUNNEL_PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            echo "SSH tunnel is already running. PID: $OLD_PID"
            return 0
        else
            rm -f "$TUNNEL_PID_FILE"
        fi
    fi
    
    # Check if port is already in use
    if command -v lsof > /dev/null 2>&1; then
        EXISTING_PID=$(lsof -ti :$LOCAL_PORT 2>/dev/null | head -1)
        if [ -n "$EXISTING_PID" ]; then
            # Check if existing process is our tunnel
            EXISTING_CMD=$(ps -p "$EXISTING_PID" -o command= 2>/dev/null | grep -E "ssh.*${LOCAL_PORT}.*kube-master|vagrant.*ssh.*kube-master" || echo "")
            if [ -n "$EXISTING_CMD" ]; then
                echo "Existing SSH tunnel is running. PID: $EXISTING_PID (reusing)"
                echo "$EXISTING_PID" > "$TUNNEL_PID_FILE"
                return 0
            else
                echo "Warning: Port $LOCAL_PORT is in use by another process. (PID: $EXISTING_PID)"
                echo "Please use a different port or stop the existing process."
                return 1
            fi
        fi
    fi
    
    # Check if Vagrantfile exists
    if [ ! -f "$VAGRANT_DIR/Vagrantfile" ]; then
        echo "Error: Vagrantfile not found at $VAGRANT_DIR"
        echo "Please set VAGRANT_DIR or use indirect mode (ACCESS_MODE=indirect)"
        return 1
    fi
    
    # Check if vagrant is installed
    if ! command -v vagrant > /dev/null 2>&1; then
        echo "Error: vagrant is not installed"
        echo "Please install vagrant or use indirect mode (ACCESS_MODE=indirect)"
        return 1
    fi
    
    # Start SSH tunnel using vagrant ssh
    echo "Starting tunnel via vagrant ssh..."
    (cd "$VAGRANT_DIR" && vagrant ssh kube-master -- -L $LOCAL_PORT:127.0.0.1:6443 -N -f) 2>&1
    
    if [ $? -eq 0 ]; then
        sleep 1
        PID=$(ps aux | grep -E "[s]sh.*${LOCAL_PORT}:127.0.0.1:6443.*kube-master|vagrant.*ssh.*kube-master" | awk '{print $2}' | head -1)
        if [ -n "$PID" ]; then
            echo "$PID" > "$TUNNEL_PID_FILE"
            echo "SSH tunnel started. PID: $PID"
            echo "MacBook localhost:${LOCAL_PORT} -> kube-master:6443 (direct)"
            return 0
        else
            echo "Warning: SSH process started but PID not found."
            echo "Check manually: ps aux | grep ssh | grep ${LOCAL_PORT}"
        fi
    else
        echo "Error: Failed to start SSH tunnel via vagrant ssh"
        return 1
    fi
    
    return 1
}

# Function: Start SSH tunnel (indirect mode: MacBook -> my-ubuntu -> kube-master)
start_tunnel_indirect() {
    echo "Starting SSH tunnel (MacBook -> my-ubuntu -> kube-master, indirect mode)..."
    
    # First, check if kube-master tunnel is running on my-ubuntu
    # This is critical - without it, the MacBook tunnel won't work
    echo "Checking kube-master tunnel status on my-ubuntu..."
    # access-k8s-from-host.sh is in tz-drillquiz/provisioning
    TUNNEL_STATUS=$(ssh -o ConnectTimeout=$SSH_TIMEOUT "$MY_UBUNTU_HOST" "
        if [ -f ~/workspaces/tz-drillquiz/provisioning/access-k8s-from-host.sh ]; then
            cd ~/workspaces/tz-drillquiz/provisioning && ./access-k8s-from-host.sh status 2>&1
        else
            echo 'Error: access-k8s-from-host.sh not found (expected in tz-drillquiz/provisioning)'
            exit 1
        fi
    " 2>&1)
    SSH_EXIT_CODE=$?
    
    if [ $SSH_EXIT_CODE -ne 0 ]; then
        echo "Error: Failed to check tunnel status on $MY_UBUNTU_HOST"
        echo "SSH error output: $TUNNEL_STATUS"
        return 1
    fi
    
    TUNNEL_EXISTS=$(echo "$TUNNEL_STATUS" | grep -i "실행 중\|running" || echo "")
    
    # Check if tunnel already exists on MacBook
    if [ -f "$TUNNEL_PID_FILE" ]; then
        OLD_PID=$(cat "$TUNNEL_PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            if [ -z "$TUNNEL_EXISTS" ]; then
                echo "Warning: MacBook tunnel is running (PID: $OLD_PID) but kube-master tunnel on my-ubuntu is not running."
                echo "This will cause connection failures. Restarting MacBook tunnel..."
                kill "$OLD_PID" 2>/dev/null
                rm -f "$TUNNEL_PID_FILE"
            else
                echo "SSH tunnel is already running. PID: $OLD_PID"
                echo "kube-master tunnel is also running on my-ubuntu."
                
                # Verify the tunnel is actually working by testing local port
                if command -v nc > /dev/null 2>&1; then
                    if nc -z -w 2 127.0.0.1 $LOCAL_PORT 2>/dev/null; then
                        echo "✓ Local tunnel port $LOCAL_PORT is accessible."
                        return 0
                    else
                        echo "⚠ Warning: Tunnel process exists but port $LOCAL_PORT is not accessible."
                        echo "Restarting tunnel..."
                        kill "$OLD_PID" 2>/dev/null
                        rm -f "$TUNNEL_PID_FILE"
                        # Continue to start new tunnel below
                    fi
                else
                    # If nc is not available, assume tunnel is working
                    return 0
                fi
            fi
        else
            rm -f "$TUNNEL_PID_FILE"
        fi
    fi
    
    # Check if port is already in use
    if command -v lsof > /dev/null 2>&1; then
        EXISTING_PID=$(lsof -ti :$LOCAL_PORT 2>/dev/null | head -1)
        if [ -n "$EXISTING_PID" ]; then
            # Check if existing process is our tunnel
            EXISTING_CMD=$(ps -p "$EXISTING_PID" -o command= 2>/dev/null | grep -E "ssh.*${LOCAL_PORT}.*${MY_UBUNTU_HOST}" || echo "")
            if [ -n "$EXISTING_CMD" ]; then
                if [ -z "$TUNNEL_EXISTS" ]; then
                    echo "Warning: MacBook tunnel exists (PID: $EXISTING_PID) but kube-master tunnel on my-ubuntu is not running."
                    echo "Killing existing tunnel to restart properly..."
                    kill "$EXISTING_PID" 2>/dev/null
                    sleep 1
                else
                    echo "Existing SSH tunnel is running. PID: $EXISTING_PID (reusing)"
                    echo "$EXISTING_PID" > "$TUNNEL_PID_FILE"
                    return 0
                fi
            else
                echo "Warning: Port $LOCAL_PORT is in use by another process. (PID: $EXISTING_PID)"
                echo "Please use a different port or stop the existing process."
                return 1
            fi
        fi
    fi
    
    if [ -z "$TUNNEL_EXISTS" ]; then
        echo "Starting kube-master tunnel on my-ubuntu..."
        TUNNEL_START_OUTPUT=$(ssh -o ConnectTimeout=$SSH_TIMEOUT "$MY_UBUNTU_HOST" "
            if [ -f ~/workspaces/tz-drillquiz/provisioning/access-k8s-from-host.sh ]; then
                cd ~/workspaces/tz-drillquiz/provisioning && ./access-k8s-from-host.sh start 2>&1
            else
                echo 'Error: access-k8s-from-host.sh not found (expected in tz-drillquiz/provisioning)'
                exit 1
            fi
        " 2>&1)
        TUNNEL_START_EXIT_CODE=$?
        
        if [ $TUNNEL_START_EXIT_CODE -ne 0 ]; then
            echo "Error: Failed to start kube-master tunnel on $MY_UBUNTU_HOST"
            echo "Output: $TUNNEL_START_OUTPUT"
            echo ""
            if echo "$TUNNEL_START_OUTPUT" | grep -qi "Unable to read kubeconfig\|connection refused\|VM"; then
                echo "Possible causes:"
                echo "  1. kube-master VM is not running on $MY_UBUNTU_HOST"
                echo "  2. VM is not accessible from $MY_UBUNTU_HOST"
                echo "  3. Please check VM status: ssh $MY_UBUNTU_HOST 'vagrant status' (if using Vagrant)"
            fi
            return 1
        fi
        
        # Verify tunnel is actually running
        sleep 3
        echo "Verifying kube-master tunnel is running..."
        VERIFY_STATUS=$(ssh -o ConnectTimeout=$SSH_TIMEOUT "$MY_UBUNTU_HOST" "
            if [ -f ~/workspaces/tz-drillquiz/provisioning/access-k8s-from-host.sh ]; then
                cd ~/workspaces/tz-drillquiz/provisioning && ./access-k8s-from-host.sh status 2>&1
            else
                echo 'Error: access-k8s-from-host.sh not found'
                exit 1
            fi
        " 2>&1)
        VERIFY_EXISTS=$(echo "$VERIFY_STATUS" | grep -i "실행 중\|running" || echo "")
        
        if [ -z "$VERIFY_EXISTS" ]; then
            echo "Warning: Tunnel start command succeeded but tunnel is not running."
            echo "Status output: $VERIFY_STATUS"
            return 1
        fi
        echo "✓ kube-master tunnel is now running on my-ubuntu."
    else
        echo "kube-master tunnel is already running on my-ubuntu."
        
        # Verify tunnel is actually working by checking if port is accessible
        echo "Verifying tunnel connectivity..."
        if ssh -o ConnectTimeout=5 "$MY_UBUNTU_HOST" "timeout 2 bash -c '</dev/tcp/127.0.0.1/6443' 2>/dev/null" 2>/dev/null; then
            echo "✓ Tunnel port 6443 is accessible on my-ubuntu."
        else
            echo "⚠ Warning: Tunnel is reported as running but port 6443 is not accessible."
            echo "The tunnel may not be working correctly. Trying to restart..."
            RESTART_OUTPUT=$(ssh -o ConnectTimeout=$SSH_TIMEOUT "$MY_UBUNTU_HOST" "
                if [ -f ~/workspaces/tz-drillquiz/provisioning/access-k8s-from-host.sh ]; then
                    cd ~/workspaces/tz-drillquiz/provisioning && ./access-k8s-from-host.sh restart 2>&1
                else
                    echo 'Error: access-k8s-from-host.sh not found'
                    exit 1
                fi
            " 2>&1)
            echo "$RESTART_OUTPUT"
            sleep 3
            
            # Verify restart was successful
            VERIFY_STATUS=$(ssh -o ConnectTimeout=$SSH_TIMEOUT "$MY_UBUNTU_HOST" "
                if [ -f ~/workspaces/tz-drillquiz/provisioning/access-k8s-from-host.sh ]; then
                    cd ~/workspaces/tz-drillquiz/provisioning && ./access-k8s-from-host.sh status 2>&1
                else
                    echo 'Error: access-k8s-from-host.sh not found'
                    exit 1
                fi
            " 2>&1)
            VERIFY_EXISTS=$(echo "$VERIFY_STATUS" | grep -i "실행 중\|running" || echo "")
            if [ -z "$VERIFY_EXISTS" ]; then
                echo "Error: Failed to restart kube-master tunnel on my-ubuntu."
                return 1
            fi
            echo "✓ kube-master tunnel restarted successfully."
        fi
    fi
    
    # Start MacBook -> my-ubuntu SSH tunnel
    # Forward my-ubuntu's 127.0.0.1:6443 to MacBook's 127.0.0.1:6443
    echo "Starting MacBook -> my-ubuntu SSH tunnel..."
    ssh -o ConnectTimeout=$SSH_TIMEOUT -f -N -L ${LOCAL_PORT}:127.0.0.1:${REMOTE_PORT} "$MY_UBUNTU_HOST" 2>&1
    
    TUNNEL_EXIT_CODE=$?
    if [ $TUNNEL_EXIT_CODE -eq 0 ]; then
        sleep 2
        PID=$(ps aux | grep -E "[s]sh.*${LOCAL_PORT}:127.0.0.1:${REMOTE_PORT}.*${MY_UBUNTU_HOST}" | grep -v grep | awk '{print $2}' | head -1)
        if [ -n "$PID" ]; then
            echo "$PID" > "$TUNNEL_PID_FILE"
            echo "SSH tunnel started. PID: $PID"
            echo "MacBook localhost:${LOCAL_PORT} -> my-ubuntu:${REMOTE_PORT} -> kube-master:6443"
            return 0
        else
            echo "Warning: SSH process started but PID not found."
            echo "Check manually: ps aux | grep ssh | grep ${LOCAL_PORT}"
        fi
    else
        echo "Warning: SSH tunnel command failed. (exit code: $TUNNEL_EXIT_CODE)"
    fi
    
    echo "Error: Failed to start SSH tunnel."
    return 1
}

# Function: Start SSH tunnel (wrapper that selects mode)
start_tunnel() {
    MODE=$(detect_access_mode)
    
    if [ "$MODE" = "direct" ]; then
        start_tunnel_direct
    else
        start_tunnel_indirect
    fi
}

# Function: Stop SSH tunnel
stop_tunnel() {
    if [ -f "$TUNNEL_PID_FILE" ]; then
        PID=$(cat "$TUNNEL_PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID"
            echo "SSH tunnel stopped. PID: $PID"
        else
            echo "SSH tunnel is not running."
        fi
        rm -f "$TUNNEL_PID_FILE"
    else
        # Try to find and stop tunnel (both direct and indirect modes)
        PID=$(ps aux | grep -E "[s]sh.*${LOCAL_PORT}:127.0.0.1:${REMOTE_PORT}.*${MY_UBUNTU_HOST}|[s]sh.*${LOCAL_PORT}:127.0.0.1:6443.*kube-master|vagrant.*ssh.*kube-master" | grep -v grep | awk '{print $2}' | head -1)
        if [ -n "$PID" ]; then
            kill "$PID"
            echo "SSH tunnel stopped. PID: $PID"
        else
            echo "No SSH tunnel is running."
        fi
    fi
}

# Function: Copy kubeconfig (direct mode: from kube-master VM)
copy_kubeconfig_direct() {
    echo "=========================================="
    echo "Copying kubeconfig (from kube-master VM, direct mode)..."
    echo "=========================================="
    
    # Check if Vagrantfile exists
    if [ ! -f "$VAGRANT_DIR/Vagrantfile" ]; then
        echo "Error: Vagrantfile not found at $VAGRANT_DIR"
        return 1
    fi
    
    # Check if vagrant is installed
    if ! command -v vagrant > /dev/null 2>&1; then
        echo "Error: vagrant is not installed"
        return 1
    fi
    
    # Get kubeconfig from kube-master VM
    echo "Reading kubeconfig from kube-master VM..."
    (cd "$VAGRANT_DIR" && vagrant ssh kube-master -c "sudo cat $KUBECONFIG_VM_PATH") > /tmp/kubeconfig_temp 2>&1
    VAGRANT_EXIT_CODE=$?
    
    if [ $VAGRANT_EXIT_CODE -ne 0 ] || [ ! -s /tmp/kubeconfig_temp ]; then
        echo "Error: Unable to read kubeconfig file from kube-master VM"
        if [ $VAGRANT_EXIT_CODE -ne 0 ]; then
            echo "Vagrant command failed (exit code: $VAGRANT_EXIT_CODE)"
            cat /tmp/kubeconfig_temp 2>/dev/null | head -5
        elif [ ! -s /tmp/kubeconfig_temp ]; then
            echo "kubeconfig file is empty or does not exist on kube-master VM"
        fi
        echo ""
        echo "Please ensure:"
        echo "  1. kube-master VM is running: cd $VAGRANT_DIR && vagrant status"
        echo "  2. VM is accessible: cd $VAGRANT_DIR && vagrant ssh kube-master"
        echo "  3. Check if $KUBECONFIG_VM_PATH exists on kube-master VM"
        rm -f /tmp/kubeconfig_temp
        return 1
    fi
    
    mkdir -p "$HOME/.kube"
    cp /tmp/kubeconfig_temp "$KUBECONFIG_HOST_PATH"
    
    # Change server address to MacBook's localhost:6443
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|server: https://.*:6443|server: https://127.0.0.1:$LOCAL_PORT|g" "$KUBECONFIG_HOST_PATH"
    else
        sed -i "s|server: https://.*:6443|server: https://127.0.0.1:$LOCAL_PORT|g" "$KUBECONFIG_HOST_PATH"
    fi
    
    chmod 600 "$KUBECONFIG_HOST_PATH"
    rm -f /tmp/kubeconfig_temp
    
    echo "kubeconfig copied to: $KUBECONFIG_HOST_PATH"
    echo ""
    echo "Usage:"
    echo "  export KUBECONFIG=\"$KUBECONFIG_HOST_PATH\""
    echo "  kubectl get nodes"
    return 0
}

# Function: Copy kubeconfig (indirect mode: from my-ubuntu)
copy_kubeconfig_indirect() {
    echo "=========================================="
    echo "Copying kubeconfig (from my-ubuntu, indirect mode)..."
    echo "=========================================="
    
    # Check host connectivity first
    if ! check_host_connectivity; then
        return 1
    fi
    
    # Get kubeconfig from my-ubuntu (use ~/.kube/config on my-ubuntu)
    echo "Reading kubeconfig from $MY_UBUNTU_HOST..."
    ssh -o ConnectTimeout=$SSH_TIMEOUT "$MY_UBUNTU_HOST" "cat ~/.kube/config" > /tmp/kubeconfig_temp 2>&1
    SSH_EXIT_CODE=$?
    
    if [ $SSH_EXIT_CODE -ne 0 ] || [ ! -s /tmp/kubeconfig_temp ]; then
        echo "Error: Unable to read kubeconfig file from $MY_UBUNTU_HOST"
        if [ $SSH_EXIT_CODE -ne 0 ]; then
            echo "SSH connection failed (exit code: $SSH_EXIT_CODE)"
            cat /tmp/kubeconfig_temp 2>/dev/null | head -5
        elif [ ! -s /tmp/kubeconfig_temp ]; then
            echo "kubeconfig file is empty or does not exist on $MY_UBUNTU_HOST"
        fi
        echo ""
        echo "Please ensure:"
        echo "  1. $MY_UBUNTU_HOST is accessible via SSH"
        echo "  2. On $MY_UBUNTU_HOST run: cd ~/workspaces/tz-drillquiz/provisioning && ./access-k8s-from-host.sh start"
        echo "  3. Check if ~/.kube/config exists on $MY_UBUNTU_HOST"
        rm -f /tmp/kubeconfig_temp
        return 1
    fi
    
    mkdir -p "$HOME/.kube"
    cp /tmp/kubeconfig_temp "$KUBECONFIG_HOST_PATH"
    
    # Change server address to MacBook's localhost:6443
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|server: https://.*:6443|server: https://127.0.0.1:$LOCAL_PORT|g" "$KUBECONFIG_HOST_PATH"
    else
        sed -i "s|server: https://.*:6443|server: https://127.0.0.1:$LOCAL_PORT|g" "$KUBECONFIG_HOST_PATH"
    fi
    
    chmod 600 "$KUBECONFIG_HOST_PATH"
    rm -f /tmp/kubeconfig_temp
    
    echo "kubeconfig copied to: $KUBECONFIG_HOST_PATH"
    echo ""
    echo "Usage:"
    echo "  export KUBECONFIG=\"$KUBECONFIG_HOST_PATH\""
    echo "  kubectl get nodes"
    return 0
}

# Function: Copy kubeconfig (wrapper that selects mode)
copy_kubeconfig() {
    MODE=$(detect_access_mode)
    
    if [ "$MODE" = "direct" ]; then
        copy_kubeconfig_direct
    else
        copy_kubeconfig_indirect
    fi
}

# Function: Test connection
test_connection() {
    echo "Testing connection..."
    if command -v kubectl > /dev/null 2>&1; then
        # Use timeout to avoid hanging
        KUBECTL_OUTPUT=$(timeout 10 kubectl --kubeconfig="$KUBECONFIG_HOST_PATH" get nodes 2>&1)
        KUBECTL_EXIT_CODE=$?
        
        if [ $KUBECTL_EXIT_CODE -eq 0 ]; then
            echo "$KUBECTL_OUTPUT"
            echo "Connection successful!"
            return 0
        else
            echo "$KUBECTL_OUTPUT"
            echo "Connection failed. Exit code: $KUBECTL_EXIT_CODE"
            
            # Check if it's a timeout or connection issue
            if echo "$KUBECTL_OUTPUT" | grep -qi "timeout\|handshake\|connection refused\|connection reset"; then
                echo ""
                echo "Detected connection issue. Attempting to restart tunnel..."
                stop_tunnel
                sleep 2
                if start_tunnel; then
                    sleep 3
                    echo "Retrying connection test..."
                    KUBECTL_OUTPUT=$(timeout 10 kubectl --kubeconfig="$KUBECONFIG_HOST_PATH" get nodes 2>&1)
                    if [ $? -eq 0 ]; then
                        echo "$KUBECTL_OUTPUT"
                        echo "Connection successful after tunnel restart!"
                        return 0
                    else
                        echo "$KUBECTL_OUTPUT"
                        echo "Connection still failed after tunnel restart."
                    fi
                fi
            fi
            
            return 1
        fi
    else
        echo "Warning: kubectl is not installed."
        echo "Please install kubectl or check the path."
        echo "macOS: brew install kubectl"
        return 1
    fi
}

# Function: Start ingress port-forward
start_ingress_portforward() {
    local SERVICE_NAME="${1:-$INGRESS_DEFAULT_SERVICE_NAME}"
    local NAMESPACE="${2:-$INGRESS_DEFAULT_NAMESPACE}"
    
    echo "Starting kubectl port-forward for service: $SERVICE_NAME (namespace: $NAMESPACE)..."
    
    # Check if kubeconfig exists
    if [ ! -f "$KUBECONFIG_HOST_PATH" ]; then
        echo "Error: kubeconfig file not found: $KUBECONFIG_HOST_PATH"
        echo "Please run '$0 start' first to set up kubeconfig and SSH tunnel."
        return 1
    fi
    
    # Check if port-forward already exists
    if [ -f "$INGRESS_PID_FILE" ]; then
        OLD_PID=$(cat "$INGRESS_PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            echo "Ingress port-forward is already running. PID: $OLD_PID"
            echo "Ports: localhost:$INGRESS_HTTP_LOCAL_PORT (HTTP), localhost:$INGRESS_HTTPS_LOCAL_PORT (HTTPS)"
            return 0
        else
            rm -f "$INGRESS_PID_FILE"
        fi
    fi
    
    # Check if ports are already in use and stop existing port-forwards
    if command -v lsof > /dev/null 2>&1; then
        HTTP_PID=$(lsof -ti :$INGRESS_HTTP_LOCAL_PORT 2>/dev/null | head -1)
        HTTPS_PID=$(lsof -ti :$INGRESS_HTTPS_LOCAL_PORT 2>/dev/null | head -1)
        
        if [ -n "$HTTP_PID" ]; then
            # Check if it's a kubectl port-forward process
            if ps -p "$HTTP_PID" > /dev/null 2>&1; then
                CMD=$(ps -p "$HTTP_PID" -o command= 2>/dev/null)
                if echo "$CMD" | grep -q "kubectl.*port-forward"; then
                    echo "Stopping existing port-forward on port $INGRESS_HTTP_LOCAL_PORT (PID: $HTTP_PID)..."
                    kill "$HTTP_PID" 2>/dev/null
                    sleep 1
                fi
            fi
        fi
        
        if [ -n "$HTTPS_PID" ] && [ "$HTTPS_PID" != "$HTTP_PID" ]; then
            # Check if it's a kubectl port-forward process
            if ps -p "$HTTPS_PID" > /dev/null 2>&1; then
                CMD=$(ps -p "$HTTPS_PID" -o command= 2>/dev/null)
                if echo "$CMD" | grep -q "kubectl.*port-forward"; then
                    echo "Stopping existing port-forward on port $INGRESS_HTTPS_LOCAL_PORT (PID: $HTTPS_PID)..."
                    kill "$HTTPS_PID" 2>/dev/null
                    sleep 1
                fi
            fi
        fi
        
        # Also stop any existing kubectl port-forward processes (like original script)
        EXISTING_PF_PIDS=$(ps aux | grep -E "[k]ubectl.*port-forward" | awk '{print $2}')
        if [ -n "$EXISTING_PF_PIDS" ]; then
            echo "Stopping all existing kubectl port-forward processes..."
            echo "$EXISTING_PF_PIDS" | xargs kill 2>/dev/null
            sleep 1
        fi
        
        # Clean up any PID files
        rm -f /tmp/k8s-port-forward-*.pid 2>/dev/null
        rm -f "$INGRESS_PID_FILE" 2>/dev/null
    fi
    
    # Verify service exists
    export KUBECONFIG="$KUBECONFIG_HOST_PATH"
    if ! kubectl get svc "$SERVICE_NAME" -n "$NAMESPACE" > /dev/null 2>&1; then
        echo "Error: Service '$SERVICE_NAME' not found in namespace '$NAMESPACE'."
        echo "Available services in namespace '$NAMESPACE':"
        kubectl get svc -n "$NAMESPACE" 2>&1 | head -10
        return 1
    fi
    
    # Get service ports
    SERVICE_PORTS=$(kubectl get svc "$SERVICE_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.ports[*].port}' 2>/dev/null)
    HTTP_PORT=$(echo "$SERVICE_PORTS" | awk '{print $1}')
    HTTPS_PORT=$(echo "$SERVICE_PORTS" | awk '{print $2}')
    
    # Start port-forward
    if [ -n "$HTTPS_PORT" ]; then
        REMOTE_HTTP_PORT="${HTTP_PORT:-80}"
        REMOTE_HTTPS_PORT="${HTTPS_PORT:-443}"
        echo "Starting port-forward: $INGRESS_HTTP_LOCAL_PORT:$REMOTE_HTTP_PORT, $INGRESS_HTTPS_LOCAL_PORT:$REMOTE_HTTPS_PORT"
        kubectl port-forward -n "$NAMESPACE" svc/$SERVICE_NAME ${INGRESS_HTTP_LOCAL_PORT}:${REMOTE_HTTP_PORT} ${INGRESS_HTTPS_LOCAL_PORT}:${REMOTE_HTTPS_PORT} > /dev/null 2>&1 &
    else
        REMOTE_HTTP_PORT="${HTTP_PORT:-80}"
        echo "Starting port-forward: $INGRESS_HTTP_LOCAL_PORT:$REMOTE_HTTP_PORT"
        kubectl port-forward -n "$NAMESPACE" svc/$SERVICE_NAME ${INGRESS_HTTP_LOCAL_PORT}:${REMOTE_HTTP_PORT} > /dev/null 2>&1 &
    fi
    
    PF_PID=$!
    sleep 2
    
    if ps -p "$PF_PID" > /dev/null 2>&1; then
        echo "$PF_PID" > "$INGRESS_PID_FILE"
        echo "Ingress port-forward started. PID: $PF_PID"
        echo ""
        echo "Service: $SERVICE_NAME (namespace: $NAMESPACE)"
        echo "Ports: localhost:$INGRESS_HTTP_LOCAL_PORT -> $SERVICE_NAME:$REMOTE_HTTP_PORT"
        if [ -n "$REMOTE_HTTPS_PORT" ]; then
            echo "        localhost:$INGRESS_HTTPS_LOCAL_PORT -> $SERVICE_NAME:$REMOTE_HTTPS_PORT"
        fi
        echo ""
        # Get ingress host if available (like original script)
        INGRESS_HOST=$(kubectl get ingress -n "$NAMESPACE" -o jsonpath='{.items[?(@.spec.rules[0].http.paths[0].backend.service.name=="'$SERVICE_NAME'")].spec.rules[0].host}' 2>/dev/null | awk '{print $1}')
        if [ -z "$INGRESS_HOST" ]; then
            # Try to find any ingress with this service
            INGRESS_HOST=$(kubectl get ingress -A -o jsonpath='{range .items[*]}{.spec.rules[0].host}{"\n"}{end}' 2>/dev/null | grep -v "^$" | head -1)
        fi
        
        if [ -n "$INGRESS_HOST" ]; then
            echo "Access URL (add to /etc/hosts: 127.0.0.1 $INGRESS_HOST):"
            echo "  http://$INGRESS_HOST:$INGRESS_HTTP_LOCAL_PORT"
            if [ -n "$REMOTE_HTTPS_PORT" ]; then
                echo "  https://$INGRESS_HOST:$INGRESS_HTTPS_LOCAL_PORT"
            fi
        else
            echo "Access URL:"
            echo "  http://localhost:$INGRESS_HTTP_LOCAL_PORT"
            if [ -n "$REMOTE_HTTPS_PORT" ]; then
                echo "  https://localhost:$INGRESS_HTTPS_LOCAL_PORT"
            fi
        fi
        return 0
    else
        echo "Error: Failed to start port-forward."
        return 1
    fi
}

# Function: Stop ingress port-forward
stop_ingress_portforward() {
    if [ -f "$INGRESS_PID_FILE" ]; then
        PID=$(cat "$INGRESS_PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID"
            echo "Ingress port-forward stopped. PID: $PID"
        else
            echo "Ingress port-forward is not running."
        fi
        rm -f "$INGRESS_PID_FILE"
    else
        PID=$(ps aux | grep -E "[k]ubectl.*port-forward.*${INGRESS_HTTP_LOCAL_PORT}" | awk '{print $2}' | head -1)
        if [ -n "$PID" ]; then
            kill "$PID"
            echo "Ingress port-forward stopped. PID: $PID"
        else
            echo "No ingress port-forward is running."
        fi
    fi
}

# Function: Show ingress status
show_ingress_status() {
    if [ -f "$INGRESS_PID_FILE" ]; then
        PID=$(cat "$INGRESS_PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Ingress port-forward running. PID: $PID"
            echo "Ports: localhost:$INGRESS_HTTP_LOCAL_PORT (HTTP), localhost:$INGRESS_HTTPS_LOCAL_PORT (HTTPS)"
        else
            echo "Ingress port-forward is not running."
        fi
    else
        echo "Ingress port-forward is not running."
    fi
}

# Function: List available ingresses
list_ingresses() {
    local LIST_NAMESPACE="${1:-}"
    
    if [ ! -f "$KUBECONFIG_HOST_PATH" ]; then
        echo "Error: kubeconfig file not found: $KUBECONFIG_HOST_PATH"
        echo "Please run '$0 start' first."
        return 1
    fi
    
    export KUBECONFIG="$KUBECONFIG_HOST_PATH"
    
    if [ -z "$LIST_NAMESPACE" ]; then
        echo "Available ingresses (all namespaces):"
        kubectl get ingress -A --no-headers 2>/dev/null | while read -r namespace name class hosts address ports age; do
            service_name=$(kubectl get ingress "$name" -n "$namespace" -o jsonpath='{.spec.rules[0].http.paths[0].backend.service.name}' 2>/dev/null)
            if [ -n "$service_name" ]; then
                echo "  $0 ingress start $service_name $namespace"
            else
                echo "  $0 ingress start $name $namespace"
            fi
        done
    else
        echo "Available ingresses in namespace '$LIST_NAMESPACE':"
        kubectl get ingress -n "$LIST_NAMESPACE" --no-headers 2>/dev/null | while read -r name class hosts address ports age; do
            service_name=$(kubectl get ingress "$name" -n "$LIST_NAMESPACE" -o jsonpath='{.spec.rules[0].http.paths[0].backend.service.name}' 2>/dev/null)
            if [ -n "$service_name" ]; then
                echo "  $0 ingress start $service_name $LIST_NAMESPACE"
            else
                echo "  $0 ingress start $name $LIST_NAMESPACE"
            fi
        done
    fi
}

# Main logic
ACTION="${1:-start}"
SUB_ACTION="${2:-}"

if [ "$ACTION" = "ingress" ]; then
    # Ingress commands
    case "$SUB_ACTION" in
        start)
            start_ingress_portforward "${3:-}" "${4:-}"
            ;;
        stop)
            stop_ingress_portforward
            ;;
        restart)
            stop_ingress_portforward
            sleep 1
            start_ingress_portforward "${3:-}" "${4:-}"
            ;;
        status)
            show_ingress_status
            ;;
        list)
            list_ingresses "${3:-}"
            ;;
        *)
            echo "Usage: $0 ingress {start|stop|restart|status|list} [service-name] [namespace]"
            echo ""
            echo "  start    - Start kubectl port-forward for ingress service"
            echo "  stop     - Stop ingress port-forward"
            echo "  restart  - Restart ingress port-forward"
            echo "  status   - Show ingress port-forward status"
            echo "  list     - List available ingresses"
            echo ""
            echo "Examples:"
            echo "  $0 ingress start                                    # Use default service (ingress-nginx-controller)"
            echo "  $0 ingress start my-service my-namespace            # Forward specific service"
            echo "  $0 ingress list                                     # List all ingresses"
            echo "  $0 ingress list my-namespace                        # List ingresses in namespace"
            echo "  $0 ingress stop                                     # Stop port-forward"
            ;;
    esac
elif [ "$ACTION" = "start" ]; then
    if copy_kubeconfig; then
        if start_tunnel; then
            sleep 2
            test_connection
            # Automatically start ingress port-forward if not running
            # Only start if kubectl connection is working
            echo ""
            echo "Checking ingress port-forward status..."
            INGRESS_PID=""
            if [ -f "$INGRESS_PID_FILE" ]; then
                INGRESS_PID=$(cat "$INGRESS_PID_FILE" 2>/dev/null)
            fi
            
            if [ -z "$INGRESS_PID" ] || ! ps -p "$INGRESS_PID" > /dev/null 2>&1; then
                # Verify kubectl connection is working before starting ingress port-forward
                echo "Verifying kubectl connection before starting ingress port-forward..."
                if timeout 5 kubectl --kubeconfig="$KUBECONFIG_HOST_PATH" get nodes > /dev/null 2>&1; then
                    echo "Starting ingress port-forward automatically..."
                    start_ingress_portforward
                else
                    echo "⚠ Warning: kubectl connection is not stable. Skipping automatic ingress port-forward."
                    echo "Please run '$0 ingress start' manually after kubectl connection is stable."
                fi
            else
                echo "Ingress port-forward is already running. PID: $INGRESS_PID"
            fi
        fi
    fi
elif [ "$ACTION" = "stop" ]; then
    stop_tunnel
    stop_ingress_portforward
elif [ "$ACTION" = "restart" ]; then
    stop_tunnel
    sleep 1
    start_tunnel
elif [ "$ACTION" = "status" ]; then
    MODE=$(detect_access_mode)
    echo "=== Access Mode ==="
    echo "Mode: $MODE"
    if [ "$MODE" = "direct" ]; then
        echo "  - Direct access via vagrant ssh"
        echo "  - Vagrant directory: $VAGRANT_DIR"
    else
        echo "  - Indirect access via $MY_UBUNTU_HOST"
    fi
    echo ""
    echo "=== SSH Tunnel Status ==="
    if [ -f "$TUNNEL_PID_FILE" ]; then
        PID=$(cat "$TUNNEL_PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "SSH tunnel running. PID: $PID"
        else
            echo "SSH tunnel is not running."
        fi
    else
        echo "SSH tunnel is not running."
    fi
    echo ""
    if [ "$MODE" = "indirect" ]; then
        echo "Tunnel status on my-ubuntu:"
        if check_host_connectivity > /dev/null 2>&1; then
            ssh -o ConnectTimeout=$SSH_TIMEOUT "$MY_UBUNTU_HOST" "
                if [ -f ~/workspaces/tz-drillquiz/provisioning/access-k8s-from-host.sh ]; then
                    cd ~/workspaces/tz-drillquiz/provisioning && ./access-k8s-from-host.sh status 2>&1
                else
                    echo 'Error: access-k8s-from-host.sh not found'
                fi
            " 2>&1 || echo "Failed to get status from $MY_UBUNTU_HOST"
        else
            echo "Cannot connect to $MY_UBUNTU_HOST to check tunnel status"
        fi
        echo ""
    fi
    echo "=== Ingress Port-Forward Status ==="
    show_ingress_status
elif [ "$ACTION" = "test" ]; then
    test_connection
else
    echo "Usage: $0 {start|stop|restart|status|test|ingress}"
    echo ""
    echo "Kubernetes API Access:"
    echo "  start   - Copy kubeconfig and start SSH tunnel (default)"
    echo "  stop    - Stop SSH tunnel and ingress port-forward"
    echo "  restart - Restart SSH tunnel"
    echo "  status  - Check SSH tunnel and ingress status"
    echo "  test    - Test kubectl connection"
    echo ""
    echo "Ingress Access:"
    echo "  ingress start [service] [namespace]    - Start ingress port-forward"
    echo "  ingress stop                           - Stop ingress port-forward"
    echo "  ingress restart [service] [namespace]  - Restart ingress port-forward"
    echo "  ingress status                         - Show ingress port-forward status"
    echo "  ingress list [namespace]               - List available ingresses"
    echo ""
    echo "Access Modes:"
    echo "  - Direct mode: MacBook -> kube-master (via vagrant ssh)"
    echo "    * Requires: Vagrantfile at $VAGRANT_DIR"
    echo "    * Requires: vagrant command installed"
    echo "    * Requires: kube-master VM accessible via vagrant"
    echo "    * Set: ACCESS_MODE=direct"
    echo ""
    echo "  - Indirect mode: MacBook -> my-ubuntu -> kube-master (via SSH tunnel)"
    echo "    * Requires: SSH access to my-ubuntu ('ssh my-ubuntu' should work)"
    echo "    * Requires: access-k8s-from-host.sh must exist on my-ubuntu"
    echo "    * Set: ACCESS_MODE=indirect"
    echo ""
    echo "  - Auto mode (default): Automatically detects which mode to use"
    echo "    * Set: ACCESS_MODE=auto (or omit)"
    echo ""
    echo "Requirements:"
    echo "  - kubectl must be installed on MacBook (brew install kubectl)"
    echo ""
    echo "Examples:"
    echo "  $0 start                              # Start SSH tunnel for kubectl (auto-detect mode)"
    echo "  ACCESS_MODE=direct $0 start           # Force direct mode"
    echo "  ACCESS_MODE=indirect $0 start          # Force indirect mode"
    echo "  $0 ingress start                      # Start ingress port-forward"
    echo "  $0 ingress list                       # List available ingresses"
    echo "  $0 status                             # Check all tunnels status"
    echo ""
    echo "kubeconfig file location: $KUBECONFIG_HOST_PATH"
    echo "Usage:"
    echo "  export KUBECONFIG=\"$KUBECONFIG_HOST_PATH\""
    echo "  kubectl get nodes"
    exit 1
fi

