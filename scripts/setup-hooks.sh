#!/bin/bash
# Install the project's git hooks directly into .git/hooks/.
# Run this once after cloning: bash scripts/setup-hooks.sh
# Also called automatically by scripts/post-merge.sh after every task merge.
set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_SRC="$REPO_ROOT/scripts/hooks"
HOOKS_DEST="$REPO_ROOT/.git/hooks"

for hook in "$HOOKS_SRC"/*; do
  name="$(basename "$hook")"
  cp "$hook" "$HOOKS_DEST/$name"
  chmod +x "$HOOKS_DEST/$name"
  echo "Installed hook: $name"
done

echo "Git hooks installed into $HOOKS_DEST"
