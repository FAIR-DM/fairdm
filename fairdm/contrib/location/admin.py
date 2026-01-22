from django.contrib import admin

from .models import Point


@admin.register(Point)
class PointAdmin(admin.ModelAdmin):
    list_display = ["x", "y", "crs"]
    search_fields = ["x", "y", "crs"]  # Required for autocomplete_fields
