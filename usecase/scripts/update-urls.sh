#!/usr/bin/env bash

# Script to update hardcoded URLs in all test scripts to use environment variables
# Usage: ./update-urls.sh

echo "Updating hardcoded URLs to use environment variables..."

# Find all .sh files in the current directory
for file in *.sh; do
    if [ "$file" != "update-urls.sh" ] && [ "$file" != "test-config.sh" ]; then
        echo "Processing $file..."
        
        # Add configuration loading at the top (after shebang and before color definitions)
        if ! grep -q "test-config.sh" "$file"; then
            # Find the line with color definitions and add config loading before it
            if grep -q "RED='\\\\033\[0;31m'" "$file"; then
                sed -i '' '/RED='\''\\033\[0;31m'\''/i\
# Load test configuration\
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\
source "$SCRIPT_DIR/test-config.sh"\
' "$file"
            fi
        fi
        
        # Replace hardcoded URLs with environment variables
        sed -i '' 's|http://localhost:8000|$BACKEND_URL|g' "$file"
        sed -i '' 's|http://localhost:8080|$FRONTEND_URL|g' "$file"
        sed -i '' 's|/Users/dhong/workspaces/drillquiz|$PROJECT_ROOT|g' "$file"
        
        echo "  ✓ Updated $file"
    fi
done

echo ""
echo "All files have been updated!"
echo ""
echo "Environment variables used:"
echo "  BACKEND_URL - Backend server URL (default: http://localhost:8000)"
echo "  FRONTEND_URL - Frontend server URL (default: http://localhost:8080)"
echo "  PROJECT_ROOT - Project root directory (default: /Users/dhong/workspaces/drillquiz)"
echo ""
echo "Example usage:"
echo "  # Local development"
echo "  ./uc-all.sh"
echo ""
echo "  # Kubernetes environment"
echo "  BACKEND_URL=http://drillquiz-backend:8000 FRONTEND_URL=http://drillquiz-frontend:8080 ./uc-all.sh"
echo ""
echo "  # Custom environment"
echo "  BACKEND_URL=https://api.drillquiz.com FRONTEND_URL=https://drillquiz.com PROJECT_ROOT=/app ./uc-all.sh"
