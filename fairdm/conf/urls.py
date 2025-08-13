from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog

from fairdm.core.utils import UUID_RE_PATTERN
from fairdm.utils.views import DirectoryView, HomeView
from .setup import addon_urls

urlpatterns = [
    path("", include("fairdm.contrib.admin.urls")),
    path(r"jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    path("django-literature/", include("literature.urls")),
    path("", HomeView.as_view(), name="home"),
    path("data/", TemplateView.as_view(template_name="fairdm/data.html"), name="data"),
    path("", include("fairdm.core.urls")),
    path("", include("fairdm.contrib.contributors.urls")),
    path("", include("fairdm.contrib.import_export.urls")),
    path("", include("fairdm.contrib.location.urls")),
    path("", include("fairdm.utils.urls")),
    path("api/", include("fairdm.contrib.api.urls")),
    path("", include("dac.addons.urls")),
    path("account-center/", include("dac.urls")),
    path("invitations/", include("invitations.urls", namespace="invitations")),
    path("contact/", include("django_contact_form.urls")),
    path("select2/", include("django_select2.urls")),
    path("activity/", include("actstream.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("martor/", include("martor.urls")),
]

if addon_urls:
    urlpatterns += [
        path("", include(*addon_urls)),
    ]

urlpatterns += [
    re_path(UUID_RE_PATTERN, DirectoryView.as_view(), name="directory"),
]

# adds the debug toolbar to templates if installed
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

    if "debug_toolbar" in settings.INSTALLED_APPS:
        from debug_toolbar.toolbar import debug_toolbar_urls

        urlpatterns += debug_toolbar_urls()


# urlpatterns += [path("", include("cms.urls"))]  # must be last
