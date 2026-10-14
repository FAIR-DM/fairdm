# Before You Begin

```{admonition} You are here
:class: tip
**Developer Guide** → Before You Begin

This page covers the prerequisites and tools for developing FairDM portals. If you landed here from a search, you may want to start with the [Developer Guide overview](index.md) to understand the developer role.
```

Before diving in, it’s helpful to be comfortable with the following tools and concepts:

## Assumed knowledge

FairDM is built on top of Python and the Django web framework, so a basic understanding of these technologies is extremely helpful. While you don’t need to be an expert, familiarity with the following concepts will make your experience smoother:

    - Python programming (especially object-oriented programming)
    - Package management (preferrably using the `Poetry` package)
    - Git version control (basic commands like `clone`, `commit`, `push`, `pull`)
    - Docker (what is it and what problems does it solve?)

```{note}
We highly suggest that you complete the [Django tutorial](https://docs.djangoproject.com/en/stable/intro/tutorial01/) if you are new to Django. It will provide a solid foundation for working within the FairDM framework.
```

```{seealso}
**Ready to get hands-on?** Once you have the prerequisites installed, head to the [Getting Started guide](getting_started.md) for a complete walkthrough of running the demo portal and creating your first custom models.
```

## Tools & Technologies

To get started, make sure the following tools are installed on your system.

### 🐍 Python 3.10 or newer

You’ll also need to install the following globally:

- **Poetry** – for dependency management and virtual environments
- **Cookiecutter** – for scaffolding a new project from the template

Install with `pip`:

```bash
    pip install poetry cookiecutter
```

### 🔧 Git

If Git isn’t already installed, search online for "install Git" followed by your operating system (e.g., "install Git on macOS" or "install Git on Windows").

> 💡 Tip: Configure your Git user info with `git config --global user.name "Your Name"` and `git config --global user.email "you@example.com"`.

## Recommended tools

### 🧑‍💻 Visual Studio Code (VS Code)

We highly recommend [Visual Studio Code](https://code.visualstudio.com/) as your IDE of choice. It provides:

- Excellent Python support
- Integrated terminal and Git support
- A rich ecosystem of extensions
- Intuitive UI for managing containers and databases

> ✅ The FairDM project template includes a pre-configured VS Code workspace (`.code-workspace`) that automatically sets up recommended extensions and settings, so you can get started faster.


### 🐳 Docker

A FairDM portal runs on PostgreSQL with the PostGIS extension, in development as well as in production, and Django needs the GDAL, GEOS and PROJ libraries to use it. Docker is the simplest way to have both: the official `postgis/postgis` image gives you the database, and an image with GDAL installed gives you the libraries without installing anything on your own machine. That matters most on Windows, where GDAL is hard to install natively. Docker is also how you test your deployment settings before pushing them to a server.

Visit the official site to install it for your platform: https://www.docker.com/products/docker-desktop