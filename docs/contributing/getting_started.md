# Contributing to FairDM

This guide outlines the workflow for contributing code, documentation, and other improvements to the FairDM framework. By following these steps, you can fork the repository, make changes, run quality checks, and submit a pull request.

```{important}
**Read the constitution first**: Before making significant changes, review the [FairDM Constitution](https://github.com/FAIR-DM/fairdm/blob/main/.specify/memory/constitution.md) to understand the framework's core principles, design constraints, and development workflow. All contributions should align with these principles.
```

## Prerequisites

Before you begin, ensure you have completed the environment setup:

- **[Development environment set up](before_you_start.md)**: Follow the setup guide to install Python, Poetry, Git, PostgreSQL (optional), and clone the repository
- **[Quality gates understood](django_dev.md)**: Familiarize yourself with tests, type checking, linting, and documentation builds

If you haven't set up your environment yet, start with [Before You Start](before_you_start.md).

## Contribution Workflow Overview

The FairDM contribution workflow follows a standard Git-based process:

1. **Identify or create an issue**: Discuss your proposed change
2. **Fork and clone**: Create your personal copy of the repository
3. **Create a feature branch**: Work in isolation from the main codebase
4. **Make changes**: Implement your feature or fix
5. **Write tests**: Ensure your changes are covered by tests
6. **Run quality gates**: Verify tests, type checking, linting, and docs build
7. **Commit and push**: Save your changes to your fork
8. **Submit a pull request**: Propose your changes to the main repository
9. **Address feedback**: Respond to review comments and make requested changes
10. **Merge**: Once approved, your changes are merged into main

```{tip}
**Small, focused pull requests**: Break large changes into smaller, reviewable chunks. This makes reviews faster and reduces the risk of conflicts.
```

## Step 1: Identify or Create an Issue

Before starting work, check if an issue exists for your proposed change:

