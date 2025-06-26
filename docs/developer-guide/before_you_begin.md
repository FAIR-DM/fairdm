# Before you begin

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

Docker is not required to test and develop your FairDM on your local machine. However, when the time comes to deploy your portal to a production setting, it is handy to have Docker installed locally in order to test your deployment settings before pushing it to the cloud.

Visit the official site to install it for your platform: https://www.docker.com/products/docker-desktop