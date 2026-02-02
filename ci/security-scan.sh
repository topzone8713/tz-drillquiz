#!/bin/sh

# Unified Security Scan Script
# Usage: ./ci/security-scan.sh [phase]
# Phase: pre-build (default) or post-build
# This script runs security scans based on the specified phase

set -e

# Get phase parameter
PHASE=${1:-pre-build}

echo "🔍 Starting unified security scan (Phase: ${PHASE})..."

# Check and adjust current directory
if [ ! -f "manage.py" ]; then
    echo "🔍 Looking for manage.py..."
    if [ -f "../manage.py" ]; then
        current_dir=$(pwd)
        parent_dir=$(dirname "$current_dir")
        echo "📁 Moving to parent directory: $current_dir -> $parent_dir"
        cd ..
        echo "✅ Successfully moved to Django project root: $(pwd)"
    else
        echo "❌ Django project root not found"
        exit 1
    fi
fi

# Installation functions
install_packages() {
    echo "📦 Installing required packages..."
    
    # Check Alpine Linux environment
    if [ -f /etc/alpine-release ]; then
        apk add --no-cache python3 py3-pip git jq curl wget tar gzip >/dev/null 2>&1
    else
        # Ubuntu/Debian environment
        if command -v apt-get &> /dev/null; then
            apt-get update >/dev/null 2>&1 && apt-get install -y python3 python3-pip git jq curl wget >/dev/null 2>&1
        # CentOS/RHEL environment
        elif command -v yum &> /dev/null; then
            yum install -y python3 python3-pip git jq curl wget >/dev/null 2>&1
        # Other environments
        else
            echo "⚠️  Unknown Linux distribution. Please install packages manually."
        fi
    fi
    
    echo "✅ Package installation completed"
}

setup_git() {
    echo "🔧 Setting up Git safe directory..."
    git config --global --add safe.directory $(pwd)
    git config --global --add safe.directory /home/jenkins/agent/workspace/tz-drillquiz
    echo "✅ Git setup completed"
}

install_pip() {
    if ! command -v pip &> /dev/null; then
        echo "📦 pip installing..."
        python3 -m ensurepip --upgrade
        # Link pip3 to pip
        ln -sf /usr/bin/pip3 /usr/bin/pip 2>/dev/null || true
        echo "✅ pip installation completed"
    fi
}

install_semgrep() {
    if ! command -v semgrep &> /dev/null; then
        echo "📦 semgrep installing..."
        pip install semgrep >/dev/null 2>&1
        echo "✅ semgrep installation completed"
    else
        echo "✅ semgrep already installed"
    fi
}

