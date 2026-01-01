#!/bin/bash
# Validate LeekScript code using local generator

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GENERATOR_DIR="$SCRIPT_DIR/leek-wars-generator"

if [ -z "$1" ]; then
    echo "Usage: $0 <file.leek>"
    exit 1
fi

# Convert to absolute path
AI_FILE="$(realpath "$1")"

# Run from generator directory so it finds data files
cd "$GENERATOR_DIR"
java -jar generator.jar --analyze "$AI_FILE"
