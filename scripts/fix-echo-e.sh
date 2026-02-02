#!/bin/bash
# Fix echo -e to printf in all test scripts

for file in usecase/scripts/uc-*.sh; do
    if [ -f "$file" ]; then
        echo "Fixing $file..."
        # Replace echo -e with printf
        sed -i.bak 's/echo -e "${BLUE}\[INFO\]"${NC} $1/printf "${BLUE}[INFO]${NC} %s\\n" "$1"/g' "$file"
        sed -i.bak 's/echo -e "${GREEN}\[SUCCESS\]"${NC} $1/printf "${GREEN}[SUCCESS]${NC} %s\\n" "$1"/g' "$file"
        sed -i.bak 's/echo -e "${YELLOW}\[WARNING\]"${NC} $1/printf "${YELLOW}[WARNING]${NC} %s\\n" "$1"/g' "$file"
        sed -i.bak 's/echo -e "${RED}\[ERROR\]"${NC} $1/printf "${RED}[ERROR]${NC} %s\\n" "$1"/g' "$file"
        
        # Clean up backup files
        rm -f "$file.bak"
    fi
done

echo "All echo -e commands have been fixed to printf"