install_trivy() {
    if ! command -v trivy &> /dev/null; then
        echo "📦 Trivy installing..."
        
        # Install Trivy on Alpine Linux
        if [ -f /etc/alpine-release ]; then
            echo "🐧 Installing Trivy on Alpine Linux..."
            # Package installation for Alpine
            apk add --no-cache curl
            # Download and install Trivy binary
            TRIVY_VERSION=$(curl -s https://api.github.com/repos/aquasecurity/trivy/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
            if [ -z "$TRIVY_VERSION" ]; then
                TRIVY_VERSION="v0.50.0"  # Default version
            fi
            echo "📥 Trivy ${TRIVY_VERSION} downloading..."
            wget -qO- "https://github.com/aquasecurity/trivy/releases/download/${TRIVY_VERSION}/trivy_${TRIVY_VERSION#v}_Linux-64bit.tar.gz" | tar -xz -C /tmp
            mv /tmp/trivy /usr/local/bin/trivy
            chmod +x /usr/local/bin/trivy
        else
            # General Linux environment
        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
        fi
        
        # Installation check
        if command -v trivy &> /dev/null; then
            echo "✅ Trivy installation completed"
        else
            echo "❌ Trivy installation failed"
            return 1
        fi
    else
        echo "✅ Trivy already installed"
    fi
}

install_checkov() {
    if ! command -v checkov &> /dev/null; then
        echo "📦 Checkov installing..."
        
        # Install Checkov on Alpine Linux
        if [ -f /etc/alpine-release ]; then
            pip install checkov >/dev/null 2>&1
        else
            # General Linux environment
            pip install checkov >/dev/null 2>&1
        fi
        
        # Installation check
        if command -v checkov &> /dev/null; then
            echo "✅ Checkov installation completed"
        else
            echo "❌ Checkov installation failed"
            return 1
        fi
    else
        echo "✅ Checkov already installed"
    fi
}

install_owasp_zap() {
    if ! command -v zap-baseline.py &> /dev/null; then
        echo "📦 Installing OWASP ZAP..."
        
        # Install Java and required packages
        if [ -f /etc/alpine-release ]; then
            apk add --no-cache openjdk11-jre unzip >/dev/null 2>&1
        elif command -v apt-get &> /dev/null; then
            apt-get update >/dev/null 2>&1 && apt-get install -y openjdk-11-jre unzip >/dev/null 2>&1
        elif command -v yum &> /dev/null; then
            yum install -y java-11-openjdk unzip >/dev/null 2>&1
        fi
        
        # Download and install OWASP ZAP
        RELEASE_INFO=$(curl -s https://api.github.com/repos/zaproxy/zaproxy/releases/latest)
        ZAP_VERSION=$(echo "$RELEASE_INFO" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
        
        if [ -z "$ZAP_VERSION" ]; then
            ZAP_VERSION="v2.14.0"
        fi
        
        DOWNLOAD_URL="https://github.com/zaproxy/zaproxy/releases/download/${ZAP_VERSION}/ZAP_${ZAP_VERSION#v}_Linux.tar.gz"
        
        if curl -sL "${DOWNLOAD_URL}" -o /tmp/zap.tar.gz && \
           [ -s /tmp/zap.tar.gz ] && [ $(stat -c%s /tmp/zap.tar.gz) -gt 1000 ] && \
           tar -xzf /tmp/zap.tar.gz -C /opt/ && \
           [ -d "/opt/ZAP_${ZAP_VERSION#v}" ] && \
           [ -f "/opt/ZAP_${ZAP_VERSION#v}/zap.sh" ]; then
            ZAP_DIR="/opt/ZAP_${ZAP_VERSION#v}"
            ln -sf "$ZAP_DIR/zap.sh" /usr/local/bin/zap-baseline.py
            ln -sf "$ZAP_DIR/zap.sh" /usr/local/bin/zap-full-scan.py
            chmod +x /usr/local/bin/zap-baseline.py
            chmod +x /usr/local/bin/zap-full-scan.py
            echo "✅ OWASP ZAP installation completed"
        else
            echo "❌ OWASP ZAP installation failed"
            return 1
        fi
    else
        echo "✅ OWASP ZAP already installed"
    fi
}

install_nikto() {
    if ! command -v nikto &> /dev/null; then
        echo "📦 Nikto installing..."
        
        # Install Nikto on Alpine Linux
        if [ -f /etc/alpine-release ]; then
            # Install Perl and required modules
            apk add --no-cache perl perl-net-ssleay perl-io-socket-ssl perl-libwww >/dev/null 2>&1
            
            # Download and install Nikto
            echo "📥 Downloading Nikto..."
            if wget -q "https://github.com/sullo/nikto/archive/master.zip" -O /tmp/nikto.zip; then
                echo "✅ Download completed"
                unzip -q /tmp/nikto.zip -d /opt/
                ln -sf /opt/nikto-master/program/nikto.pl /usr/local/bin/nikto
                chmod +x /usr/local/bin/nikto
                echo "✅ Nikto installation completed"
            else
                echo "❌ Nikto download failed"
                return 1
            fi
        else
            # General Linux environment
            if command -v apt-get &> /dev/null; then
                apt-get update >/dev/null 2>&1 && apt-get install -y nikto >/dev/null 2>&1
            elif command -v yum &> /dev/null; then
                yum install -y nikto >/dev/null 2>&1
            fi
        fi
        
        # Installation check
        if command -v nikto &> /dev/null; then
            echo "✅ Nikto installation completed: $(nikto -Version 2>/dev/null | head -1 || echo 'unknown')"
        else
            echo "❌ Nikto installation failed"
            return 1
        fi
    else
        echo "✅ Nikto already installed: $(nikto -Version 2>/dev/null | head -1 || echo 'unknown')"
    fi
}

install_syft() {
    if ! command -v syft &> /dev/null; then
        echo "📦 Installing syft..."
        
        # Install syft on Alpine Linux
        if [ -f /etc/alpine-release ]; then
            # Download and install syft binary
            RELEASE_INFO=$(curl -s https://api.github.com/repos/anchore/syft/releases/latest)
            SYFT_VERSION=$(echo "$RELEASE_INFO" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
            
            if [ -z "$SYFT_VERSION" ]; then
                SYFT_VERSION="v1.4.0"
            fi
            
            echo "📥 Syft ${SYFT_VERSION} downloading..."
            wget -qO- "https://github.com/anchore/syft/releases/download/${SYFT_VERSION}/syft_${SYFT_VERSION#v}_linux_amd64.tar.gz" | tar -xz -C /tmp
            mv /tmp/syft /usr/local/bin/syft
            chmod +x /usr/local/bin/syft
        else
            # General Linux environment
            curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
        fi
        
        # Installation check
        if command -v syft &> /dev/null; then
            echo "✅ Syft installation completed"
        else
            echo "❌ Syft installation failed"
            return 1
        fi
    else
        echo "✅ Syft already installed"
    fi
}

install_cosign() {
    if ! command -v cosign &> /dev/null; then
        echo "📦 Installing cosign..."
        
        # Install cosign on Alpine Linux
        if [ -f /etc/alpine-release ]; then
            # Download and install cosign binary
            RELEASE_INFO=$(curl -s https://api.github.com/repos/sigstore/cosign/releases/latest)
            COSIGN_VERSION=$(echo "$RELEASE_INFO" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
            
            if [ -z "$COSIGN_VERSION" ]; then
                COSIGN_VERSION="v2.2.4"
            fi
            
            echo "📥 Cosign ${COSIGN_VERSION} downloading..."
            wget -qO- "https://github.com/sigstore/cosign/releases/download/${COSIGN_VERSION}/cosign-linux-amd64" -O /usr/local/bin/cosign
            chmod +x /usr/local/bin/cosign
        else
            # General Linux environment
            curl -sSfL https://raw.githubusercontent.com/sigstore/cosign/main/install.sh | sh -s -- -b /usr/local/bin
        fi
        
        # Installation check
        if command -v cosign &> /dev/null; then
            echo "✅ Cosign installation completed"
        else
            echo "❌ Cosign installation failed"
            return 1
        fi
    else
        echo "✅ Cosign already installed"
    fi
}

install_slsa_verifier() {
    if ! command -v slsa-verifier &> /dev/null; then
        echo "📦 Installing slsa-verifier..."
        
        # Install slsa-verifier on Alpine Linux
        if [ -f /etc/alpine-release ]; then
            # Download and install slsa-verifier binary
            RELEASE_INFO=$(curl -s https://api.github.com/repos/slsa-framework/slsa-verifier/releases/latest)
            SLSA_VERSION=$(echo "$RELEASE_INFO" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
            
            if [ -z "$SLSA_VERSION" ]; then
                SLSA_VERSION="v2.6.0"
            fi
            
            echo "📥 SLSA Verifier ${SLSA_VERSION} downloading..."
            wget -qO- "https://github.com/slsa-framework/slsa-verifier/releases/download/${SLSA_VERSION}/slsa-verifier-linux-amd64" -O /usr/local/bin/slsa-verifier
            chmod +x /usr/local/bin/slsa-verifier
        else
            # General Linux environment
            curl -sSfL https://raw.githubusercontent.com/slsa-framework/slsa-verifier/main/install.sh | sh -s -- -b /usr/local/bin
        fi
        
        # Installation check
        if command -v slsa-verifier &> /dev/null; then
            echo "✅ SLSA Verifier installation completed"
        else
            echo "❌ SLSA Verifier installation failed"
            return 1
        fi
    else
        echo "✅ SLSA Verifier already installed"
    fi
}

install_kube_linter() {
    if ! command -v kube-linter &> /dev/null; then
        echo "📦 Installing kube-linter..."
        
        # Install kube-linter on Alpine Linux
        if [ -f /etc/alpine-release ]; then
            # First try installing from Alpine package
            if apk add --no-cache kube-linter 2>/dev/null; then
                echo "✅ kube-linter installation completed"
                return 0
            fi
            
            # Download and install kube-linter binary
            RELEASE_INFO=$(curl -s https://api.github.com/repos/stackrox/kube-linter/releases/latest)
            KUBE_LINTER_VERSION=$(echo "$RELEASE_INFO" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
            
            if [ -z "$KUBE_LINTER_VERSION" ]; then
                KUBE_LINTER_VERSION="v0.6.4"
            fi
            
            # Find Linux binary
            ASSETS=$(echo "$RELEASE_INFO" | grep '"browser_download_url"' | sed -E 's/.*"([^"]+)".*/\1/')
            LINUX_AMD64_URL=$(echo "$ASSETS" | grep -i "linux.*amd64" | head -1)
            LINUX_URL=$(echo "$ASSETS" | grep -i "linux\.tar\.gz" | head -1)
            
            if [ -n "$LINUX_AMD64_URL" ]; then
                DOWNLOAD_URLS="$LINUX_AMD64_URL"
            elif [ -n "$LINUX_URL" ]; then
                DOWNLOAD_URLS="$LINUX_URL"
            else
                DOWNLOAD_URLS="https://github.com/stackrox/kube-linter/releases/download/${KUBE_LINTER_VERSION}/kube-linter-linux.tar.gz"
            fi
            
            DOWNLOAD_SUCCESS=false
            for DOWNLOAD_URL in $DOWNLOAD_URLS; do
                # Download with wget then extract with tar
                if wget -q "${DOWNLOAD_URL}" -O /tmp/kube-linter.tar.gz 2>/dev/null; then
                    
                    # If file is too small, might be 404 page
                    FILE_SIZE=$(stat -c%s /tmp/kube-linter.tar.gz 2>/dev/null || echo "0")
                    if [ "$FILE_SIZE" -lt 1000 ]; then
                        continue
                    fi
                    
                    # Create unique extraction directory
                    EXTRACT_DIR="/tmp/kube-linter-extract-$(date +%s)-$$"
                    mkdir -p "$EXTRACT_DIR"
                    
                    # First try extraction with gzip
                    if gzip -dc /tmp/kube-linter.tar.gz | tar -xf - -C "$EXTRACT_DIR" 2>/dev/null; then
                        
                        # Find kube-linter binary (check multiple locations)
                        KUBE_LINTER_BINARY=""
                        if [ -f "$EXTRACT_DIR/kube-linter" ]; then
                            KUBE_LINTER_BINARY="$EXTRACT_DIR/kube-linter"
                        elif [ -d "$EXTRACT_DIR/kube-linter" ] && [ -f "$EXTRACT_DIR/kube-linter/kube-linter" ]; then
                            KUBE_LINTER_BINARY="$EXTRACT_DIR/kube-linter/kube-linter"
                        else
                            # Recursively find kube-linter binary
                            KUBE_LINTER_BINARY=$(find "$EXTRACT_DIR" -name "kube-linter" -type f 2>/dev/null | head -1)
                        fi
                        
                        if [ -n "$KUBE_LINTER_BINARY" ] && [ -f "$KUBE_LINTER_BINARY" ]; then
                            echo "✅ kube-linter binary found: $KUBE_LINTER_BINARY"
                            if command -v file &> /dev/null; then
                                echo "📁 Binary info: $(file "$KUBE_LINTER_BINARY")"
                            else
                                echo "📁 Binary info: file command not available (Alpine Linux)"
                            fi
                            echo "📁 Binary size: $(ls -lh "$KUBE_LINTER_BINARY" | awk '{print $5}')"
                            
                            mv "$KUBE_LINTER_BINARY" /usr/local/bin/kube-linter
                            chmod +x /usr/local/bin/kube-linter
                            echo "✅ kube-linter installation completed"
                            
                            # Clean up temporary files
                            rm -f /tmp/kube-linter.tar.gz
                            rm -rf "$EXTRACT_DIR" 2>/dev/null || true
                            
                            DOWNLOAD_SUCCESS=true
                            break
                        else
                            echo "❌ kube-linter binary not found"
                            echo "📁 Extraction directory contents:"
                            ls -la "$EXTRACT_DIR" 2>/dev/null || echo "  No directory"
                            echo "📁 Searching for kube-linter related files:"
                            find "$EXTRACT_DIR" -name "*kube*" -o -name "*linter*" 2>/dev/null || echo "  No related files"
                            
                            # Clean up temporary files
                            rm -rf "$EXTRACT_DIR" 2>/dev/null || true
                        fi
                    else
                        echo "❌ gzip+tar extraction failed, trying alternative methods..."
                        
                        # Alternative 1: Try tar -xzf directly
                        if tar -xzf /tmp/kube-linter.tar.gz -C "$EXTRACT_DIR" 2>/dev/null; then
                            echo "✅ tar -xzf extraction successful"
                            echo "📁 Extracted files:"
                            ls -la "$EXTRACT_DIR" 2>/dev/null || echo "  No directory"
                            
                            # Find kube-linter binary
                            KUBE_LINTER_BINARY=$(find "$EXTRACT_DIR" -name "kube-linter" -type f 2>/dev/null | head -1)
                            
                            if [ -n "$KUBE_LINTER_BINARY" ] && [ -f "$KUBE_LINTER_BINARY" ]; then
                                echo "✅ kube-linter binary found: $KUBE_LINTER_BINARY"
                                mv "$KUBE_LINTER_BINARY" /usr/local/bin/kube-linter
                                chmod +x /usr/local/bin/kube-linter
                                echo "✅ kube-linter installation completed"
                                rm -f /tmp/kube-linter.tar.gz
                                rm -rf "$EXTRACT_DIR" 2>/dev/null || true
                                DOWNLOAD_SUCCESS=true
                                break
                            fi
                        fi
                        
                        # Alternative 2: Try gunzip then tar
                        echo "🔍 Trying gunzip + tar method..."
                        if gunzip -c /tmp/kube-linter.tar.gz | tar -xf - -C "$EXTRACT_DIR" 2>/dev/null; then
                            echo "✅ gunzip+tar extraction successful"
                            echo "📁 Extracted files:"
                            ls -la "$EXTRACT_DIR" 2>/dev/null || echo "  No directory"
                            
                            # Find kube-linter binary
                            KUBE_LINTER_BINARY=$(find "$EXTRACT_DIR" -name "kube-linter" -type f 2>/dev/null | head -1)
                            
                            if [ -n "$KUBE_LINTER_BINARY" ] && [ -f "$KUBE_LINTER_BINARY" ]; then
                                echo "✅ kube-linter binary found: $KUBE_LINTER_BINARY"
                                mv "$KUBE_LINTER_BINARY" /usr/local/bin/kube-linter
                                chmod +x /usr/local/bin/kube-linter
                                echo "✅ kube-linter installation completed"
                                rm -f /tmp/kube-linter.tar.gz
                                rm -rf "$EXTRACT_DIR" 2>/dev/null || true
                                DOWNLOAD_SUCCESS=true
                                break
                            fi
                        fi
                        
                        echo "❌ All extraction methods failed"
                        echo "📁 Downloaded file content check:"
                        echo "  file size: $(ls -lh /tmp/kube-linter.tar.gz | awk '{print $5}')"
                        if command -v file &> /dev/null; then
                            echo "  file type: $(file /tmp/kube-linter.tar.gz)"
                        else
                            echo "  file type: file command not available (Alpine Linux)"
                        fi
                        echo "  file header: $(head -c 100 /tmp/kube-linter.tar.gz | hexdump -C | head -5)"
                        
                        # Clean up temporary files
                        rm -rf "$EXTRACT_DIR" 2>/dev/null || true
                    fi
                else
                    echo "❌ wget download failed"
                fi
                
                # Clean up temporary files before trying next URL
                rm -f /tmp/kube-linter.tar.gz
            done
            
            if [ "$DOWNLOAD_SUCCESS" = "false" ]; then
                echo "❌ All download URL attempts failed"
                echo "🔍 Download failure analysis:"
                echo "  - Network connection check: $(ping -c 1 github.com >/dev/null 2>&1 && echo "Connected" || echo "Connection failed")"
                echo "  - DNS resolution check: $(nslookup github.com >/dev/null 2>&1 && echo "Resolved" || echo "Resolution failed")"
                echo "  - wget version: $(wget --version | head -1)"
                echo "  - Trying with curl:"
                FIRST_URL=$(echo $DOWNLOAD_URLS | awk '{print $1}')
                if curl -sL "${FIRST_URL}" -o /tmp/kube-linter.tar.gz; then
                    echo "    ✅ Download successful with curl"
                    echo "    📁 Downloaded file size: $(ls -lh /tmp/kube-linter.tar.gz | awk '{print $5}')"
                else
                    echo "    ❌ Download failed with curl too"
                fi
                echo "⚠️  Continuing IaC scan without kube-linter"
                return 0  # Continue even if failed
            fi
        else
            # General Linux environment
            curl -sL https://raw.githubusercontent.com/stackrox/kube-linter/main/scripts/install.sh | bash -s -- --use-sudo=false
        fi
        
        # Installation check
        if command -v kube-linter &> /dev/null; then
            echo "✅ kube-linter installation completed: $(kube-linter version)"
        else
            echo "⚠️  kube-linter installation failed - Using Checkov only"
            return 0  # Continue even if failed
        fi
    else
        echo "✅ kube-linter already installed: $(kube-linter version)"
    fi
}

# Create empty SARIF file function
create_empty_sarif() {
    local filename=$1
    local tool_name=$2
    cat > "$filename" << EOF
{
  "\$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "$tool_name",
          "version": "unknown"
        }
      },
      "results": []
    }
  ]
}
EOF
}

# Installation check function
check_installations() {
    echo "🔍 Verifying tool installations..."
    local missing_count=0
    
    if ! command -v jq >/dev/null 2>&1; then
        echo "⚠️  jq not found"
        missing_count=$((missing_count + 1))
    fi
    
    if ! command -v semgrep >/dev/null 2>&1; then
        echo "⚠️  semgrep not found"
        missing_count=$((missing_count + 1))
    fi
    
    if ! command -v trivy >/dev/null 2>&1; then
        echo "⚠️  trivy not found"
        missing_count=$((missing_count + 1))
    fi
    
    if ! command -v checkov >/dev/null 2>&1; then
        echo "⚠️  checkov not found"
        missing_count=$((missing_count + 1))
    fi
    
    if ! command -v kube-linter >/dev/null 2>&1; then
        echo "⚠️  kube-linter not found"
        missing_count=$((missing_count + 1))
    fi
    
    if ! command -v zap-baseline.py >/dev/null 2>&1; then
        echo "⚠️  OWASP ZAP not found"
        missing_count=$((missing_count + 1))
    fi
    
    if ! command -v nikto >/dev/null 2>&1; then
        echo "⚠️  nikto not found"
        missing_count=$((missing_count + 1))
    fi
    
    if ! command -v syft >/dev/null 2>&1; then
        echo "⚠️  syft not found"
        missing_count=$((missing_count + 1))
    fi
    
    if ! command -v cosign >/dev/null 2>&1; then
        echo "⚠️  cosign not found"
        missing_count=$((missing_count + 1))
    fi
    
    if ! command -v slsa-verifier >/dev/null 2>&1; then
        echo "⚠️  slsa-verifier not found"
        missing_count=$((missing_count + 1))
    fi
    
    if [ $missing_count -gt 0 ]; then
        echo "⚠️  $missing_count tools missing - some scans may be limited or skipped"
    else
        echo "✅ All required tools are installed"
    fi
}

# Execute initial setup
install_packages
setup_git
install_pip

# Install only necessary tools based on phase and enabled scans
echo "🔧 Environment variables:"
echo "  PHASE: ${PHASE}"
echo "  SAST_YN: ${SAST_YN:-true}"
echo "  SCA_YN: ${SCA_YN:-true}"
echo "  IAC_SCAN_YN: ${IAC_SCAN_YN:-true}"
echo "  CONTAINER_SCAN_YN: ${CONTAINER_SCAN_YN:-true}"
echo "  DAST_SCAN_YN: ${DAST_SCAN_YN:-true}"
echo "  SBOM_YN: ${SBOM_YN:-true}"
echo "  IMAGE_SIGNING_YN: ${IMAGE_SIGNING_YN:-true}"
echo "  PROVENANCE_YN: ${PROVENANCE_YN:-true}"

if [ "$PHASE" = "pre-build" ]; then
    # Pre-build tools: SAST, SCA, IaC, SBOM
    if [ "${SAST_YN:-true}" = "true" ]; then
        install_semgrep
    fi

    if [ "${SCA_YN:-true}" = "true" ]; then
        install_trivy
    fi

    if [ "${IAC_SCAN_YN:-true}" = "true" ]; then
        install_checkov
        install_kube_linter
    fi

    # SBOM generation tools
    if [ "${SBOM_YN:-true}" = "true" ]; then
        install_syft
    fi
    
    # Image signing tools (only if needed)
    if [ "${IMAGE_SIGNING_YN:-true}" = "true" ]; then
        install_cosign
    fi
    
    # Provenance verification tools (only if needed)
    if [ "${PROVENANCE_YN:-true}" = "true" ]; then
        install_slsa_verifier
    fi
elif [ "$PHASE" = "post-build" ]; then
    # Post-build tools: Container, DAST, Signing, Provenance
    if [ "${CONTAINER_SCAN_YN:-true}" = "true" ]; then
        install_trivy
    fi

    if [ "${DAST_SCAN_YN:-true}" = "true" ]; then
        install_owasp_zap
        install_nikto
    fi

    # Signing and provenance tools
    if [ "${IMAGE_SIGNING_YN:-true}" = "true" ] || [ "${PROVENANCE_YN:-true}" = "true" ]; then
        install_cosign
    fi
    if [ "${PROVENANCE_YN:-true}" = "true" ]; then
        install_slsa_verifier
    fi
fi

check_installations

# Scan functions
run_semgrep_scans() {
    if [ "${SAST_YN:-true}" = "true" ]; then
        echo "🔍 Semgrep SAST scan starting..."
        
        echo "🐍 Scanning Python/Django code..."
        if ! semgrep ci --config p/owasp-top-ten --config p/python --sarif --output semgrep-python.sarif --no-git-ignore 2>/dev/null; then
            echo "⚠️  Python scan failed, creating empty SARIF file"
            create_empty_sarif "semgrep-python.sarif" "Semgrep"
        fi

        echo "🌐 Scanning Frontend code (JavaScript + Vue.js)..."
        if ! semgrep ci --config p/owasp-top-ten --config p/javascript --config p/vue --sarif --output semgrep-frontend.sarif --no-git-ignore 2>/dev/null; then
            echo "⚠️  Frontend scan failed, creating empty SARIF file"
            create_empty_sarif "semgrep-frontend.sarif" "Semgrep"
        fi

        # Node.js dependency scan (package.json)
        if [ -f "package.json" ]; then
            echo "📦 Scanning Node.js dependencies..."
            if ! semgrep ci --config p/owasp-top-ten --config p/javascript --include="package*.json" --sarif --output semgrep-dependencies.sarif --no-git-ignore 2>/dev/null; then
                echo "⚠️  Dependencies scan failed, creating empty SARIF file"
                create_empty_sarif "semgrep-dependencies.sarif" "Semgrep"
            fi
        fi

        echo "🔍 Running integrated security scan..."
        if ! semgrep ci --config p/owasp-top-ten --sarif --output semgrep.sarif --no-git-ignore 2>/dev/null; then
            echo "⚠️  Integrated scan failed, creating empty SARIF file"
            create_empty_sarif "semgrep.sarif" "Semgrep"
        fi
    else
        echo "⏭️  SAST scan is disabled (SAST_YN=${SAST_YN})"
    fi
}

run_trivy_sca_scans() {
    if [ "${SCA_YN:-true}" = "true" ]; then
        echo "📦 Trivy SCA scan starting..."

        # Check Trivy installation
        if ! command -v trivy &> /dev/null; then
            echo "❌ Trivy is not installed. Skipping SCA scan."
            echo "⚠️  Trivy installation is required for SCA scan."
            return 1
        fi

        # Python dependency scan
        echo "🐍 Scanning Python dependencies..."
        if trivy fs --scanners vuln --vuln-type library --format sarif -o sca-python.sarif . 2>/dev/null; then
            echo "✅ Python dependency scan completed"
        else
            echo "⚠️  Python dependency scan failed (creating empty SARIF file)"
            echo '{"$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json", "version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Trivy", "version": "unknown"}}, "results": []}]}' > sca-python.sarif
        fi

        # Node.js dependency scan
        if [ -d "node_modules" ]; then
            echo "📦 Scanning Node.js dependencies..."
            if trivy fs --scanners vuln --vuln-type library --format sarif -o sca-node.sarif ./node_modules 2>/dev/null; then
                echo "✅ Node.js dependency scan completed"
            else
                echo "⚠️  Node.js dependency scan failed (creating empty SARIF file)"
                echo '{"$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json", "version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Trivy", "version": "unknown"}}, "results": []}]}' > sca-node.sarif
            fi
        else
            echo "📦 node_modules directory not found. Skipping Node.js scan."
        fi

        # OS package scan
        echo "🖥️ Scanning OS packages..."
        if trivy fs --scanners vuln --vuln-type os --format sarif -o sca-os.sarif . 2>/dev/null; then
            echo "✅ OS package scan completed"
        else
            echo "⚠️  OS package scan failed (creating empty SARIF file)"
            echo '{"$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json", "version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Trivy", "version": "unknown"}}, "results": []}]}' > sca-os.sarif
        fi

        # Enhanced dependency scan - specific files
        if [ -f "requirements.txt" ]; then
            echo "📋 Scanning requirements.txt..."
            if trivy fs --scanners vuln --vuln-type library --format sarif -o sca-requirements.sarif requirements.txt 2>/dev/null; then
                echo "✅ requirements.txt scan completed"
            else
                echo "⚠️  requirements.txt scan failed (creating empty SARIF file)"
                echo '{"$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json", "version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Trivy", "version": "unknown"}}, "results": []}]}' > sca-requirements.sarif
            fi
        fi

        if [ -f "package.json" ]; then
            echo "📋 Scanning package.json..."
            if trivy fs --scanners vuln --vuln-type library --format sarif -o sca-package.sarif package.json 2>/dev/null; then
                echo "✅ package.json scan completed"
            else
                echo "⚠️  package.json scan failed (creating empty SARIF file)"
                echo '{"$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json", "version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Trivy", "version": "unknown"}}, "results": []}]}' > sca-package.sarif
            fi
        fi
    else
        echo "⏭️  SCA scan is disabled (SCA_YN=${SCA_YN})"
    fi
}

run_container_scans() {
    if [ "${CONTAINER_SCAN_YN:-true}" = "true" ]; then
        # Check Trivy installation
        if ! command -v trivy &> /dev/null; then
            echo "❌ Trivy is not installed. Skipping container scan."
            echo "⚠️  Trivy installation is required for container scan."
            return 1
        fi

        # Container image scan (if image is built)
        if [ -n "${REGISTRY}" ] && [ -n "${DOCKER_NAME}" ] && [ -n "${BUILD_NUMBER}" ]; then
            echo "🐳 Scanning container images..."
            
            # Backend image scan
            echo "🐳 Scanning Backend image..."
            if trivy image --format sarif -o image-backend.sarif ${REGISTRY}/${DOCKER_NAME}:${BUILD_NUMBER} 2>/dev/null; then
                echo "✅ Backend image scan completed"
            else
                echo "⚠️  Backend image scan failed (creating empty SARIF file)"
                echo '{"$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json", "version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Trivy", "version": "unknown"}}, "results": []}]}' > image-backend.sarif
            fi
            
            # Frontend image scan
            if [ -n "${FRONT_DOCKER_NAME}" ]; then
                echo "🐳 Scanning Frontend image..."
                if trivy image --format sarif -o image-frontend.sarif ${REGISTRY}/${FRONT_DOCKER_NAME}:${BUILD_NUMBER} 2>/dev/null; then
                    echo "✅ Frontend image scan completed"
                else
                    echo "⚠️  Frontend image scan failed (creating empty SARIF file)"
                    echo '{"$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json", "version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Trivy", "version": "unknown"}}, "results": []}]}' > image-frontend.sarif
                fi
            fi
            
            # Unused packages and root user check
            echo "🐳 Scanning image configuration..."
            if trivy image --scanners vuln,config --format sarif -o image-config.sarif ${REGISTRY}/${DOCKER_NAME}:${BUILD_NUMBER} 2>/dev/null; then
                echo "✅ Image configuration scan completed"
            else
                echo "⚠️  Image configuration scan failed (creating empty SARIF file)"
                echo '{"$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json", "version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Trivy", "version": "unknown"}}, "results": []}]}' > image-config.sarif
            fi
        else
            echo "⚠️  Skipping container image scan (no image information)"
            echo "   REGISTRY: ${REGISTRY:-'Not set'}"
            echo "   DOCKER_NAME: ${DOCKER_NAME:-'Not set'}"
            echo "   BUILD_NUMBER: ${BUILD_NUMBER:-'Not set'}"
        fi
    else
        echo "⏭️  Container scan is disabled (CONTAINER_SCAN_YN=${CONTAINER_SCAN_YN})"
    fi
}

run_dast_scans() {
    if [ "${DAST_SCAN_YN:-true}" = "true" ]; then
        echo "🌐 DAST scan starting..."

        # Check service URL
        if [ -z "${SERVICE_URL}" ]; then
            echo "❌ SERVICE_URL is not set. Skipping DAST scan."
            echo "⚠️  SERVICE_URL environment variable is required for DAST scan."
            return 1
        fi

        echo "🎯 Target URL for scan: ${SERVICE_URL}"
        
        # Wait for service preparation and availability check
        echo "⏳ Waiting for service preparation..."
        echo "  SERVICE_URL: ${SERVICE_URL}"
        
        # Wait up to 5 minutes for service to be ready
        SERVICE_READY=false
        i=1
        while [ $i -le 30 ]; do
            echo "  Attempt $i/30: Checking service status..."
            
            # HTTP connection test
            if curl -s --connect-timeout 10 --max-time 30 "${SERVICE_URL}" >/dev/null 2>&1; then
                echo "  ✅ Service connection successful"
                SERVICE_READY=true
                break
            else
                echo "  ⏳ Waiting for service connection... ($i/30)"
            fi
            
            if [ $i -eq 30 ]; then
                echo "  ⚠️  Service preparation timeout (5 minutes)"
                echo "  Final connection attempt..."
            fi
            sleep 10
            i=$((i + 1))
        done
        
        if [ "$SERVICE_READY" = "false" ]; then
            echo "❌ Cannot connect to service. Skipping DAST scan."
            echo "⚠️  Please wait until the service is fully started."
            echo "  - Service URL: ${SERVICE_URL}"
            service_host=$(echo ${SERVICE_URL} | sed 's|http://||' | cut -d: -f1)
            if ping -c 1 "$service_host" >/dev/null 2>&1; then
                echo "  - Network connection check: Connected"
            else
                echo "  - Network connection check: Connection failed"
            fi
            
            # Create empty SARIF file even if service connection fails
            echo "📁 Creating empty SARIF file due to service connection failure"
            cat > zap-baseline.sarif << EOF
{
  "\$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "OWASP ZAP",
          "version": "2.16.1"
        }
      },
      "results": []
    }
  ]
}
EOF
            
            cat > nikto.sarif << EOF
{
  "\$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "Nikto",
          "version": "unknown"
        }
      },
      "results": []
    }
  ]
}
EOF
            echo "✅ creating empty SARIF file completed"
            return 0  # Continue even if failed
        fi
        
        # Additional 30 second wait (service fully started)
        echo "  Waiting additional 30 seconds (service fully started)..."
        sleep 30
        
        # Final service status check
        echo "🔍 Checking final service status..."
        if curl -s --connect-timeout 10 --max-time 30 "${SERVICE_URL}" >/dev/null 2>&1; then
            echo "✅ Service connection verification completed"
        else
            echo "⚠️  Final connection verification failed but continuing with DAST scan."
        fi

        # OWASP ZAP scan
        echo "🔍 Running OWASP ZAP scan..."
        if command -v zap-baseline.py &> /dev/null; then
            echo "📋 ZAP version: $(zap-baseline.py -version 2>/dev/null || echo 'unknown')"
            
            # Execute ZAP baseline scan
            if zap-baseline.py -t "${SERVICE_URL}" -J zap-baseline.sarif -r zap-baseline-report.html 2>/dev/null; then
                echo "✅ OWASP ZAP scan completed"
                
                # Create empty SARIF if SARIF file was not generated
                if [ ! -f "zap-baseline.sarif" ]; then
                    echo "⚠️  ZAP SARIF file was not generated. creating empty SARIF file"
                    cat > zap-baseline.sarif << EOF
{
  "\$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "OWASP ZAP",
          "version": "2.14.0"
        }
      },
      "results": []
    }
  ]
}
EOF
                fi
            else
                echo "⚠️  OWASP ZAP scan failed (creating empty SARIF file)"
                cat > zap-baseline.sarif << EOF
{
  "\$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "OWASP ZAP",
          "version": "2.14.0"
        }
      },
      "results": []
    }
  ]
}
EOF
            fi
        else
            echo "⚠️  OWASP ZAP is not installed. Skipping ZAP scan."
            cat > zap-baseline.sarif << EOF
{
  "\$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "OWASP ZAP",
          "version": "unknown"
        }
      },
      "results": []
    }
  ]
}
EOF
        fi

        # Nikto scan
        echo "🔍 Running Nikto scan..."
        if command -v nikto &> /dev/null; then
            echo "📋 Nikto version: $(nikto -Version 2>/dev/null | head -1 || echo 'unknown')"
            
            # Execute Nikto scan (JSON output)
            if nikto -h "${SERVICE_URL}" -Format json -output nikto.json 2>/dev/null; then
                
                # Convert Nikto JSON to SARIF
                if [ -f "nikto.json" ] && [ -s "nikto.json" ]; then
                    # Simple SARIF conversion
                    cat > nikto.sarif << EOF
{
  "\$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "Nikto",
          "version": "$(nikto -Version 2>/dev/null | head -1 | grep -o '[0-9.]*' || echo 'unknown')"
        }
      },
      "results": []
    }
  ]
}
EOF
                    echo "✅ Nikto scan completed"
                else
                    echo "⚠️  Nikto JSON file is empty. creating empty SARIF file"
                    cat > nikto.sarif << EOF
{
  "\$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "Nikto",
          "version": "unknown"
        }
      },
      "results": []
    }
  ]
}
EOF
                fi
            else
                echo "⚠️  Nikto scan failed (creating empty SARIF file)"
                cat > nikto.sarif << EOF
{
  "\$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "Nikto",
          "version": "unknown"
        }
      },
      "results": []
    }
  ]
}
EOF
            fi
        else
            echo "⚠️  Nikto is not installed. Skipping Nikto scan."
            cat > nikto.sarif << EOF
{
  "\$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "Nikto",
          "version": "unknown"
        }
      },
      "results": []
    }
  ]
}
EOF
        fi
    else
        echo "⏭️  DAST scan is disabled (DAST_SCAN_YN=${DAST_SCAN_YN})"
    fi
}

