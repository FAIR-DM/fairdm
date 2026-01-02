from django.urls import include, path

from .views import follow_unfollow

urlpatterns = [
    # Include django-activity-stream's built-in URLs
    path("", include("actstream.urls")),
    path("activity/follow-object/<str:uuid>", follow_unfollow, name="follow-object"),
]
