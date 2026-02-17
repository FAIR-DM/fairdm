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
def format(c):
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
def test(c, tox=False):
    """
    Run the test suite
    """
    print("🚀 Testing code: Running pytest")
    c.run("poetry run pytest --cov --cov-config=pyproject.toml --cov-report=html")
    # if tox:
    #     print("🚀 Testing code: Running pytest with all tests")
    #     c.run("tox")
    # else:
    #     print("🚀 Testing code: Running pytest")
    #     c.run("poetry run pytest --cov --cov-config=pyproject.toml --cov-report=html")


@task
def bump(c, rule="patch"):
    """
    Create a new git tag and push it to the remote repository.

    .. note::
        Specifying either "minor" or "release" as the rule will create a new tag and push it to the remote repository, triggering a new release to PyPI.

    RULE	    BEFORE	AFTER
    major	    1.3.0	2.0.0
    minor	    2.1.4	2.2.0
    patch	    4.1.1	4.1.2
    premajor	1.0.2	2.0.0a0
    preminor	1.0.2	1.1.0a0
    prepatch	1.0.2	1.0.3a0
    prerelease	1.0.2	1.0.3a0
    prerelease	1.0.3a0	1.0.3a1
    prerelease	1.0.3b0	1.0.3b1

    """
    # 1. Bump and commit the version
    vnum = c.run(f"poetry version {rule} -s", hide=True).stdout.strip()
    c.run(f'git commit pyproject.toml -m "bump version v{vnum}"')

    if rule in ["major", "minor"]:
        # 3. create a tag and push it to the remote repository
        c.run(f'git tag -a v{vnum} -m "{vnum}"')
        c.run("git push --tags")