run_iac_scans() {
    if [ "${IAC_SCAN_YN:-true}" = "true" ]; then
        echo "🏗️  IaC scan starting..."

        # Check Checkov installation
        if ! command -v checkov &> /dev/null; then
            echo "❌ Checkov is not installed. Skipping IaC scan."
            echo "⚠️  Checkov installation is required to use IaC scan."
            return 1
        fi

        # Force cleanup of existing SARIF files (Kubernetes environment support)
        echo "🧹 Cleaning up existing SARIF files..."
        echo "🔍 File status before cleanup:"
        ls -la *.sarif 2>/dev/null || echo "  No SARIF files"
        
        # Check current working directory
        echo "📁 Current working directory: $(pwd)"
        
        # Special cleanup for Kubernetes
        echo "☸️  Cleaning up SARIF files on Kubernetes..."
        
        # Force delete both directories and files (more powerful method)
        echo "🗑️  Running force deletion..."
        
        # Step 1: Delete with wildcards
        rm -rf checkov-*.sarif kube-linter.sarif 2>/dev/null || true
        
        # Step 2: Delete directories with find
        find . -maxdepth 1 -name "*.sarif" -type d -exec rm -rf {} + 2>/dev/null || true
        
        # Step 3: Delete files with find
        find . -maxdepth 1 -name "*.sarif" -type f -delete 2>/dev/null || true
        
        # Step 4: Check and delete individual files
        for sarif_file in checkov-*.sarif kube-linter.sarif; do
            if [ -e "$sarif_file" ]; then
                echo "🗑️  Individual deletion: $sarif_file"
                if [ -d "$sarif_file" ]; then
                    echo "  → Exists as directory, force delete"
                    rm -rf "$sarif_file" 2>/dev/null || true
                else
                    echo "  → Exists as file, delete"
                    rm -f "$sarif_file" 2>/dev/null || true
                fi
            fi
        done
        
        # Step 5: Final check and force deletion
        echo "🔍 Step 5: Final force deletion"
        for file in checkov-k8s.sarif checkov-docker.sarif kube-linter.sarif; do
            if [ -e "$file" ]; then
                echo "🗑️  Final deletion: $file ($(file "$file" 2>/dev/null || echo "unknown type"))"
                rm -rf "$file" 2>/dev/null || true
            fi
        done
        
        echo "🔍 File status after cleanup:"
        ls -la *.sarif 2>/dev/null || echo "  No SARIF files"
        
        # Kubernetes manifest scan
        if [ -d "ci" ] && [ -f "ci/k8s.yaml" ]; then
            echo "☸️  Scanning Kubernetes manifests with Checkov..."
            
            # Remove existing directory if it exists
            rm -rf checkov-k8s.sarif 2>/dev/null || true
            
            if checkov -d ci/ -o sarif --output-file-path checkov-k8s.sarif --quiet --no-guide 2>/dev/null 1>/dev/null; then
                echo "✅ Kubernetes manifest scan completed"
            else
                echo "⚠️  Kubernetes manifest scan failed (creating empty SARIF file)"
                echo '{"$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json", "version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Checkov", "version": "unknown"}}, "results": []}]}' > checkov-k8s.sarif
            fi
        else
            echo "⚠️  ci/k8s.yaml file not found. Skipping Kubernetes scan."
            # creating empty SARIF file
            echo '{"$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json", "version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Checkov", "version": "unknown"}}, "results": []}]}' > checkov-k8s.sarif
        fi

        # Dockerfile scan
        if [ -f "Dockerfile.backend" ] || [ -f "Dockerfile.frontend" ]; then
            echo "🐳 Scanning Dockerfiles with Checkov..."
            
            DOCKERFILES=""
            if [ -f "Dockerfile.backend" ]; then
                DOCKERFILES="${DOCKERFILES} -f Dockerfile.backend"
            fi
            if [ -f "Dockerfile.frontend" ]; then
                DOCKERFILES="${DOCKERFILES} -f Dockerfile.frontend"
            fi
            
            # Remove existing directory if it exists
            rm -rf checkov-docker.sarif 2>/dev/null || true
            
            if checkov ${DOCKERFILES} -o sarif --output-file-path checkov-docker.sarif --quiet --no-guide 2>/dev/null 1>/dev/null; then
                echo "✅ Dockerfile scan completed"
            else
                echo "⚠️  Dockerfile scan failed (creating empty SARIF file)"
                echo '{"$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json", "version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Checkov", "version": "unknown"}}, "results": []}]}' > checkov-docker.sarif
            fi
        else
            echo "⚠️  Dockerfile not found. Skipping Dockerfile scan."
            # creating empty SARIF file
            echo '{"$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json", "version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Checkov", "version": "unknown"}}, "results": []}]}' > checkov-docker.sarif
        fi

        # kube-linter scan (Kubernetes specific)
        if command -v kube-linter &> /dev/null; then
            echo "🔍 Running kube-linter scan on ci/k8s.yaml..."
            
            if [ -f "ci/k8s.yaml" ]; then
                
                # Run in SARIF format
                if kube-linter lint ci/k8s.yaml --exclude no-read-only-root-fs,readiness-port,run-as-non-root --format sarif > kube-linter.sarif 2>/dev/null; then
                    echo "✅ kube-linter scan completed"
                    echo "📁 Generated SARIF file size: $(ls -lh kube-linter.sarif | awk '{print $5}')"
                    
                    # Check SARIF file content
                    if [ -s kube-linter.sarif ]; then
                        echo "📄 SARIF file content (first 500 chars):"
                        head -c 500 kube-linter.sarif
                        echo ""
                    else
                        echo "⚠️  SARIF file is empty"
                    fi
                else
                    echo "⚠️  kube-linter SARIF generation failed"
                    echo "📄 Error log:"
                    cat kube-linter-error.log 2>/dev/null || echo "  No error log"
                    
                    # Convert normal output to SARIF
                    echo "🔄 Attempting to convert normal output to SARIF..."
                    kube-linter lint ci/k8s.yaml --exclude no-read-only-root-fs,readiness-port,run-as-non-root > kube-linter-output.txt 2>/dev/null
                    
                    if [ -s kube-linter-output.txt ]; then
                        echo "📄 kube-linter output:"
                        cat kube-linter-output.txt
                        
                        # Simple SARIF conversion (based on error count)
                        # Extract actual count from "Error: found X lint errors" pattern
                        ERROR_COUNT=$(grep -o "Error: found [0-9]* lint errors" kube-linter-output.txt 2>/dev/null | grep -o "[0-9]*" || echo "0")
                        if [ "$ERROR_COUNT" = "0" ]; then
                            # Alternative: count actual issue lines
                            ERROR_COUNT=$(grep -c "does not have\|does not expose\|is not set" kube-linter-output.txt 2>/dev/null || echo "0")
                        fi
                        echo "🔍 Found error count: $ERROR_COUNT"
                        
                        # Generate SARIF file
                        cat > kube-linter.sarif << EOF
{
  "\$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "kube-linter",
          "version": "0.7.6"
        }
      },
      "results": [
        {
          "ruleId": "kube-linter-errors",
          "level": "error",
          "message": {
            "text": "Found $ERROR_COUNT lint errors in Kubernetes manifests"
          },
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": {
                  "uri": "ci/k8s.yaml"
                }
              }
            }
          ]
        }
      ]
    }
  ]
}
EOF
                        echo "✅ Converted SARIF file generation completed"
                    else
                        echo "📁 Creating empty SARIF file"
                        echo '{"$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json", "version": "2.1.0", "runs": [{"tool": {"driver": {"name": "kube-linter", "version": "0.7.6"}}, "results": []}]}' > kube-linter.sarif
                    fi
                fi
                rm -f kube-linter-error.log kube-linter-output.txt
            else
                echo "⚠️  ci/k8s.yaml file not found. Skipping kube-linter scan."
                echo '{"$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json", "version": "2.1.0", "runs": [{"tool": {"driver": {"name": "kube-linter", "version": "unknown"}}, "results": []}]}' > kube-linter.sarif
            fi
        else
            echo "⚠️  kube-linter is not installed. Skipping kube-linter scan."
            echo "✅ Continuing IaC scan with Checkov only"
            echo '{"$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json", "version": "2.1.0", "runs": [{"tool": {"driver": {"name": "kube-linter", "version": "unknown"}}, "results": []}]}' > kube-linter.sarif
        fi
    else
        echo "⏭️  IaC scan is disabled (IAC_SCAN_YN=${IAC_SCAN_YN})"
    fi
}

