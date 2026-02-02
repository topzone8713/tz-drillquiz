#!/usr/bin/env bash

# Script to fix venv/bin/activate issue in all test scripts
# Usage: ./fix-venv-issue.sh

echo "Fixing venv/bin/activate issue in all test scripts..."

# List of scripts to fix
SCRIPTS_TO_FIX="uc-1.3-profile.sh uc-1.4-password.sh uc-1.5-data-reset.sh uc-1.6-withdrawal.sh uc-2.1-file-upload.sh uc-2.2-file-download.sh uc-3.1-exam-creation.sh uc-3.2-exam-taking.sh uc-3.3-exam-results.sh uc-3.4-wrong-notes.sh uc-4.1-study-creation.sh uc-4.2-study-members.sh uc-4.3-study-tasks.sh uc-5.1-voice-mode.sh uc-5.2-ai-mock-interview.sh"

for script in $SCRIPTS_TO_FIX; do
    if [ -f "$script" ]; then
        echo "Processing $script..."
        
        # Replace source venv/bin/activate with system python
        sed -i '' 's|source venv/bin/activate|# source venv/bin/activate (using system python)|g' "$script"
        
        echo "  ✓ Fixed venv issue in $script"
    else
        echo "  ⚠️  Script not found: $script"
    fi
done

echo ""
echo "All scripts have been updated to use system Python instead of venv!"
echo ""
echo "Changes made:"
echo "  - Replaced 'source venv/bin/activate' with comment"
echo "  - Using system python3 instead of virtual environment"
echo ""
echo "The scripts should now work in Jenkins containers without venv."
