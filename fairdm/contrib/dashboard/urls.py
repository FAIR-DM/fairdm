"""Addresses of the pages the dashboard links out to."""

from django.urls import path

from fairdm.contrib.dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("dashboard/getting-started/", views.HideGettingStartedView.as_view(), name="hide-getting-started"),
    path("dashboard/publication/", views.PublicationQueueView.as_view(), name="publication-queue"),
    path("community/activity/", views.CommunityActivityView.as_view(), name="community-activity"),
]
