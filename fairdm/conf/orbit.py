"""Access control for the Django Orbit observability dashboard.

Orbit records requests, queries and exceptions, and its dashboard defaults to
open access when ``DEBUG`` is ``False``. :func:`dashboard_access` is wired up as
``ORBIT_CONFIG["AUTH_CHECK"]`` so the dashboard stays protected in production.
"""

from django.conf import settings


def dashboard_access(request):
    """Return whether ``request`` may view the Orbit dashboard (``/orbit/``).

    In development (``DEBUG=True``) the dashboard is open for convenience. In
    production it is restricted to authenticated superusers. Override
    ``ORBIT_CONFIG["AUTH_CHECK"]`` in your own project to change this policy.
    """
    if settings.DEBUG:
        return True
    user = getattr(request, "user", None)
    return bool(user and user.is_authenticated and user.is_superuser)
