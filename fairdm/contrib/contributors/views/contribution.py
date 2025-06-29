"""Views that handle adding and editing contribution objects."""

from braces.views import MessageMixin
from django import forms
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.views.generic.edit import FormView

from fairdm import plugins
from fairdm.plugins import reverse
from fairdm.utils.view_mixins import RelatedObjectMixin
from fairdm.views import FairDMCreateView, FairDMDeleteView, FairDMUpdateView

from .. import utils
from ..forms.contribution import AddExistingPersonForm, QuickAddContributionForm, UpdateContributionForm
from ..forms.forms import RemoteContributionForm
from ..models import Contribution


class BaseContributionView(MessageMixin, RelatedObjectMixin):
    title = _("Add Contributor")

    def get_help_text(self):
        help_text = f"You are adding a contributor to {self.base_object}. "
        return help_text

    def get_success_url(self) -> str:
        return reverse(self.base_object, "contributors")


class ContributorQuickAddView(BaseContributionView, FormView):
    """View to quickly add a contribution to a project, dataset, sample, or measurement.

    This view is used for quick addition of contributions without the need for a full form submission.
    It is typically used with htmx requests from the Contribution Plugin on detail pages.

    Returns:
        HttpResponse: A rendered partial HTML template.

    """

    form_class = QuickAddContributionForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # kwargs["base_object"] = self.base_object
        return kwargs

    def form_valid(self, form):
        data = form.cleaned_data
        contributors = data.get("contributors", [])

        for contributor in contributors:
            # self.base_object.add_contributor(contributor, with_roles=data.get("roles", []))
            utils.update_or_create_contribution(contributor, self.base_object, roles=data.get("roles", []))

        self.messages.info("Successfully added contributors to the project.")
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        self.messages.error("There was an error adding contributors. Please try again.")
        return HttpResponseRedirect(self.get_success_url())


class ContributionCreateView(BaseContributionView, FairDMCreateView):
    """Adds a new Contribution to a Project, Dataset, Sample or Measurement. Used with htmx requests predominantly from
    the Contribution Plugin on detail pages.

    Returns:
        HttpResponse: A rendered partial HTML template.

    """

    form_class = AddExistingPersonForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["base_object"] = self.base_object
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["base_object"] = self.base_object
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        contribution, created = utils.update_or_create_contribution(
            data.get("contributor"), self.base_object, roles=data.get("roles", [])
        )
        if created:
            self.messages.info("Succesfully added new contributor to the project.")

        affiliation, created = utils.update_or_create_contribution(
            data.get("affiliation"), self.base_object, roles=["ProjectMember"]
        )
        if created:
            self.messages.info("Succesfully added new affiliation to the project.")

        return HttpResponseRedirect(self.get_success_url())

        # return render(self.request, "contributors/contribution.html", {"contributor": contribution})

    def get_success_url(self):
        """Redirect to the detail page of the base object."""
        return self.base_object.get_absolute_url()


class AddContributorFromOrcidView(BaseContributionView, FairDMCreateView):
    """View to add a contributor from an ORCID identifier."""

    form_class = RemoteContributionForm
    form_component = "contributor.forms.existing-contributor"

    def form_valid(self, form):
        data = form.cleaned_data["data"]
        orcid = data.get("orcid-identifier", {}).get("path")
        contributor, contributor_created = utils.get_or_create_from_orcid(orcid)
        contribution, created = utils.update_or_create_contribution(contributor, self.base_object)
        return HttpResponseRedirect(self.get_success_url())

    def get_info_block(self):
        """Return an info block for the view."""
        return {
            "title": _("Add Contributor from ORCID"),
            "description": _(
                "You can add a contributor by providing their ORCID identifier. "
                "This will automatically fetch their details and create a contribution."
            ),
            "icon": static("fairdm/contrib/contributors/images/orcid.svg"),
        }


class ContributionUpdateView(plugins.BasePlugin, FairDMUpdateView):
    model = Contribution
    form_class = UpdateContributionForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["base_object"] = self.base_object
        return kwargs

    def get_page_title(self):
        """Return the title for the view."""
        return str(self.object.contributor)

    def get_help_text(self):
        help_text = f"<p>You are currently editing the role of this contributor within the context of:<p><p class='fw-semibold'>{self.base_object}.</p>"
        return mark_safe(help_text)


class ContributionRemoveView(BaseContributionView, FairDMDeleteView):
    model = Contribution
    form_class = forms.Form
    title = _("Remove Contributor")

    def get_help_text(self):
        contribution = self.object.contributor.first_name
        text = _(
            "Are you sure you want to remove this contributor? They will no longer have access if visibility is set to private. Do you want to continue?"
        )
        return mark_safe(f"<p>{contribution}</p><p>{text}</p>")