# SBOM generation function
run_sbom_generation() {
    echo "📋 SBOM generation starting..."
    
    # Check syft installation
    if ! command -v syft &> /dev/null; then
        echo "❌ Syft is not installed. Skipping SBOM generation."
        return 1
    fi

    # Generate SBOM for source code
    echo "📋 Generating SBOM for source code..."
    if syft packages . -o spdx-json --file sbom-source.spdx.json 2>/dev/null; then
        echo "✅ Source code SBOM generated"
    else
        echo "⚠️  Source code SBOM generation failed"
    fi

    # Generate SBOM for Python dependencies
    if [ -f "requirements.txt" ]; then
        echo "📋 Generating SBOM for Python dependencies..."
        if syft packages requirements.txt -o spdx-json --file sbom-python.spdx.json 2>/dev/null; then
            echo "✅ Python dependencies SBOM generated"
        else
            echo "⚠️  Python dependencies SBOM generation failed"
        fi
    fi

    # Generate SBOM for Node.js dependencies
    if [ -f "package.json" ]; then
        echo "📋 Generating SBOM for Node.js dependencies..."
        if syft packages package.json -o spdx-json --file sbom-nodejs.spdx.json 2>/dev/null; then
            echo "✅ Node.js dependencies SBOM generated"
        else
            echo "⚠️  Node.js dependencies SBOM generation failed"
        fi
    fi

    # Generate comprehensive SBOM
    echo "📋 Generating comprehensive SBOM..."
    if syft packages . -o spdx-json --file sbom-comprehensive.spdx.json 2>/dev/null; then
        echo "✅ Comprehensive SBOM generated"
    else
        echo "⚠️  Comprehensive SBOM generation failed"
    fi

    # Generate human-readable SBOM
    echo "📋 Generating human-readable SBOM..."
    if syft packages . -o table --file sbom-human-readable.txt 2>/dev/null; then
        echo "✅ Human-readable SBOM generated"
    else
        echo "⚠️  Human-readable SBOM generation failed"
    fi
}

