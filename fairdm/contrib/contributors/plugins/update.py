"""The page where a contributor's profile is edited."""

from django.conf import settings
from django.urls import reverse
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from fairdm.contrib.plugins import Plugin
from fairdm.views import FairDMUpdateView

from ..forms.profile import PersonProfileForm
from ..models import Contributor


def contributor_is_editable(request, contributor):
    """Say whether the request's user may open the editing page for a contributor.

    An additional view is governed by its own ``check``, not its owner's, so the overview's
    rule for who may look at a profile does not apply here. ``Plugin`` asks on every request,
    so a right lost while the page is open refuses the save.

    Args:
        request: The current request.
        contributor: The contributor, or None when no record has been resolved.

    Returns:
        True when the contributor's ``is_editable_by`` accepts the user.
    """
    return contributor is not None and contributor.is_editable_by(request.user)


class Update(Plugin, FairDMUpdateView):
    """Edit a contributor's profile.

    An additional view of the overview plugin, so the navigation strip carries one entry for the
    whole collection. Which form it shows is read from ``FAIRDM_PROFILE_FORMS`` for the kind of
    contributor, and falls back to the form the package ships.

    Attributes:
        shipped_forms: The form each kind of contributor is edited with when the setting names
            none.
    """

    url_path = "update"
    model = Contributor
    check = staticmethod(contributor_is_editable)
    page_title = _("Edit profile")
    success_message = _("Your changes were saved.")
    template_name = "contributors/plugins/update.html"
    shipped_forms = {"person": PersonProfileForm}

    def get_form_class(self):
        """Use the portal's form for this kind of contributor, else the shipped one."""
        kind = "organization" if self.base_object.is_organization else "person"
        path = getattr(settings, "FAIRDM_PROFILE_FORMS", {}).get(kind)
        return import_string(path) if path else self.shipped_forms[kind]

    def get_page_title(self):
        """Title the page as it is declared, with no model name interpolated."""
        return self.page_title

    def get_success_url(self):
        """Return to the contributor's own page."""
        return self.base_object.get_absolute_url()

    def get_context_data(self, **kwargs):
        """Add where Cancel leads and the account centre's address."""
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.base_object.get_absolute_url()
        context["account_centre_url"] = reverse("account-center")
        context["is_own_profile"] = self.request.user.pk == self.base_object.pk
        return context
