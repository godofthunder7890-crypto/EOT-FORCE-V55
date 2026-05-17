#!/bin/bash
set -e

if [ -z "$GITHUB_ACCESS_TOKEN" ]; then
  echo "ERROR: GITHUB_ACCESS_TOKEN secret not set"
  exit 1
fi

if [ -z "$GITHUB_REPO" ]; then
  echo "ERROR: GITHUB_REPO secret not set"
  exit 1
fi

cd "$(git rev-parse --show-toplevel)"

REMOTE_URL="https://${GITHUB_ACCESS_TOKEN}@github.com/${GITHUB_REPO}.git"

git config user.email "replit-agent@replit.com"
git config user.name "Replit Agent"

if git remote get-url github &>/dev/null; then
  git remote set-url github "$REMOTE_URL"
else
  git remote add github "$REMOTE_URL"
fi

BRANCH=$(git --no-optional-locks rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")

echo "Pushing to GitHub: $GITHUB_REPO (branch: $BRANCH)..."
git push github "$BRANCH" --force
echo "Done! Successfully pushed to https://github.com/$GITHUB_REPO"