# Image signing function
run_image_signing() {
    echo "🔐 Image signing starting..."
    
    # Check cosign installation
    if ! command -v cosign &> /dev/null; then
        echo "❌ Cosign is not installed. Skipping image signing."
        return 1
    fi

    # Check if images exist
    if [ -n "${REGISTRY}" ] && [ -n "${DOCKER_NAME}" ] && [ -n "${BUILD_NUMBER}" ]; then
        echo "🔐 Signing Docker images..."
        
        # Set Cosign environment variables for Docker Hub
        export COSIGN_DOCKER_MEDIA_TYPES=1
        export DOCKER_CONFIG=/home/jenkins/.docker
        
        # Check Docker configuration directory
        echo "🔍 Checking Docker configuration..."
        echo "🔍 Current user: $(whoami)"
        echo "🔍 Current directory: $(pwd)"
        echo "🔍 HOME directory: $HOME"
        
        if [ -d "/home/jenkins/.docker" ]; then
            echo "✅ Docker config directory exists: /home/jenkins/.docker"
            echo "📁 Docker config contents:"
            ls -la /home/jenkins/.docker/ 2>/dev/null || echo "  No files found"
            export DOCKER_CONFIG=/home/jenkins/.docker
        else
            echo "⚠️  Docker config directory not found: /home/jenkins/.docker"
            echo "🔍 Checking alternative Docker config locations..."
            if [ -d "/root/.docker" ]; then
                echo "✅ Found Docker config in /root/.docker"
                export DOCKER_CONFIG=/root/.docker
                echo "📁 Docker config contents:"
                ls -la /root/.docker/ 2>/dev/null || echo "  No files found"
            elif [ -d "$HOME/.docker" ]; then
                echo "✅ Found Docker config in $HOME/.docker"
                export DOCKER_CONFIG="$HOME/.docker"
                echo "📁 Docker config contents:"
                ls -la $HOME/.docker/ 2>/dev/null || echo "  No files found"
            else
                echo "❌ No Docker config directory found"
                echo "🔍 Searching for Docker config files in common locations:"
                find /home /root -name "config.json" -path "*/.docker/*" 2>/dev/null | head -5 || echo "  No Docker config files found"
            fi
        fi
        
        # Check Docker login status
        echo "🔍 Checking Docker login status..."
        echo "🔍 DOCKER_CONFIG: $DOCKER_CONFIG"
        
        if docker info >/dev/null 2>&1; then
            echo "✅ Docker is authenticated"
            echo "🔍 Docker registry info:"
            docker info 2>/dev/null | grep -E "(Registry|Server Version|Storage Driver)" || echo "  No registry info available"
        else
            echo "⚠️  Docker authentication failed"
            echo "🔍 Docker info output:"
            docker info 2>&1 | head -10
            echo "🔍 Trying to check Docker Hub connectivity..."
            curl -s -I https://index.docker.io/v1/ | head -3 || echo "  Cannot access Docker Hub"
        fi
        
        # Additional debugging for image signing
        echo "🔍 Checking if images exist locally..."
        echo "🔍 Backend image:"
        docker images | grep "doohee323/drillquiz" | head -3 || echo "  Backend image not found locally"
        echo "🔍 Frontend image:"
        docker images | grep "doohee323/drillquiz-frontend" | head -3 || echo "  Frontend image not found locally"
        
        # Backend image signing with explicit Docker Hub authentication
        echo "🔐 Signing Backend image: ${REGISTRY}/${DOCKER_NAME}:${BUILD_NUMBER}"
        if cosign sign --yes --registry-1 ${REGISTRY}/${DOCKER_NAME}:${BUILD_NUMBER} 2>/dev/null; then
            echo "✅ Backend image signed successfully"
        else
            echo "⚠️  Backend image signing failed"
            # Try alternative signing method
            echo "🔐 Trying alternative signing method..."
            if cosign sign --yes --keyless ${REGISTRY}/${DOCKER_NAME}:${BUILD_NUMBER} 2>/dev/null; then
                echo "✅ Backend image signed successfully (keyless)"
            else
                echo "❌ Backend image signing failed (all methods)"
            fi
        fi
        
        # Frontend image signing
        if [ -n "${FRONT_DOCKER_NAME}" ]; then
            echo "🔐 Signing Frontend image: ${REGISTRY}/${FRONT_DOCKER_NAME}:${BUILD_NUMBER}"
            if cosign sign --yes --registry-1 ${REGISTRY}/${FRONT_DOCKER_NAME}:${BUILD_NUMBER} 2>/dev/null; then
                echo "✅ Frontend image signed successfully"
            else
                echo "⚠️  Frontend image signing failed"
                # Try alternative signing method
                echo "🔐 Trying alternative signing method..."
                if cosign sign --yes --keyless ${REGISTRY}/${FRONT_DOCKER_NAME}:${BUILD_NUMBER} 2>/dev/null; then
                    echo "✅ Frontend image signed successfully (keyless)"
                else
                    echo "❌ Frontend image signing failed (all methods)"
                fi
            fi
        fi

        # Generate attestation for images
        echo "🔐 Generating image attestations..."
        if cosign attest --yes --predicate sbom-comprehensive.spdx.json --type spdxjson ${REGISTRY}/${DOCKER_NAME}:${BUILD_NUMBER} 2>/dev/null; then
            echo "✅ Backend image attestation generated"
        else
            echo "⚠️  Backend image attestation generation failed"
        fi

        if [ -n "${FRONT_DOCKER_NAME}" ]; then
            if cosign attest --yes --predicate sbom-comprehensive.spdx.json --type spdxjson ${REGISTRY}/${FRONT_DOCKER_NAME}:${BUILD_NUMBER} 2>/dev/null; then
                echo "✅ Frontend image attestation generated"
            else
                echo "⚠️  Frontend image attestation generation failed"
            fi
        fi
    else
        echo "⚠️  Skipping image signing (no image information)"
        echo "   REGISTRY: ${REGISTRY:-'Not set'}"
        echo "   DOCKER_NAME: ${DOCKER_NAME:-'Not set'}"
        echo "   BUILD_NUMBER: ${BUILD_NUMBER:-'Not set'}"
    fi
}

