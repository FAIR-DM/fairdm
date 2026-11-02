"""URLs of routed_addon."""

from django.http import HttpResponse
from django.urls import path


def addon_page(request):
    return HttpResponse()


urlpatterns = [path("routed-addon/", addon_page, name="routed-addon-page")]