1. **Search existing issues**: [GitHub Issues](https://github.com/FAIR-DM/fairdm/issues)
2. **If no issue exists**, create one:
   - **Bug reports**: Describe the problem, steps to reproduce, expected vs actual behavior
   - **Feature requests**: Explain the use case, proposed solution, and how it aligns with FairDM's constitution
   - **Documentation improvements**: Describe what's unclear or missing

3. **Discuss first for major changes**: For significant architectural changes, new features, or changes that affect the constitution, open a **Discussion** first to gather feedback before coding.

```{important}
**Constitution alignment**: When proposing features or changes, explain how they align with FairDM's core principles (FAIR-first, domain-driven, configuration over code, opinionated defaults, etc.). Proposals that conflict with the constitution may be rejected unless a strong case for amending the constitution is made.
```

## Step 2: Fork and Clone the Repository

If you haven't already:

1. **Fork the repository** on GitHub:
   - Navigate to [https://github.com/FAIR-DM/fairdm](https://github.com/FAIR-DM/fairdm)
   - Click **Fork** in the top-right corner

2. **Clone your fork** to your local machine:

   ```bash
   git clone https://github.com/YOUR-USERNAME/fairdm.git
   cd fairdm
   ```

3. **Add the upstream remote** (to keep your fork in sync):

   ```bash
   git remote add upstream https://github.com/FAIR-DM/fairdm.git
   ```

## Step 3: Create a Feature Branch

Create a new branch for your contribution:

```bash
git checkout -b feature/your-feature-name
```

**Branch naming conventions**:

- `feature/description`: New features (e.g., `feature/add-polymorphic-filters`)
- `fix/description`: Bug fixes (e.g., `fix/measurement-save-validation`)
- `docs/description`: Documentation changes (e.g., `docs/improve-getting-started`)
- `refactor/description`: Code refactoring without functional changes

Replace `<branch_name>` with a descriptive name that reflects the nature of your changes.

## Step 4: Make Your Changes

1. **Open the VS Code workspace** (recommended):

   - Open the project in VS Code
   - Select the `fairdm.code-workspace` file to open the project workspace
   - Install the recommended extensions when prompted (Python, Django, mypy, etc.)

2. **Make your changes**:

   - Follow the coding style guidelines in [Python Code Development](django_dev.md)
   - Use meaningful variable and function names
   - Add type hints to function signatures
   - Write docstrings for classes and public functions
   - Keep functions small and focused (single responsibility)

3. **Check alignment with constitution**:

   - If adding new models: Are they domain-driven and polymorphic where appropriate?
   - If adding configuration: Is it declarative and easy to understand?
   - If adding UI: Does it follow Bootstrap 5 conventions and require minimal custom CSS?
   - If adding dependencies: Are they well-maintained and aligned with the tech stack?

```{tip}
**Incremental commits**: Commit your changes incrementally as you work. This makes it easier to review and revert if needed.
```

## Step 5: Write Tests for Your Changes

All code changes must include tests. See the [Python Code Development guide](django_dev.md) for testing guidelines.

### For New Features

1. **Write tests first** (TDD approach): Define the expected behavior before implementing
2. **Test the happy path**: Verify the feature works as intended
3. **Test edge cases**: What happens with invalid input, missing data, etc.?
4. **Test integration**: If your feature interacts with other components, test those interactions

### For Bug Fixes

1. **Write a failing test**: Reproduce the bug in a test
2. **Fix the bug**: Implement the fix
3. **Verify the test passes**: Confirm the bug is resolved

### Run Tests Locally

```bash
poetry run pytest
```

Ensure all tests pass before proceeding.

## Step 6: Run Quality Gates

Before committing, run all quality gates locally:

### 1. Tests

```bash
poetry run pytest
```

### 2. Type Checking

```bash
poetry run mypy fairdm
```

### 3. Linting

```bash
poetry run ruff check fairdm
```

Auto-fix issues where possible:

```bash
poetry run ruff check --fix fairdm
```

### 4. Documentation Build (if you changed docs)

```bash
poetry run sphinx-build -W -b html docs docs/_build/html
```

```{important}
**All quality gates must pass**: Pull requests that fail any quality gate will not be merged. Run these checks locally to avoid CI failures.
```

## Step 7: Commit Your Changes

1. **Stage your changes**:

   ```bash
   git add .
   ```

   Or stage specific files:

   ```bash
   git add fairdm/core/models.py tests/test_core/test_models.py
   ```

2. **Commit with a clear message**:

   ```bash
   git commit -m "Add polymorphic filtering for Measurements

   - Implement filter_by_type method on MeasurementQuerySet
   - Add tests for filtering by measurement subclass
   - Update documentation with usage example

   Fixes #123"
   ```

**Commit message guidelines**:

- **First line**: Short summary (50 characters or less)
- **Blank line**: Separates summary from body
- **Body**: Detailed explanation (wrapped at 72 characters)
  - What changed and why
  - Any relevant context or decisions
- **Footer**: Reference issues (e.g., `Fixes #123`, `Closes #456`, `Relates to #789`)

## Step 8: Push Your Branch to Your Fork

```bash
git push origin feature/your-feature-name
```

## Step 9: Submit a Pull Request

1. **Visit your fork on GitHub**: You should see a prompt to create a pull request
2. **Click "Compare & pull request"**
3. **Fill out the PR template**:
   - **Title**: Clear, concise summary (e.g., "Add polymorphic filtering for Measurements")
   - **Description**:
     - What problem does this solve?
     - What changes were made?
     - How was it tested?
     - How does it align with the constitution?
   - **Related issues**: Link to the issue (e.g., `Fixes #123`)
   - **Screenshots/GIFs**: If UI changes, include visuals
   - **Checklist**: Confirm all quality gates passed

4. **Request review**: Tag relevant maintainers or leave it to auto-assignment

```{tip}
**Draft pull requests**: If your work is in progress, open a **Draft PR** to get early feedback. Convert it to "Ready for review" when complete.
```

## Step 10: Address Review Feedback

Reviewers may request changes:

1. **Respond to comments**: Ask clarifying questions if needed
2. **Make requested changes**: Commit and push to the same branch
3. **Re-run quality gates**: Ensure changes don't break tests or linting
4. **Request re-review**: Once changes are made, request another review

```{important}
**Be responsive and respectful**: Code review is collaborative. Reviewers are helping improve the code, not criticizing you personally. Respond to feedback promptly and professionally.
```

## Step 11: Merge

Once approved by maintainers, your pull request will be merged into the `main` branch. Congratulations! 🎉

### After Merging

- **Sync your fork** with upstream:

  ```bash
  git checkout main
  git pull upstream main
  git push origin main
  ```

- **Delete your feature branch** (optional):

  ```bash
  git branch -d feature/your-feature-name
  git push origin --delete feature/your-feature-name
  ```

## Keeping Your Fork in Sync

Periodically sync your fork with the upstream repository to avoid merge conflicts:

```bash
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

## Common Contribution Scenarios

### Scenario 1: Reporting a Bug

1. Search for existing issues to avoid duplicates
2. Create a new issue with:
   - Clear title (e.g., "Measurement validation fails for negative values")
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, FairDM version)
3. Wait for maintainer triage before starting a fix (to avoid duplicate work)

### Scenario 2: Proposing a New Feature

1. Open a **Discussion** (not an issue) to propose the feature
2. Explain the use case and how it aligns with the constitution
3. Gather feedback from maintainers and community
4. If approved, create an issue to track implementation
5. Follow the standard contribution workflow

### Scenario 3: Improving Documentation

1. Identify what's unclear or missing
2. Create an issue or go straight to a PR (for small changes)
3. Make changes to Markdown files in `docs/`
4. Run `sphinx-build` to verify the docs build correctly
5. Submit a PR with clear explanation of what improved

## Resources

- **[FairDM Constitution](https://github.com/FAIR-DM/fairdm/blob/main/.specify/memory/constitution.md)**: Core principles and design constraints
- **[Code of Conduct](https://github.com/FAIR-DM/fairdm/blob/main/CODE_OF_CONDUCT.md)**: Community standards
- **[Quality Gates Guide](django_dev.md)**: Tests, type checking, linting, docs
- **[Frontend Development Guide](frontend_dev.md)**: Templates, CSS, JavaScript
- **[Issue Tracker](https://github.com/FAIR-DM/fairdm/issues)**: Report bugs and request features
- **[Discussions](https://github.com/FAIR-DM/fairdm/discussions)**: Ask questions and propose ideas

## Getting Help

If you're stuck or have questions:

- **Check the documentation**: Many common questions are answered in the guides
- **Search existing issues and discussions**: Your question may already be answered
- **Open a discussion**: Ask in [GitHub Discussions](https://github.com/FAIR-DM/fairdm/discussions)
- **Join the community**: Connect with other contributors (link to Slack/Discord if available)

Thank you for contributing to FairDM! Your efforts help make research data more FAIR and accessible. 🚀