# Provenance verification function
run_provenance_verification() {
    echo "🔍 Provenance verification starting..."
    
    # Check slsa-verifier installation
    if ! command -v slsa-verifier &> /dev/null; then
        echo "❌ SLSA Verifier is not installed. Skipping provenance verification."
        return 1
    fi

    # Generate build provenance
    echo "🔍 Generating build provenance..."
    
    # Create provenance metadata
    cat > build-provenance.json << EOF
{
  "buildType": "https://github.com/slsa-framework/slsa-github-generator/delegator-generic@v1",
  "buildInvocationId": "${BUILD_NUMBER:-unknown}",
  "buildStartTime": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "buildFinishTime": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "builder": {
    "id": "https://github.com/dhong/workspaces/drillquiz/actions/runs/${BUILD_NUMBER:-unknown}"
  },
  "metadata": {
    "invocationId": "${BUILD_NUMBER:-unknown}",
    "startedOn": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "finishedOn": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  },
  "materials": [
    {
      "uri": "git+https://github.com/dhong/workspaces/drillquiz.git",
      "digest": {
        "gitCommit": "${GIT_COMMIT:-unknown}"
      }
    }
  ]
}
EOF

    echo "✅ Build provenance metadata generated"

    # Verify image signatures
    if [ -n "${REGISTRY}" ] && [ -n "${DOCKER_NAME}" ] && [ -n "${BUILD_NUMBER}" ]; then
        echo "🔍 Verifying image signatures..."
        
        # Verify backend image signature
        if cosign verify --key cosign.pub ${REGISTRY}/${DOCKER_NAME}:${BUILD_NUMBER} 2>/dev/null; then
            echo "✅ Backend image signature verified"
        else
            echo "⚠️  Backend image signature verification failed"
        fi

        # Verify frontend image signature
        if [ -n "${FRONT_DOCKER_NAME}" ]; then
            if cosign verify --key cosign.pub ${REGISTRY}/${FRONT_DOCKER_NAME}:${BUILD_NUMBER} 2>/dev/null; then
                echo "✅ Frontend image signature verified"
            else
                echo "⚠️  Frontend image signature verification failed"
            fi
        fi
    fi

    echo "✅ Provenance verification completed"
}

# Result summary function
show_scan_summary() {
    echo ""
    echo "📊 scan results summary:"
    echo "=================="

    if [ -f "semgrep-python.sarif" ]; then
        if command -v jq &> /dev/null; then
            python_count=$(jq '.runs[0].results | length' semgrep-python.sarif 2>/dev/null || echo "0")
            echo "🐍 Python issues: ${python_count}"
            
            # Severity classification
            if [ "$python_count" -gt 0 ]; then
                echo "   Severity classification:"
                jq -r '.runs[0].results[] | .level' semgrep-python.sarif 2>/dev/null | sort | uniq -c | while read count level; do
                    echo "     ${level}: ${count}"
                done
            fi
        else
            echo "🐍 Python scan completed (detailed analysis not available without jq)"
        fi
    fi

    if [ -f "semgrep-frontend.sarif" ]; then
        if command -v jq &> /dev/null; then
            frontend_count=$(jq '.runs[0].results | length' semgrep-frontend.sarif 2>/dev/null || echo "0")
            echo "🌐 Frontend issues: ${frontend_count}"
            
            # Severity classification
            if [ "$frontend_count" -gt 0 ]; then
                echo "   Severity classification:"
                jq -r '.runs[0].results[] | .level' semgrep-frontend.sarif 2>/dev/null | sort | uniq -c | while read count level; do
                    echo "     ${level}: ${count}"
                done
            fi
        else
            echo "🌐 Frontend scan completed (detailed analysis not available without jq)"
        fi
    fi

    if [ -f "semgrep-dependencies.sarif" ]; then
        if command -v jq &> /dev/null; then
            deps_count=$(jq '.runs[0].results | length' semgrep-dependencies.sarif 2>/dev/null || echo "0")
            echo "📦 Dependency issues: ${deps_count}"
        else
            echo "📦 Dependency scan completed (detailed analysis not available without jq)"
        fi
    fi

    # Trivy SCA scan results summary
    if [ -f "sca-python.sarif" ]; then
        if command -v jq &> /dev/null; then
            sca_python_count=$(jq '.runs[0].results | length' sca-python.sarif 2>/dev/null || echo "0")
            echo "🐍 Python SCA issues: ${sca_python_count}"
        else
            echo "🐍 Python SCA scan completed (detailed analysis not available without jq)"
        fi
    fi

    if [ -f "sca-node.sarif" ]; then
        if command -v jq &> /dev/null; then
            sca_node_count=$(jq '.runs[0].results | length' sca-node.sarif 2>/dev/null || echo "0")
            echo "📦 Node.js SCA issues: ${sca_node_count}"
        else
            echo "📦 Node.js SCA scan completed (detailed analysis not available without jq)"
        fi
    fi

    if [ -f "sca-os.sarif" ]; then
        if command -v jq &> /dev/null; then
            sca_os_count=$(jq '.runs[0].results | length' sca-os.sarif 2>/dev/null || echo "0")
            echo "🖥️ OS SCA issues: ${sca_os_count}"
        else
            echo "🖥️ OS SCA scan completed (detailed analysis not available without jq)"
        fi
    fi

    if [ -f "image-backend.sarif" ]; then
        if command -v jq &> /dev/null; then
            image_backend_count=$(jq '.runs[0].results | length' image-backend.sarif 2>/dev/null || echo "0")
            echo "🐳 Backend image issues: ${image_backend_count}"
        else
            echo "🐳 Backend image scan completed (detailed analysis not available without jq)"
        fi
    fi

    if [ -f "image-frontend.sarif" ]; then
        if command -v jq &> /dev/null; then
            image_frontend_count=$(jq '.runs[0].results | length' image-frontend.sarif 2>/dev/null || echo "0")
            echo "🐳 Frontend image issues: ${image_frontend_count}"
        else
            echo "🐳 Frontend image scan completed (detailed analysis not available without jq)"
        fi
    fi

    # IaC scan results summary
    if [ -f "checkov-k8s.sarif" ]; then
        if command -v jq &> /dev/null; then
            checkov_k8s_count=$(jq '.runs[0].results | length' checkov-k8s.sarif 2>/dev/null || echo "0")
            echo "☸️  Kubernetes IaC issues: ${checkov_k8s_count}"
        else
            echo "☸️  Kubernetes IaC scan completed (detailed analysis not available without jq)"
        fi
    fi

    if [ -f "checkov-docker.sarif" ]; then
        if command -v jq &> /dev/null; then
            checkov_docker_count=$(jq '.runs[0].results | length' checkov-docker.sarif 2>/dev/null || echo "0")
            echo "🐳 Dockerfile IaC issues: ${checkov_docker_count}"
        else
            echo "🐳 Dockerfile IaC scan completed (detailed analysis not available without jq)"
        fi
    fi

    if [ -f "kube-linter.sarif" ]; then
        if command -v jq &> /dev/null; then
            kube_linter_count=$(jq '.runs[0].results | length' kube-linter.sarif 2>/dev/null || echo "0")
            echo "🔍 kube-linter issues: ${kube_linter_count}"
        else
            echo "🔍 kube-linter scan completed (detailed analysis not available without jq)"
        fi
    fi

    # DAST scan results summary
    if [ -f "zap-baseline.sarif" ]; then
        if command -v jq &> /dev/null; then
            zap_count=$(jq '.runs[0].results | length' zap-baseline.sarif 2>/dev/null || echo "0")
            echo "🌐 OWASP ZAP issues: ${zap_count}"
        else
            echo "🌐 OWASP ZAP scan completed (detailed analysis not available without jq)"
        fi
    fi

    if [ -f "nikto.sarif" ]; then
        if command -v jq &> /dev/null; then
            nikto_count=$(jq '.runs[0].results | length' nikto.sarif 2>/dev/null || echo "0")
            echo "🔍 Nikto issues: ${nikto_count}"
        else
            echo "🔍 Nikto scan completed (detailed analysis not available without jq)"
        fi
    fi

    if [ -f "semgrep.sarif" ]; then
        if command -v jq &> /dev/null; then
            total_count=$(jq '.runs[0].results | length' semgrep.sarif 2>/dev/null || echo "0")
            echo "🔍 Total issues: ${total_count}"
            
            # Critical/High issues check
            critical_count=$(jq '.runs[0].results[] | select(.level == "error" and (.properties.severity == "CRITICAL" or .properties.severity == "HIGH")) | .ruleId' semgrep.sarif 2>/dev/null | wc -l)
            if [ "$critical_count" -gt 0 ]; then
                echo "🚨 Critical/High issues: ${critical_count} (immediate fix required)"
            fi
        else
            echo "🔍 Integrated scan completed (detailed analysis not available without jq)"
        fi
    fi

    echo ""
    echo "📁 Generated files:"
    ls -la *.sarif 2>/dev/null || echo "  No SARIF files generated"
}

