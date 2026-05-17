#!/bin/bash
set -e

# Install pnpm dependencies (for any remaining Node.js lib packages)
pnpm install --frozen-lockfile

# Push DB schema — non-fatal, only runs if DATABASE_URL is available
if [ -n "${DATABASE_URL:-}" ]; then
  pnpm --filter @workspace/db push || echo "DB push skipped or failed (non-fatal)"
fi

# Reinstall git hooks into .git/hooks/ so they survive container restarts
bash "$(git rev-parse --show-toplevel)/scripts/setup-hooks.sh"

# Push current state to GitHub immediately after merge
if [ -n "${GITHUB_ACCESS_TOKEN:-}" ] && [ -n "${GITHUB_REPO:-}" ]; then
  echo "Pushing to GitHub..."
  bash "$(git rev-parse --show-toplevel)/scripts/github-push.sh"
else
  echo "Skipping GitHub push: GITHUB_ACCESS_TOKEN or GITHUB_REPO not set"
fi
