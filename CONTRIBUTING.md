# Contributing to FairDM

Thank you for contributing to FairDM! This guide will help you set up your development environment and ensure your contributions pass CI checks.

## Development Setup

### 1. Install Dependencies

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install --with dev,test,docs
```

### 2. Install Git Hooks (IMPORTANT!)

**This prevents CI failures by running the same checks locally before you push:**

```bash
poetry run invoke install-hooks
```

This configures git to run pre-push validation automatically. It will:
- Run Ruff linting and formatting checks
- Show you exactly what needs to be fixed
- Prevent pushing code that will fail CI

## Development Workflow

### Before You Commit

Git will automatically run basic checks on commit (trailing whitespace, etc.). If you want to run all checks manually:

```bash
# Auto-fix all formatting issues
poetry run invoke format

# Or manually run pre-commit
poetry run pre-commit run --all-files
```

### Before You Push (CRITICAL!)

**Option 1: Automatic (RECOMMENDED)**
If you installed git hooks, checks run automatically when you push.

**Option 2: Manual**
Run checks manually before pushing:

```bash
poetry run invoke pre-push
```

This runs **exactly the same checks as CI**, preventing failures.

### Common Tasks

| Task | Command | Description |
|------|---------|-------------|
| **Format code** | `poetry run invoke format` | Auto-fix formatting and linting issues |
| **Run tests** | `poetry run invoke test` | Run test suite with coverage |
| **Pre-push checks** | `poetry run invoke pre-push` | Run all CI checks locally |
| **Install hooks** | `poetry run invoke install-hooks` | Set up automatic pre-push validation |
| **Django checks** | `poetry run python manage.py check` | Run Django system checks |

## Understanding CI Failures

If CI fails with **Lint & Format** errors:

1. **Pull latest changes** (in case files were reformatted):
   ```bash
   git pull origin your-branch
   ```

2. **Run format to auto-fix**:
   ```bash
   poetry run invoke format
   ```

3. **Check for remaining issues**:
   ```bash
   poetry run invoke pre-push
   ```

4. **Commit and push fixes**:
   ```bash
   git add .
   git commit -m "style: fix linting issues"
   git push
   ```

## Code Quality Standards

### Linting & Formatting

We use **Ruff** for both linting and formatting:
- Max line length: **120 characters**
- Python version: **3.13+**
- Style guide: Based on Black with custom rules

### Type Checking

MyPy is configured but currently disabled in CI. When enabled:
- Use type hints for function signatures
- Follow `django-stubs` patterns for Django code
- Check `pyproject.toml` for mypy configuration

### Testing

- Write tests for all new features
- Aim for >80% coverage
- Use pytest with Django plugin
- Follow existing test patterns in `tests/`

## Pre-commit Hooks

The project uses `.pre-commit-config.yaml` for code quality:

| Hook | Purpose |
|------|---------|
| `trailing-whitespace` | Remove trailing whitespace |
| `end-of-file-fixer` | Ensure files end with newline |
| `pyupgrade` | Upgrade Python syntax to 3.13+ |
| `ruff` | Fast Python linter (replaces flake8, isort, etc.) |
| `ruff-format` | Fast Python formatter (replaces black) |

## Troubleshooting

### "Pre-commit checks failed"

Run to see all issues:
```bash
poetry run pre-commit run --all-files
```

Auto-fix most issues:
```bash
poetry run invoke format
```

### "Line too long" errors

Ruff enforces 120-character lines. Break long lines:
```python
# Bad (>120 chars)
result = some_very_long_function_name(argument1, argument2, argument3, argument4, argument5, argument6)

# Good
result = some_very_long_function_name(
    argument1, argument2, argument3,
    argument4, argument5, argument6
)
```

### "Import not sorted correctly"

Ruff handles import sorting automatically:
```bash
poetry run invoke format
```

### Git hooks not working

Reinstall hooks:
```bash
poetry run invoke install-hooks
```

## Questions?

- Check existing issues: https://github.com/FAIR-DM/fairdm/issues
- Read the docs: https://fairdm.readthedocs.io/
- Ask in discussions: https://github.com/FAIR-DM/fairdm/discussions
