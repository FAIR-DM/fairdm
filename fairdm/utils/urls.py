from django.urls import path

from .views import GenericContactForm, ReferenceListView

urlpatterns = [
    path("generic-contact/", GenericContactForm.as_view(), name="contact"),
    path("references/", ReferenceListView.as_view(), name="reference-list"),
]
