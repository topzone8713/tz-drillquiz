#!/usr/bin/env bash

# Script to fix POSIX compatibility issues in all remaining test scripts
# Usage: ./fix-all-posix.sh

echo "Fixing POSIX compatibility issues in all remaining test scripts..."

# List of scripts to fix (excluding already fixed ones)
SCRIPTS_TO_FIX="uc-1.6-withdrawal.sh uc-2.1-file-upload.sh uc-2.2-file-download.sh uc-3.1-exam-creation.sh uc-3.2-exam-taking.sh uc-3.3-exam-results.sh uc-3.4-wrong-notes.sh uc-4.1-study-creation.sh uc-4.2-study-members.sh uc-4.3-study-tasks.sh uc-5.1-voice-mode.sh uc-5.2-ai-mock-interview.sh"

for script in $SCRIPTS_TO_FIX; do
    if [ -f "$script" ]; then
        echo "Processing $script..."
        
        # 1. Change shebang from #!/bin/bash to #!/bin/sh
        sed -i '' 's|#!/bin/bash|#!/bin/sh|g' "$script"
        
        # 2. Replace ${BASH_SOURCE[0]} with $0
        sed -i '' 's|${BASH_SOURCE\[0\]}|$0|g' "$script"
        
        # 3. Replace ((TESTS_FAILED++)) with TESTS_FAILED=$((TESTS_FAILED + 1))
        sed -i '' 's|((TESTS_FAILED++))|TESTS_FAILED=$((TESTS_FAILED + 1))|g' "$script"
        
        # 4. Replace ((TESTS_PASSED++)) with TESTS_PASSED=$((TESTS_PASSED + 1))
        sed -i '' 's|((TESTS_PASSED++))|TESTS_PASSED=$((TESTS_PASSED + 1))|g' "$script"
        
        # 5. Replace ((TESTS_TOTAL++)) with TESTS_TOTAL=$((TESTS_TOTAL + 1))
        sed -i '' 's|((TESTS_TOTAL++))|TESTS_TOTAL=$((TESTS_TOTAL + 1))|g' "$script"
        
        echo "  ✓ Fixed POSIX compatibility issues in $script"
    else
        echo "  ⚠️  Script not found: $script"
    fi
done

echo ""
echo "All remaining scripts have been updated for POSIX compatibility!"
echo ""
echo "Changes made:"
echo "  - Changed #!/bin/bash to #!/bin/sh"
echo "  - Replaced \${BASH_SOURCE[0]} with \$0"
echo "  - Converted ((var++)) to var=\$((var + 1))"
echo ""
echo "The scripts should now work with /bin/sh in Jenkins containers."
