"""Admin for locations."""

from django.contrib import admin

from .models import Point


@admin.register(Point)
class PointAdmin(admin.ModelAdmin):
    """Admin for locations, searchable so other admins can autocomplete them."""

    list_display = ["x", "y", "crs"]
    search_fields = ["x", "y", "crs"]
