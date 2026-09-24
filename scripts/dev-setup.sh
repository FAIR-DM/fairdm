#!/usr/bin/env bash
# Quick setup script for FairDM development environment
set -e

echo "🚀 Setting up FairDM development environment..."
echo ""

# Install dependencies
echo "📦 Installing dependencies with uv..."
uv sync --group docs

# Install git hooks
echo ""
echo "🪝 Installing git hooks for automatic validation..."
uv run invoke install-hooks

# Run initial format to ensure code is clean
echo ""
echo "✨ Formatting codebase..."
uv run invoke format || true

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Create a branch: git checkout -b feature/your-feature"
echo "   2. Make your changes"
echo "   3. Run tests: uv run invoke test"
echo "   4. Push (hooks will auto-validate): git push"
echo ""
echo "💡 See CONTRIBUTING.md for full development workflow"
echo ""
