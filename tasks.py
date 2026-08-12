from invoke import task


@task
def check(c):
    """
    Run all quality checks (same as CI) - use this before pushing!
    """
    print("🚀 Running pre-commit checks (linting & formatting)")
    c.run("poetry run pre-commit run --all-files --show-diff-on-failure")

    # Mypy is currently disabled in CI - uncomment when re-enabled
    # print("🚀 Static type checking: Running mypy")
    # c.run("poetry run mypy")


@task
def format(c):  # noqa: A001 — the task name is the `invoke format` CLI contract
    """
    Auto-fix all formatting issues (runs ruff format + ruff --fix)
    """
    print("🚀 Auto-fixing formatting and linting issues")
    c.run("poetry run ruff format .")
    c.run("poetry run ruff check --fix .")


@task(name="pre-push")
def pre_push(c):
    """
    Run pre-push checks (same as CI) - prevents CI failures
    """
    print("🔍 Running pre-push validation...\n")
    check(c)
    print("\n✅ All checks passed! Safe to push.")


@task
def install_hooks(c):
    """
    Install git hooks for automatic pre-push validation
    """
    print("📌 Installing git hooks...")
    c.run("git config core.hooksPath .githooks")
    print("✅ Git hooks installed!")
    print("   Pre-push checks will now run automatically before every push.")


@task
def test(c):
    """
    Run the test suite
    """
    print("🚀 Testing code: Running pytest")
    c.run("poetry run pytest --cov --cov-config=pyproject.toml --cov-report=html")