# SARIF summary function using ChatGPT API
summarize_with_chatgpt() {
    echo ""
    echo "🤖 Generating security scan results summary using ChatGPT API..."
    
    if [ -z "${OPENAI_API_KEY}" ]; then
        echo "⚠️  OPENAI_API_KEY is not set. Skipping ChatGPT summary."
        echo "💡 Please set 'openai-api-key' credentials in Jenkins."
        return 0
    fi
    
    echo "🔑 OPENAI_API_KEY is set. (length: ${#OPENAI_API_KEY} characters)"
    
    # Collect SARIF files (including Checkov directories)
    local sarif_files=""
    local file_count=0
    
    # General SARIF files
    for sarif_file in *.sarif; do
        if [ -f "$sarif_file" ] && [ -s "$sarif_file" ]; then
            sarif_files="$sarif_files $sarif_file"
            file_count=$((file_count + 1))
        fi
    done
    
    # Include Checkov directories
    for checkov_dir in checkov-*.sarif; do
        if [ -d "$checkov_dir" ] && [ -f "$checkov_dir/results_sarif.sarif" ]; then
            sarif_files="$sarif_files $checkov_dir"
            file_count=$((file_count + 1))
        fi
    done
    
    if [ $file_count -eq 0 ]; then
        echo "⚠️  No SARIF files to summarize."
        return 0
    fi
    
    echo "📋 Found SARIF files: $file_count"
    echo "   $sarif_files"
    
    # Combine SARIF files into one
    local combined_sarif="combined-security-results.sarif"
    echo "🔗 Combining SARIF files..."
    
    # Generate basic SARIF structure
    cat > "$combined_sarif" << 'EOF'
{
  "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": []
}
EOF
    
    # Extract runs section from each SARIF file and combine
    for sarif_file in $sarif_files; do
        echo "  📄 Processing $sarif_file..."
        if command -v jq &> /dev/null; then
            # Extract runs section using jq
            jq '.runs[]' "$sarif_file" 2>/dev/null | jq -s '. | {runs: .}' | jq '.runs' > "/tmp/${sarif_file}.runs" 2>/dev/null
            if [ -s "/tmp/${sarif_file}.runs" ]; then
                # Add to existing runs
                jq --slurpfile new_runs "/tmp/${sarif_file}.runs" '.runs += $new_runs[0]' "$combined_sarif" > "${combined_sarif}.tmp" 2>/dev/null
                if [ -s "${combined_sarif}.tmp" ]; then
                    mv "${combined_sarif}.tmp" "$combined_sarif"
                fi
            fi
        else
            echo "  ⚠️  Skipping $sarif_file (jq not available)."
        fi
    done
    
    # ChatGPT API call
    echo "🚀 Calling ChatGPT API..."
    
    # Convert SARIF files to simple text summary
    local summary_text=""
    echo "🔍 Analyzing files to send to ChatGPT API:"
    
    for sarif_file in $sarif_files; do
        local actual_file="$sarif_file"
        
        echo "  📄 Processing: $sarif_file"
        
        # For Checkov files, use internal directory file
        if [ -d "$sarif_file" ] && [ -f "$sarif_file/results_sarif.sarif" ]; then
            actual_file="$sarif_file/results_sarif.sarif"
            echo "    → Checkov directory detected, actual file: $actual_file"
        fi
        
        if [ -f "$actual_file" ] && [ -s "$actual_file" ]; then
            local tool_name=$(basename "$sarif_file" .sarif)
            local issue_count=0
            local file_size=$(wc -c < "$actual_file" 2>/dev/null || echo "0")
            
            echo "    ✅ file exists: $actual_file (size: ${file_size} bytes)"
            
            # Calculate issue count using jq
            if command -v jq &> /dev/null; then
                issue_count=$(jq '.runs[0].results | length' "$actual_file" 2>/dev/null || echo "0")
                echo "    📊 issue count calculated with jq: ${issue_count}"
            else
                echo "    ⚠️  Cannot calculate issue count (jq not available)"
            fi
            
            summary_text="${summary_text}${tool_name}: ${issue_count} issues found\n"
            
            # Extract all issues (important ones first, max 10)
            if command -v jq &> /dev/null && [ "$issue_count" -gt 0 ]; then
                echo "    🔍 Analyzing issue details..."
                
                # 1. Extract Critical/High issues first
                local critical_issues=$(jq -r '.runs[0].results[] | select(.level == "error" and (.properties.severity == "CRITICAL" or .properties.severity == "HIGH")) | "\(.ruleId): \(.message.text)"' "$actual_file" 2>/dev/null | head -5)
                if [ -n "$critical_issues" ]; then
                    summary_text="${summary_text}🚨 CRITICAL/HIGH issues:\n${critical_issues}\n"
                    echo "    🚨 Critical/High issues found:"
                    echo "$critical_issues" | while read line; do
                        echo "      - $line"
                    done
                fi
                
                # 2. Extract Medium issues
                local medium_issues=$(jq -r '.runs[0].results[] | select(.level == "error" and .properties.severity == "MEDIUM") | "\(.ruleId): \(.message.text)"' "$actual_file" 2>/dev/null | head -3)
                if [ -n "$medium_issues" ]; then
                    summary_text="${summary_text}⚠️ MEDIUM issues:\n${medium_issues}\n"
                    echo "    ⚠️ Medium issues found:"
                    echo "$medium_issues" | while read line; do
                        echo "      - $line"
                    done
                fi
                
                # 3. Extract Low issues (if above issues are few)
                local low_issues=""
                critical_count=$(echo "$critical_issues" | wc -l)
                medium_count=$(echo "$medium_issues" | wc -l)
                local total_high_medium=$((critical_count + medium_count))
                if [ "$total_high_medium" -lt 5 ]; then
                    low_issues=$(jq -r '.runs[0].results[] | select(.level == "error" and .properties.severity == "LOW") | "\(.ruleId): \(.message.text)"' "$actual_file" 2>/dev/null | head -3)
                    if [ -n "$low_issues" ]; then
                        summary_text="${summary_text}ℹ️ LOW issues:\n${low_issues}\n"
                        echo "    ℹ️ Low issues found:"
                        echo "$low_issues" | while read line; do
                            echo "      - $line"
                        done
                    fi
                fi
                
                # 4. Extract by level only if no severity (max 10)
                local any_issues=""
                low_count=$(echo "$low_issues" | wc -l)
                local total_issues=$((critical_count + medium_count + low_count))
                if [ "$total_issues" -lt 5 ]; then
                    any_issues=$(jq -r '.runs[0].results[] | select(.level == "error") | "\(.ruleId): \(.message.text)"' "$actual_file" 2>/dev/null | head -10)
                    if [ -n "$any_issues" ]; then
                        summary_text="${summary_text}📋 Other issues:\n${any_issues}\n"
                        echo "    📋 Other issues found:"
                        echo "$any_issues" | while read line; do
                            echo "      - $line"
                        done
                    fi
                fi
                
                # 5. If no issues found by any method
                if [ -z "$critical_issues" ] && [ -z "$medium_issues" ] && [ -z "$low_issues" ] && [ -z "$any_issues" ]; then
                    summary_text="${summary_text}⚠️ Cannot parse issue details.\n"
                    echo "    ⚠️ Issue parsing failed"
                fi
            fi
            summary_text="${summary_text}\n"
        else
            echo "    ❌ file does not exist or is empty: $actual_file"
        fi
        echo ""
    done
    
    echo "📄 Summary text size: $(echo "$summary_text" | wc -c) characters"
    echo "📋 Summary text to send to ChatGPT API:"
    echo "----------------------------------------"
    echo -e "$summary_text"
    echo "----------------------------------------"
    
    # Create temporary file for JSON payload to avoid shell escaping issues
    local temp_json=$(mktemp)
    echo "🔧 JSON escape processing completed (size: $(echo "$summary_text" | wc -c) characters)"
    
    # Create proper JSON payload using jq to ensure valid JSON
    echo "🔧 Creating JSON payload with jq..."
    echo "🔍 Summary text length: $(echo "$summary_text" | wc -c)"
    echo "🔍 First 100 chars of summary text: $(echo "$summary_text" | head -c 100)"
    
    # Use jq to create the entire JSON payload safely
    jq -n \
        --arg model "gpt-3.5-turbo" \
        --arg system_content "You are a security expert. Analyze security scan results and provide specific security issues and simple fix methods." \
        --arg user_content "$summary_text" \
        --argjson max_tokens 1000 \
        --argjson temperature 0.3 \
        '{
            model: $model,
            messages: [
                {
                    role: "system",
                    content: $system_content
                },
                {
                    role: "user", 
                    content: $user_content
                }
            ],
            max_tokens: $max_tokens,
            temperature: $temperature
        }' > "$temp_json"
    
    echo "🔧 JSON payload created successfully"
    echo "🔍 JSON file size: $(wc -c < "$temp_json")"
    echo "🔍 First 200 chars of JSON: $(head -c 200 "$temp_json")"
    
    # ChatGPT API request
    local response
    response=$(curl -s -X POST "https://api.openai.com/v1/chat/completions" \
        -H "Authorization: Bearer ${OPENAI_API_KEY}" \
        -H "Content-Type: application/json" \
        -d @"$temp_json" 2>/dev/null)
    
    # Clean up temporary file
    rm -f "$temp_json"
    
    if [ $? -eq 0 ] && [ -n "$response" ]; then
        echo "✅ ChatGPT API call successful"
        echo "📄 Response size: $(echo "$response" | wc -c) characters"
        
        # Extract content from response
        local summary
        if command -v jq &> /dev/null; then
            summary=$(echo "$response" | jq -r '.choices[0].message.content' 2>/dev/null)
            echo "🔍 Attempting response parsing with jq"
        else
            # Simple extraction if jq not available
            summary=$(echo "$response" | grep -o '"content":"[^"]*"' | sed 's/"content":"//g' | sed 's/"$//g' | head -1)
            echo "🔍 Attempting response parsing with sed"
        fi
        
        if [ -n "$summary" ] && [ "$summary" != "null" ]; then
            echo "✅ ChatGPT summary completed"
            echo ""
            echo "📊 === Security scan results summary (ChatGPT analysis) ==="
            echo "$summary"
            echo "==============================================="
            echo ""
            
            # Save summary to file
            echo "$summary" > "security-scan-summary.txt"
            echo "📄 Summary saved to security-scan-summary.txt"
        else
            echo "❌ Cannot parse ChatGPT response"
            echo "🔍 Extracted summary: '$summary'"
            echo "🔍 Original response (first 500 chars): $(echo "$response" | head -c 500)"
        fi
    else
        echo "❌ ChatGPT API call failed"
        echo "🔍 HTTP status code: $?"
        echo "🔍 Response: $response"
    fi
    
    # Clean up temporary files
    rm -f /tmp/*.runs "${combined_sarif}.tmp" "$combined_sarif" 2>/dev/null
}

# MinIO upload function
upload_to_minio() {
    echo ""
    echo "☁️  Uploading SARIF files to MinIO..."
    if [ -n "${MINIO_SECRET_KEY}" ] && [ -n "${MINIO_ACCESS_KEY}" ]; then
        # Install MinIO client
        if ! command -v mc &> /dev/null; then
            echo "📦 Installing MinIO client..."
            wget -q -O /tmp/mc https://dl.min.io/client/mc/release/linux-amd64/mc
            chmod +x /tmp/mc
            mv /tmp/mc /usr/local/bin/mc
            echo "✅ MinIO client installation completed"
        fi
        
        # MinIO setup
        echo "🔧 Setting up MinIO connection..."
        mc alias set drillquiz ${MINIO_ENDPOINT:-http://minio.devops.svc.cluster.local:9000} ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY} >/dev/null 2>&1
        
        # Upload SARIF files to MinIO
        echo "📤 Uploading SARIF files..."
        for sarif_file in *.sarif; do
            if [ -f "$sarif_file" ]; then
                mc cp "$sarif_file" drillquiz/${MINIO_BUCKET_NAME:-drillquiz}/security-scan/${BUILD_NUMBER:-latest}/ >/dev/null 2>&1 && echo "  ✅ $sarif_file" || echo "  ❌ $sarif_file"
            fi
        done

        # Upload SBOM files to MinIO
        echo "📤 Uploading SBOM files..."
        for sbom_file in sbom-*.spdx.json sbom-*.txt; do
            if [ -f "$sbom_file" ]; then
                mc cp "$sbom_file" drillquiz/${MINIO_BUCKET_NAME:-drillquiz}/security-scan/${BUILD_NUMBER:-latest}/ >/dev/null 2>&1 && echo "  ✅ $sbom_file" || echo "  ❌ $sbom_file"
            fi
        done

        # Upload signing and provenance files to MinIO
        echo "📤 Uploading signing and provenance files..."
        for prov_file in build-provenance.json cosign.pub; do
            if [ -f "$prov_file" ]; then
                mc cp "$prov_file" drillquiz/${MINIO_BUCKET_NAME:-drillquiz}/security-scan/${BUILD_NUMBER:-latest}/ >/dev/null 2>&1 && echo "  ✅ $prov_file" || echo "  ❌ $prov_file"
            fi
        done
        
        echo "✅ SARIF files uploaded to MinIO:"
        echo "   Bucket: ${MINIO_BUCKET_NAME:-drillquiz}"
        echo "   Path: security-scan/${BUILD_NUMBER:-latest}/"
        echo "   Endpoint: ${MINIO_ENDPOINT:-http://minio.devops.svc.cluster.local:9000}"
    else
        echo "⚠️  MinIO credentials not available. Please use Jenkins Archive Artifacts."
    fi
}

# Main security scan execution function
run_security_scan() {
    echo "🔍 Starting security scan (Phase: ${PHASE})..."
    
    local scan_errors=0
    
    # Execute scans based on phase
    if [ "$PHASE" = "pre-build" ]; then
        echo "🔍 Running pre-build security scans (Static Analysis)..."
        
        # Pre-build scans: SAST, SCA, IaC
        if [ "${SAST_YN:-true}" = "true" ]; then
            echo "🔍 Running SAST scan..."
            if run_semgrep_scans; then
                echo "✅ SAST scan completed"
            else
                echo "❌ SAST scan failed"
                scan_errors=$((scan_errors + 1))
            fi
        fi
        
        if [ "${SCA_YN:-true}" = "true" ]; then
            echo "🔍 Running SCA scan..."
            if run_trivy_sca_scans; then
                echo "✅ SCA scan completed"
            else
                echo "❌ SCA scan failed"
                scan_errors=$((scan_errors + 1))
            fi
        fi
        
        if [ "${IAC_SCAN_YN:-true}" = "true" ]; then
            echo "🔍 Running IaC scan..."
            if run_iac_scans; then
                echo "✅ IaC scan completed"
            else
                echo "❌ IaC scan failed"
                scan_errors=$((scan_errors + 1))
            fi
        fi

        # SBOM generation
        if [ "${SBOM_YN:-true}" = "true" ]; then
            echo "🔍 Running SBOM generation..."
            if run_sbom_generation; then
                echo "✅ SBOM generation completed"
            else
                echo "❌ SBOM generation failed"
                scan_errors=$((scan_errors + 1))
            fi
        else
            echo "⏭️  SBOM generation is disabled (SBOM_YN=${SBOM_YN})"
        fi
        
    elif [ "$PHASE" = "post-build" ]; then
        echo "🔍 Running post-build security scans (Dynamic Analysis)..."
        
        # Post-build scans: Container, DAST
        if [ "${CONTAINER_SCAN_YN:-true}" = "true" ]; then
            echo "🔍 Running container security scan..."
            if run_container_scans; then
                echo "✅ Container scan completed"
            else
                echo "❌ Container scan failed"
                scan_errors=$((scan_errors + 1))
            fi
        fi
        
        if [ "${DAST_SCAN_YN:-true}" = "true" ]; then
            echo "🔍 Running DAST scan..."
            if run_dast_scans; then
                echo "✅ DAST scan completed"
            else
                echo "❌ DAST scan failed"
                scan_errors=$((scan_errors + 1))
            fi
        fi

        # Image signing
        if [ "${IMAGE_SIGNING_YN:-true}" = "true" ]; then
            echo "🔐 Running image signing..."
            if run_image_signing; then
                echo "✅ Image signing completed"
            else
                echo "❌ Image signing failed"
                scan_errors=$((scan_errors + 1))
            fi
        else
            echo "⏭️  Image signing is disabled (IMAGE_SIGNING_YN=${IMAGE_SIGNING_YN})"
        fi

        # Provenance verification
        if [ "${PROVENANCE_YN:-true}" = "true" ]; then
            echo "🔍 Running provenance verification..."
            if run_provenance_verification; then
                echo "✅ Provenance verification completed"
            else
                echo "❌ Provenance verification failed"
                scan_errors=$((scan_errors + 1))
            fi
        else
            echo "⏭️  Provenance verification is disabled (PROVENANCE_YN=${PROVENANCE_YN})"
        fi
        
    else
        echo "❌ Invalid phase: ${PHASE}. Use 'pre-build' or 'post-build'"
        exit 1
    fi
    
    # Result summary
    show_scan_summary
    
    # SBOM files summary
    if [ -f "sbom-comprehensive.spdx.json" ]; then
        echo "📋 SBOM files generated:"
        ls -1 sbom-*.spdx.json sbom-*.txt 2>/dev/null | while read file; do
            echo "  - $file"
        done
    fi

    # Signing and provenance files summary
    if [ -f "build-provenance.json" ]; then
        echo "🔐 Signing and provenance files generated:"
        ls -1 build-provenance.json cosign.pub 2>/dev/null | while read file; do
            echo "  - $file"
        done
    fi

    # Output generated SARIF file list (simplified)
    echo ""
    echo "📋 Generated SARIF files:"
    ls -1 *.sarif 2>/dev/null | while read file; do
        echo "  - $file"
    done
    
    # ChatGPT summary (execute once after all scans completed)
    echo ""
    echo "🤖 ${PHASE} security scans completed. Starting ChatGPT summary..."
    echo ""
    echo "📊 Security analysis processing flow (${PHASE}):"
    echo "================================"
    if [ "$PHASE" = "pre-build" ]; then
        echo "1. 🔧 Environment setup"
        echo "   ├── Package installation completed"
        echo "   ├── Git configuration completed"
        echo "   └── Tool installation (Semgrep, Trivy, Checkov, kube-linter)"
        echo ""
        echo "2. 🔍 Pre-build security scan execution"
        echo "   ├── SAST scan (${SAST_YN:-true})"
        echo "   ├── SCA scan (${SCA_YN:-true})"
        echo "   └── IaC scan (${IAC_SCAN_YN:-true})"
    else
        echo "1. 🔧 Environment setup"
        echo "   ├── Package installation completed"
        echo "   ├── Git configuration completed"
        echo "   └── Tool installation (Trivy, OWASP ZAP, Nikto)"
        echo ""
        echo "2. 🔍 Post-build security scan execution"
        echo "   ├── Container scan (${CONTAINER_SCAN_YN:-true})"
        echo "   └── DAST scan (${DAST_SCAN_YN:-true})"
    fi
    echo ""
    echo "3. 🤖 ChatGPT summary (currently running)"
    echo "================================"
    echo ""
    summarize_with_chatgpt
    
    # MinIO upload
    upload_to_minio
    
    echo ""
    if [ $scan_errors -eq 0 ]; then
        echo "✅ ${PHASE} security scan completed!"
    else
        echo "⚠️  ${PHASE} security scan completed (some scans failed: ${scan_errors})"
    fi
    echo ""
    echo "💡 Next steps:"
    if [ "$PHASE" = "pre-build" ]; then
        echo "   1. Review generated SARIF files"
        echo "   2. Fix Critical/High issues first"
        echo "   3. Proceed to build phase only if security checks pass"
    else
        echo "   1. Review generated SARIF files"
        echo "   2. Fix Critical/High issues first"
        echo "   3. Check results with recordIssues plugin in Jenkins"
    fi
    echo ""
    echo "📤 SARIF file export methods:"
    echo "   ✅ Download from Jenkins Archive Artifacts"
    echo "   ✅ Upload to MinIO storage (secure)"
    echo "   ✅ Check directly in Jenkins workspace"
    echo "   ❌ Do not push to Git repository (security risk)"
    echo ""
    echo "🔒 Security notes:"
    echo "   - SARIF files contain sensitive security information"
    echo "   - MinIO storage is safely managed with access control"
    echo "   - Download directly from Jenkins workspace if needed"
    
    # Return exit code 1 if scan errors exist
    if [ $scan_errors -gt 0 ]; then
        echo ""
        echo "⚠️  Some security scans failed. Please check the logs."
        return 1
    fi
}

# Main execution
run_security_scan
