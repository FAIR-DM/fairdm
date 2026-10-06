"""Root URL configuration for a FairDM portal."""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views import defaults as default_views
from django.views.i18n import JavaScriptCatalog
from markdownx.views import MarkdownifyView
from mvp.views.account import AccountCenterView

from fairdm.views.generic import FairDMHomeView

from .setup import addon_urls

urlpatterns = [
    path("", include("fairdm.contrib.admin.urls")),
    path(r"jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    path("django-literature/", include("literature.urls")),
    path("", FairDMHomeView.as_view(), name="home"),
    path("", include("fairdm.core.urls")),
    path("", include("fairdm.contrib.collections.urls")),
    path("", include("fairdm.contrib.contributors.urls")),
    path("", include("fairdm.contrib.import_export.urls")),
    path("", include("fairdm.contrib.location.urls")),
    path("api/", include(("fairdm.api.urls", "api"), namespace="api")),
    path("account-center/", include("mvp.urls")),
    path("account-center/", include("allauth.urls")),
    # django-mvp mounts its landing page at ``account/`` inside ``mvp.urls``. Django reverses a
    # name to the last pattern that carries it, so this route, which keeps FairDM's address for
    # the same view, has to come after the include.
    path("account-center/", AccountCenterView.as_view(), name="account-center"),
    path("contact/", include("django_contact_form.urls")),
    path("select2/", include("django_select2.urls")),
    path("autocomplete/", include("fairdm.contrib.autocomplete.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    # Preview only: django-markdownx also ships an unauthenticated image upload view.
    path(
        "markdownx/markdownify/",
        MarkdownifyView.as_view(),
        name="markdownx_markdownify",
    ),
    path("hijack/", include("hijack.urls")),
    path("orbit/", include("orbit.urls")),
]

if addon_urls:
    for addon_url in addon_urls:
        urlpatterns += [
            path("", include(addon_url)),
        ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path(
            "500/",
            default_views.server_error,
        ),
    ]

    if "django_browser_reload" in settings.INSTALLED_APPS:
        urlpatterns += [
            path("__reload__/", include("django_browser_reload.urls")),
        ]
