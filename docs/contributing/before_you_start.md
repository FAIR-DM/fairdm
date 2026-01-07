# Before You Start

This guide is for experienced Django developers who wish to contribute to the development of the core FairDM framework. If you are looking for information on how to develop a FairDM-powered web application for your research community, please see the [Developer Guide](../portal-development/index.md).

## Prerequisites

Before contributing to FairDM, you should have:

### Required Knowledge

- **Python**: Proficient in Python 3.10+ with strong understanding of object-oriented programming
- **Django**: Experience building Django applications; familiarity with models, views, templates, forms, and the Django ORM
- **Git**: Comfortable with Git workflows (branching, committing, merging, rebasing)
- **Testing**: Understanding of unit testing and test-driven development (pytest)

### Recommended Knowledge

- **Type hints**: Experience with Python type annotations and mypy
- **PostgreSQL**: Basic understanding of relational databases
- **Docker**: Familiarity with containerization for development environments
- **Bootstrap 5**: Knowledge of Bootstrap components and grid system
- **HTMX/Alpine.js**: Understanding of progressive enhancement patterns (helpful but not required)

### Required Tools

Before setting up the development environment, ensure you have the following installed on your system:

1. **Python 3.10 or higher**
   - Check version: `python --version` or `python3 --version`
   - Download from [python.org](https://www.python.org/downloads/)

2. **Poetry** (dependency manager)
   - Install: [https://python-poetry.org/docs/#installation](https://python-poetry.org/docs/#installation)
   - Check version: `poetry --version`

3. **Git**
   - Check version: `git --version`
   - Download from [git-scm.com](https://git-scm.com/)

4. **PostgreSQL** (for production-like development)
   - Check version: `psql --version`
   - Download from [postgresql.org](https://www.postgresql.org/download/)
   - **Alternative**: Use Docker to run PostgreSQL in a container

5. **Docker** (optional but recommended)
   - Useful for running services (PostgreSQL, Redis) without local installation
   - Download from [docker.com](https://www.docker.com/products/docker-desktop/)

6. **A code editor**
   - **Recommended**: [Visual Studio Code](https://code.visualstudio.com/) with Python and Django extensions
   - Alternatives: PyCharm, Sublime Text, etc.

```{tip}
**New to Django?** If you're not yet comfortable with Django basics, we recommend completing the [official Django tutorial](https://docs.djangoproject.com/en/stable/intro/tutorial01/) before contributing to FairDM.
```

## Setting Up Your Development Environment

Follow these steps to set up a local FairDM development environment:

### 1. Fork and Clone the Repository

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

### 2. Install Dependencies with Poetry

1. **Install Python dependencies**:

   ```bash
   poetry install
   ```

   This creates a virtual environment and installs all project dependencies including development tools (pytest, mypy, ruff, etc.).

2. **Activate the Poetry shell** (optional but recommended):

   ```bash
   poetry shell
   ```

   All subsequent commands in this guide assume you're in the Poetry shell. If you don't activate the shell, prefix commands with `poetry run` (e.g., `poetry run pytest`).

### 3. Set Up the Database

FairDM uses PostgreSQL in production, but SQLite is fine for local development.

#### Option A: Use SQLite (Quick Start)

SQLite requires no setup. Django will create `db.sqlite3` automatically when you run migrations.

#### Option B: Use PostgreSQL (Recommended for Production-Like Testing)

1. **Start PostgreSQL** (locally or via Docker):

   ```bash
   # Using Docker
   docker run --name fairdm-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=fairdm -p 5432:5432 -d postgres:15
   ```

2. **Configure database connection**:

   Create a `.env` file in the project root:

   ```env
   DATABASE_URL=postgres://postgres:postgres@localhost:5432/fairdm
   ```

### 4. Run Database Migrations

Apply all database migrations to set up the schema:

```bash
poetry run python manage.py migrate
```

### 5. Create a Superuser (Optional)

To access the Django admin interface:

```bash
poetry run python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 6. Run the Development Server

Start the Django development server:

```bash
poetry run python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000) in your browser. You should see the FairDM homepage.

```{tip}
**Admin interface**: Access the admin at [http://localhost:8000/admin](http://localhost:8000/admin) using the superuser credentials you created.
```

### 7. Verify the Setup

Run the test suite to ensure everything is working:

```bash
poetry run pytest
```

All tests should pass. If any fail, check your environment setup.

## Next Steps

Now that your environment is set up, you can:

- **[Learn about quality gates](django_dev.md)**: Understand tests, type checking, linting, and documentation builds
- **[Read the contribution workflow](getting_started.md)**: Learn how to propose changes, create pull requests, and align with the FairDM constitution

```{seealso}
**Constitution**: Before making changes, read the [FairDM Constitution](https://github.com/FAIR-DM/fairdm/blob/main/.specify/memory/constitution.md) to understand the framework's goals and constraints.
```
