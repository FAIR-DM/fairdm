from django.urls import path

from .views import GenericContactForm, ReferenceListView, follow_unfollow

urlpatterns = [
    path("activity/follow-object/<str:uuid>", follow_unfollow, name="follow-object"),
    path("generic-contact/", GenericContactForm.as_view(), name="contact"),
    path("references/", ReferenceListView.as_view(), name="reference-list"),
]
