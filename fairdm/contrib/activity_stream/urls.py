from django.urls import include, path

app_name = "activity_stream"

urlpatterns = [
    # Include django-activity-stream's built-in URLs
    path("", include("actstream.urls")),
]
