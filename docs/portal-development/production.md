# Web-based deployment

## Understanding the production.yml file

This file contains all services necessary to run the application in a single server production environment. It
includes the following services:

- Django application:
  - The main application that serves the web pages and API endpoints. It is built from the Dockerfile located
        at ./compose/production/django.
- PostgreSQL database:
  - The database that stores all the data for the application.
- Redis:
  - The in-memory data structure store that is used as both a message broker for Celery workers and a cache for
        the Django application.
- Celery workers:
  - The background workers that process asynchronous tasks such as sending emails, processing uploaded files, and
        other long-running tasks.
- Celery beat:
  - The scheduler that sends tasks to the Celery workers at specified intervals.
- Flower:
  - The web-based monitoring tool for Celery workers and tasks. It is available at tasks.${DJANGO_DOMAIN}.
- Minio:
  - The object storage server that is used to store media files such as images and documents. It is available at
        media.${DJANGO_DOMAIN}. The dashboard is available at minio.${DJANGO_DOMAIN}.
  - NOTE: this service can be commented or deleted if you are using an external S3 based service such as AWS S3.
- Traefik:
  - The reverse proxy and load balancer that routes incoming requests to the appropriate services. It also
        automatically requests and renews SSL certificates from Let's Encrypt.

## Pre-Deployment Validation

Before deploying to production, validate your configuration using Django's check framework:

```bash
python manage.py check --deploy
```

This command validates production-readiness for:

- Database configuration (PostgreSQL required)
- Cache backend (Redis/Memcached required)
- SECRET_KEY security
- ALLOWED_HOSTS configuration
- DEBUG mode (must be False)
- SSL/HTTPS settings
- Cookie security
- Celery configuration

**Exit codes:**

- `0`: All checks passed, safe to deploy
- `1`: Errors found, do not deploy

For detailed information on all checks and how to fix issues, see [Configuration Checks](../portal-administration/configuration-checks.md).

```{seealso}
Include `python manage.py check --deploy` in your CI/CD pipeline to catch configuration issues before deployment.
```

## Deployment configuration

### What are environment variables?

### Where can I declare environment variables?

From highest to lowest precedence:

- production.yml (not recommended)
- stack.env (or Portainer environment variables)
- deploy/config/*.env
- system environment variables

### Which environment variables take precedence?

<!-- ```{literalinclude} ../../../pyproject.toml
   :language: toml
   :linenos:

``` -->
