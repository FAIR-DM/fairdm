from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views import defaults as default_views
from django.views.i18n import JavaScriptCatalog
from markdownx.views import MarkdownifyView

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
    # path("", include("dac.allauth")),
    path("account-center/", include("dac.urls")),
    path("contact/", include("django_contact_form.urls")),
    path("select2/", include("django_select2.urls")),
    path("autocomplete/", include("fairdm.contrib.autocomplete.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    # Only the preview endpoint is exposed. django-markdownx also ships an
    # image upload view, which writes to media storage with no authentication
    # check of any kind; the editor here has no image upload, so that route is
    # deliberately left out rather than included and then guarded.
    path(
        "markdownx/markdownify/",
        MarkdownifyView.as_view(),
        name="markdownx_markdownify",
    ),
    path("hijack/", include("hijack.urls")),
    path("orbit/", include("orbit.urls")),
    # REST API — Feature 011 (namespaced to prevent URL name collision with portal UI routes)
]

if addon_urls:
    for addon_url in addon_urls:
        urlpatterns += [
            path("", include(addon_url)),
        ]

# serve media and static files directly during development
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


# urlpatterns += [path("", include("cms.urls"))]  # must be last
