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

2. **uv** (dependency manager)
   - Install: [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)
   - Check version: `uv --version`

3. **Git**
   - Check version: `git --version`
   - Download from [git-scm.com](https://git-scm.com/)

4. **Docker**
   - FairDM runs on PostgreSQL with the PostGIS extension, and `docker-compose.yml` starts one
     for you, along with Redis
   - Download from [docker.com](https://www.docker.com/products/docker-desktop/)

5. **GDAL, GEOS and PROJ**, only if you run Django on your own machine rather than in Docker
   - GeoDjango loads these system libraries. The development image already has them
   - Debian and Ubuntu: `sudo apt install gdal-bin`. macOS: `brew install gdal`
   - On Windows, run Django in Docker instead
   - If Django cannot find them, set `GDAL_LIBRARY_PATH` and `GEOS_LIBRARY_PATH` to the full
     paths of the libraries

6. **A code editor**
   - **Recommended**: [Visual Studio Code](https://code.visualstudio.com/) with Python and Django extensions
   - Alternatives: PyCharm, Sublime Text, etc.

```{tip}
**New to Django?** If you're not yet comfortable with Django basics, we recommend completing the [official Django tutorial](https://docs.djangoproject.com/en/stable/intro/tutorial01/) before contributing to FairDM.
```

## Setting Up Your Development Environment

```{tip}
**The quickest start is Docker.** After cloning, `docker compose up` builds the development
image and starts PostGIS, Redis, a Celery worker and the development server on
<http://localhost:8000>, with your checkout mounted so edits reload. It needs nothing installed
but Docker, on Windows the same as anywhere else. The rest of this page describes running Django
on your own machine against the same databases.
```

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

### 2. Install Dependencies with uv

1. **Install Python dependencies**:

   ```bash
   uv sync
   ```

   This creates a virtual environment and installs all project dependencies including development tools (pytest, mypy, ruff, etc.).

2. **Activate the virtual environment** (optional but recommended):

   ```bash
   source .venv/bin/activate
   ```

   All subsequent commands in this guide assume you have activated the virtual environment. If you don't activate it, prefix commands with `uv run` (e.g., `uv run pytest`).

### 3. Start the Database

FairDM needs PostgreSQL with the PostGIS extension, in development as in production. SQLite has no
spatial support and is not an option. Start PostGIS and Redis from `docker-compose.yml`:

```bash
docker compose up postgres redis
```

`stack.development.env` already points a development portal at them, on `localhost:5432` and
`localhost:6379`. To use a PostGIS server of your own instead, set `DATABASE_URL` or the
`POSTGRES_*` variables in your environment, which take precedence over the file.

### 4. Run Database Migrations

Apply all database migrations to set up the schema:

```bash
uv run python manage.py migrate
```

### 5. Create a Superuser (Optional)

To access the Django admin interface:

```bash
uv run python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 6. Run the Development Server

Start the Django development server:

```bash
uv run python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000) in your browser. You should see the FairDM homepage.

```{tip}
**Admin interface**: Access the admin at [http://localhost:8000/admin](http://localhost:8000/admin) using the superuser credentials you created.
```

### 7. Verify the Setup

Run the test suite to ensure everything is working:

```bash
uv run pytest
```

All tests should pass. If any fail, check your environment setup.

## Next Steps

Now that your environment is set up, you can:

- **[Learn about quality gates](django_dev.md)**: Understand tests, type checking, linting, and documentation builds
- **[Read the contribution workflow](getting_started.md)**: Learn how to propose changes, create pull requests, and align with the FairDM constitution

```{seealso}
**Constitution**: Before making changes, read the [FairDM Constitution](https://github.com/FAIR-DM/fairdm/blob/main/CONSTITUTION.md) to understand the framework's goals and constraints.
```
