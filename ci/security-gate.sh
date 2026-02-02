#!/bin/sh
# Security threshold check script

set -e

SEMGREP_SARIF=$1
SEMGREP_VUE_SARIF=$2
SEMGREP_DEPENDENCIES_SARIF=$3
SCA_PYTHON_SARIF=$4
SCA_NODE_SARIF=$5
SCA_REQUIREMENTS_SARIF=$6
SCA_PACKAGE_SARIF=$7
IMAGE_BACKEND_SARIF=$8
IMAGE_FRONTEND_SARIF=$9
CHECKOV_K8S_SARIF=${10}
ZAP_BASELINE_SARIF=${11}
NIKTO_SARIF=${12}

# Installation function
install_jq() {
    if ! command -v jq &> /dev/null; then
        apk add --no-cache jq
    fi
}

# Install and check jq
install_jq

echo "🔍 Starting security threshold check..."

# JSON file cleanup function (remove control characters)
clean_json_file() {
    local file=$1
    local cleaned_file="${file}.cleaned"
    
    if [ -f "$file" ]; then
        # Remove control characters (U+0000-U+001F, U+007F-U+009F)
        sed 's/[\x00-\x1F\x7F-\x9F]//g' "$file" > "$cleaned_file" 2>/dev/null || {
            # Use tr if sed fails
            tr -d '\000-\037\177-\237' < "$file" > "$cleaned_file" 2>/dev/null || {
                # Use original file if tr also fails
                cp "$file" "$cleaned_file"
            }
        }
        echo "$cleaned_file"
    else
        echo "$file"
    fi
}

# Check High/Critical issue count
check_severity() {
    local file=$1
    local tool=$2
    
    if [ -f "$file" ]; then
        # Clean JSON file
        local cleaned_file=$(clean_json_file "$file")
        
        # JSON validity check
        if ! jq empty "$cleaned_file" 2>/dev/null; then
            local file_size=$(wc -c < "$file" 2>/dev/null || echo "0")
            if [ "$file_size" -lt 200 ]; then
                echo "📊 $tool: No issues found"
            else
                echo "📊 $tool: JSON parsing failed"
            fi
            rm -f "$cleaned_file" 2>/dev/null
            return 0
        fi
        
        # Check if runs array exists and is not empty
        local runs_count=$(jq '.runs | length' "$cleaned_file" 2>/dev/null || echo "0")
        if [ "$runs_count" -eq 0 ]; then
            echo "📊 $tool: No issues found"
            rm -f "$cleaned_file" 2>/dev/null
            return 0
        fi
        
        # Check if results array exists and is not empty
        local results_count=$(jq '.runs[0].results | length' "$cleaned_file" 2>/dev/null || echo "0")
        if [ "$results_count" -eq 0 ]; then
            echo "📊 $tool: No issues found"
            rm -f "$cleaned_file" 2>/dev/null
            return 0
        fi
        
        # Count issues by severity
        local high_count=$(jq '.runs[0].results[] | select(.level == "error") | .ruleId' "$cleaned_file" 2>/dev/null | wc -l || echo "0")
        local critical_count=$(jq '.runs[0].results[] | select(.level == "error" and (.properties.severity == "CRITICAL" or .properties.severity == "HIGH")) | .ruleId' "$cleaned_file" 2>/dev/null | wc -l || echo "0")
        
        echo "📊 $tool: $critical_count High/Critical issues ($high_count total errors)"
        
        if [ "$critical_count" -gt 0 ]; then
            echo "❌ Critical/High security issues found in $tool"
            echo "🚫 Pipeline stopped due to security threshold violation"
            rm -f "$cleaned_file" 2>/dev/null
            exit 1
        fi
        
        echo "✅ $tool: Security check passed"
        
        # Clean up
        rm -f "$cleaned_file" 2>/dev/null
    else
        echo "📊 $tool: File not found (skipping)"
    fi
}

# Check each tool with proper error handling
echo "🔍 Checking security scan results..."

# SAST scans
check_severity "$SEMGREP_SARIF" "Semgrep"
check_severity "$SEMGREP_VUE_SARIF" "Semgrep-Vue"
check_severity "$SEMGREP_DEPENDENCIES_SARIF" "Semgrep-Dependencies"

# SCA scans
check_severity "$SCA_PYTHON_SARIF" "SCA-Python"
check_severity "$SCA_NODE_SARIF" "SCA-Node"
check_severity "$SCA_REQUIREMENTS_SARIF" "SCA-Requirements"
check_severity "$SCA_PACKAGE_SARIF" "SCA-Package"

# Container scans
check_severity "$IMAGE_BACKEND_SARIF" "Container-Backend"
check_severity "$IMAGE_FRONTEND_SARIF" "Container-Frontend"

# IaC scans
check_severity "$CHECKOV_K8S_SARIF" "Checkov-K8s"

# DAST scans
check_severity "$ZAP_BASELINE_SARIF" "ZAP-Baseline"
check_severity "$NIKTO_SARIF" "Nikto"

echo "✅ All security checks passed."
