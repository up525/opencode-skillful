#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)/.opencode/skills/glm-vision"
TARGET_DIR="${HOME}/.config/opencode/skills/glm-vision"

mkdir -p "$(dirname "$TARGET_DIR")"
rm -rf "$TARGET_DIR"
cp -R "$SOURCE_DIR" "$TARGET_DIR"

echo "Installed glm-vision skill to: $TARGET_DIR"
echo "Set one of these before using the fallback client:"
echo "  export ZHIPU_API_KEY='your-key'"
echo "  export Z_AI_API_KEY='your-key'"
echo "Optional: merge opencode.example.jsonc into ~/.config/opencode/opencode.json"
