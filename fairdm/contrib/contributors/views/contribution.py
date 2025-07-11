"""Views that handle adding and editing contribution objects."""

from braces.views import MessageMixin
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.views.generic.edit import FormView

from fairdm import plugins
from fairdm.plugins import reverse
from fairdm.utils.view_mixins import RelatedObjectMixin
from fairdm.views import FairDMCreateView, FairDMDeleteView, FairDMUpdateView

from .. import utils
from ..forms.contribution import PersonCreateForm, QuickAddContributionForm, UpdateContributionForm
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

    form_class = PersonCreateForm

    def form_valid(self, form):
        response = super().form_valid(form)

        # Users created through this view are not active by default.
        # Being active requires having an account and loggin in.
        self.object.is_active = False
        self.object.save()

        self.base_object.add_contributor(
            self.object,
            with_roles=self.base_object.DEFAULT_ROLES,
        )

        self.messages.info("Succesfully added contributor.")

        return response

    def assign_permissions(self):
        # assigning full permissions is the default for FairDMCreateView (perhaps needs to be reviewed)
        # overriding this method to prevent that
        # Need to think about what permissions they get by default. Perhaps depends on the role?
        pass

    # return render(self.request, "contributors/contribution.html", {"contributor": contribution})

    # def get_success_url(self):
    # """Redirect to the detail page of the base object."""
    # return self.base_object.get_absolute_url()


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

    def get_success_url(self):
        """Redirect to the detail page of the base object."""
        return plugins.reverse(self.base_object, "contributors")


class ContributionRemoveView(BaseContributionView, FairDMDeleteView):
    model = Contribution
    title = _("Remove Contributor")

    def get_heading_config(self):
        """Return the heading configuration for the view."""
        return {
            "title": _(f"Remove {self.object.contributor}"),
            "description": _(
                "Are you sure you want to remove this contributor? They will no longer have access if visibility is set to private. Do you want to continue?"
            ),
        }
