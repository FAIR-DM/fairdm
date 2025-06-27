"""A collection of views for managing user accounts and profiles."""

from braces.views import FormMessagesMixin
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import UpdateView
from extra_views import InlineFormSetView
from meta.views import MetadataMixin

from ..forms.forms import UserIdentifierForm
from ..forms.person import UserProfileForm
from ..models import ContributorIdentifier

helper = FormHelper()
helper.add_input(Submit("submit", "Save"))
helper.render_required_fields = True
helper.template = "bootstrap5/table_inline_formset.html"


class Base(MetadataMixin, LoginRequiredMixin, UpdateView):
    template_name = "user/settings/base.html"
    model = get_user_model()

    def get_object(self):
        return self.request.user


class UpdateProfile(FormMessagesMixin, Base):
    title = _("Edit Profile")
    description = _("The following information is publicly available to all visitors of this portal.")
    form_class = UserProfileForm
    form_invalid_message = _(
        "There was an error updating your profile. Please check the form for errors and try again."
    )
    form_valid_message = _("Your profile has been updated successfully.")

    def get_success_url(self):
        return self.request.META.get("HTTP_REFERER", reverse_lazy("account-management"))  # Fallback to a default URL

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sections"] = {
            # holds the account center menu
            "sidebar_primary": {
                "is": "dac.sidebar",
                "breakpoint": "md",
                "class": "border-end",
                "header": {
                    "title": _("Account Center"),
                },
            },
        }
        return context


class UpdateAffiliations(Base):
    template_name = "user/settings/profile_identifiers.html"
    title = _("Affiliations")
    form_class = UserProfileForm


class UpdateIdentifiers(MetadataMixin, InlineFormSetView):
    title = _("Persistent Identifiers")
    model = get_user_model()
    inline_model = ContributorIdentifier
    form_class = UserIdentifierForm
    template_name = "user/settings/base.html"
    success_url = reverse_lazy("contributor-identifiers")
    factory_kwargs = {"extra": 1, "max_num": None, "can_order": False, "can_delete": True}

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        helper = FormHelper()
        helper.add_input(Submit("submit", "Save"))
        helper.render_required_fields = True
        helper.template = "bootstrap5/table_inline_formset.html"
        context["helper"] = helper
        return context
