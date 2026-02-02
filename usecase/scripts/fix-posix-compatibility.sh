#!/usr/bin/env bash

# Script to fix POSIX compatibility issues in all test scripts
# Usage: ./fix-posix-compatibility.sh

echo "Fixing POSIX compatibility issues in all test scripts..."

# Find all .sh files in the current directory
for file in *.sh; do
    if [ "$file" != "fix-posix-compatibility.sh" ] && [ "$file" != "test-config.sh" ] && [ "$file" != "uc-all.sh" ]; then
        echo "Processing $file..."
        
        # 1. Change shebang from #!/bin/bash to #!/bin/sh
        sed -i '' 's|#!/bin/bash|#!/bin/sh|g' "$file"
        
        # 2. Replace ${BASH_SOURCE[0]} with $0
        sed -i '' 's|${BASH_SOURCE\[0\]}|$0|g' "$file"
        
        # 3. Replace ((var++)) with var=$((var + 1))
        sed -i '' 's|((\([A-Z_]*\)++))|\1=$((\1 + 1))|g' "$file"
        
        # 4. Replace local keyword with regular variables
        sed -i '' 's|local \([a-zA-Z_][a-zA-Z0-9_]*\)=|\1=|g' "$file"
        
        # 6. Replace TESTS_FAILED++ with TESTS_FAILED=$((TESTS_FAILED + 1))
        sed -i '' 's|TESTS_FAILED++|TESTS_FAILED=$((TESTS_FAILED + 1))|g' "$file"
        
        # 7. Replace TESTS_PASSED++ with TESTS_PASSED=$((TESTS_PASSED + 1))
        sed -i '' 's|TESTS_PASSED++|TESTS_PASSED=$((TESTS_PASSED + 1))|g' "$file"
        
        # 8. Replace TESTS_TOTAL++ with TESTS_TOTAL=$((TESTS_TOTAL + 1))
        sed -i '' 's|TESTS_TOTAL++|TESTS_TOTAL=$((TESTS_TOTAL + 1))|g' "$file"
        
        echo "  ✓ Fixed POSIX compatibility issues in $file"
    fi
done

echo ""
echo "All files have been updated for POSIX compatibility!"
echo ""
echo "Changes made:"
echo "  - Changed #!/bin/bash to #!/bin/sh"
echo "  - Replaced \${BASH_SOURCE[0]} with \$0"
echo "  - Converted ((var++)) to var=\$((var + 1))"
echo "  - Removed 'local' keyword"
echo "  - Fixed TESTS_*++ syntax"
echo ""
echo "The scripts should now work with /bin/sh in Jenkins containers."