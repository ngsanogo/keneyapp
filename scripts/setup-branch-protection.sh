#!/bin/bash

# GitHub Branch Protection Configuration Script
# This script sets up recommended branch protection rules for KeneyApp
# Usage: bash setup-branch-protection.sh

set -e

REPO_OWNER="${GITHUB_REPOSITORY_OWNER:=ngsanogo}"
REPO_NAME="${GITHUB_REPOSITORY#*/}"
BRANCH="main"
API_BASE="https://api.github.com/repos/$REPO_OWNER/$REPO_NAME"

echo "🔒 Setting up branch protection for $REPO_OWNER/$REPO_NAME ($BRANCH)"

# Verify GitHub token
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN environment variable not set"
    exit 1
fi

# Configure branch protection
curl -X PUT \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token $GITHUB_TOKEN" \
  "$API_BASE/branches/$BRANCH/protection" \
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": [
        "quick-checks",
        "backend-test (Python 3.13)",
        "frontend-test (Node 20)",
        "security-check",
        "integration-test",
        "final-status"
      ]
    },
    "enforce_admins": true,
    "required_pull_request_reviews": {
      "dismiss_stale_reviews": true,
      "require_code_owner_reviews": false,
      "required_approving_review_count": 1
    },
    "restrictions": null,
    "allow_force_pushes": false,
    "allow_deletions": false,
    "required_conversation_resolution": true,
    "required_linear_history": false
  }'

echo "✅ Branch protection configured successfully!"

# Optional: Require signed commits
echo ""
echo "📝 Optional: Enabling signed commits requirement..."
curl -X PATCH \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token $GITHUB_TOKEN" \
  "$API_BASE/branches/$BRANCH/protection/required_signatures" \
  -d '{"required": true}' 2>/dev/null || echo "⚠️ Signed commits not available on this plan"

echo ""
echo "🎉 All configurations complete!"
