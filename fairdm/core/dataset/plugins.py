from django.conf import settings
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from mvp.views.detail import CRUDDirectoryMixin
from mvp.views.inline import InlinesMixin

from fairdm import plugins
from fairdm.contrib.generic.plugins import (
    DescriptionsPlugin,
    KeyDatesPlugin,
    KeywordsPlugin,
)
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins.access import has_perm
from fairdm.core.formsets import date_ordering_formset
from fairdm.core.plugins import OverviewPlugin
from fairdm.core.related_records import DatasetDateInline, DatasetIdentifierInline
from fairdm.utils.choices import Visibility
from fairdm.utils.utils import user_guide
from fairdm.views import FairDMUpdateView

from .forms import DatasetForm
from .models import Dataset, DatasetDate, DatasetDescription

DATASET_SETTINGS = getattr(settings, "FAIRDM_DATASET", {})


def dataset_is_visible(request, obj):
    """Whether ``request``'s user may view ``obj`` — a public dataset always, a private one only
    with ``dataset.view_dataset``.

    A registered page resolves its record through machinery that deliberately reads past
    filtered managers (``fairdm.contrib.plugins.base.Plugin.get_base_object``), on the assumption
    the page gates itself. Unlike ``Project``, ``Dataset.objects`` (the default manager) already
    excludes private records — but the plugin lookup reads through ``Dataset.all_objects``
    instead, precisely so a private dataset's owner can still open it, which is what makes this
    check necessary rather than redundant (research.md R2). Set as :class:`Overview`'s ``check``.
    """
    if obj is None:
        return True
    if obj.visibility == Visibility.PUBLIC:
        return True
    return has_perm(request, "dataset.view_dataset", obj)


def visible_to_holder_of(permission):
    """Build a ``check`` like :func:`dataset_is_visible`, except a private ``obj`` also stays
    visible to a user holding ``permission`` on it specifically, at record level.

    :class:`Update` needs this rather than bare :func:`dataset_is_visible`: its own permission is
    ``change_dataset``, not ``view_dataset``, and creating a dataset grants all five rights on it
    at once (``DatasetCreateView.form_valid``) — nothing in the running application ever grants
    editing rights on a record without also granting the right to view it. A record-level grant of
    the page's own permission is therefore already evidence of legitimate access. Mirrors
    ``fairdm.core.project.plugins.visible_to_holder_of``, whose docstring explains why an
    additional view cannot simply inherit :class:`Overview`'s ``check`` — the owner is read from
    ``plugin_class``, which exists only on the view instance ``as_view()`` builds, not on the
    class ``can_open`` is handed.
    """

    def check(request, obj):
        if dataset_is_visible(request, obj):
            return True
        if obj is None:
            return False
        return request.user.has_perm(permission, obj)

    return check


# ======== Management Plugins ======== #


@plugins.register(Dataset, label=_("Descriptions"), icon="description", order=510)
class Descriptions(DescriptionsPlugin):
    heading_config = {
        "title": _("Descriptions"),
        "description": _(
            "Provide key details about your dataset, including its name and key descriptions. This information is essential for conveying the dataset's purpose and scope, helping users quickly understand its relevance."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/descriptions"),
                "icon": "documentation",
            }
        ],
    }
    # These three plugins are editing surfaces, not reading ones. Without a
    # declared permission `can_open()` admits every request, anonymous
    # included, and a private dataset's metadata would stay readable and
    # writable by anyone holding its UUID.
    permission = "dataset.change_dataset"
    model = Dataset
    inline_model = DatasetDescription


@plugins.register(Dataset, label=_("Keywords"), icon="keywords", order=520)
class Keywords(KeywordsPlugin):
    heading_config = {
        "title": _("Keywords"),
        "description": _(
            "Keywords enhance your dataset's visibility in search engines and catalogs by summarizing its content. They help others quickly evaluate its relevance without reading the full documentation."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/keywords"),
                "icon": "documentation",
            }
        ],
    }
    permission = "dataset.change_dataset"


@plugins.register(Dataset, label=_("Key Dates"), icon="date", order=530)
class KeyDates(KeyDatesPlugin):
    heading_config = {
        "title": _("Key Dates"),
        "description": _(
            "Entering key dates helps track important milestones and timelines, supporting effective dataset management and giving others insight into the dataset's history and progress."
        ),
        "links": [
            {
                "text": _("Learn more"),
                "href": user_guide("dataset/key-dates"),
                "icon": "documentation",
            }
        ],
    }
    permission = "dataset.change_dataset"
    model = Dataset
    inline_model = DatasetDate


class DatasetDatesInline(DatasetDateInline):
    """The dataset's own dates, ordered ``CollectionStart`` before ``CollectionEnd`` (014 plan
    P3). Parameterised on :attr:`DatasetDate.START_TYPE`/``END_TYPE`` rather than the literals,
    and stated here rather than in ``related_records.py`` because it is this page's own choice of
    which shared declaration to combine with which shared rule — mirrors
    ``fairdm.core.project.plugins.ProjectDatesInline``, whose docstring explains why (a project's
    dates page pairs the same base with a differently-typed, differently-worded pair)."""

    formset = date_ordering_formset(
        DatasetDate.START_TYPE,
        DatasetDate.END_TYPE,
        _(
            "The dataset's collection end date (%(end)s) cannot be before its "
            "collection start date (%(start)s)."
        ),
    )


class Update(Plugin, InlinesMixin, FairDMUpdateView):
    """The dataset's own attributes: image, name, project, licence, visibility and the
    publication that describes it, plus its identifiers and its collection dates (014 plan P3).
    An additional view belonging to :class:`Overview` rather than a registration of its own, so
    the navigation strip carries one entry for the whole collection — mirrors
    ``fairdm.core.project.plugins.Update``.

    Supersedes the standalone ``dataset-update`` route and ``DatasetUpdateView``, which duplicated
    the same surface with its own, separate navigation entry and hand-wrote a DOI text box where
    the identifiers row set now edits every identifier, DOI included.
    """

    url_path = "update"
    # An additional view inherits its owner's `check` but never its `permission`
    # (fairdm/contrib/plugins/access.py `can_open`), so one that states none is open to everyone,
    # anonymous included (mirrors project issue #279). This page writes its own.
    permission = "dataset.change_dataset"
    # Stated directly rather than inherited from Overview — inheritance does not carry to an
    # additional view (see `visible_to_holder_of`). `visible_to_holder_of` rather than bare
    # `dataset_is_visible`: this page's own permission is `change_dataset`, not `view_dataset`,
    # and a record-level grant of it is already evidence of legitimate access.
    check = staticmethod(visible_to_holder_of("dataset.change_dataset"))
    page_title = _("Update dataset")
    model = Dataset
    form_class = DatasetForm
    template_name = "dataset/plugins/update.html"
    inlines = [DatasetIdentifierInline, DatasetDatesInline]

    def handle_no_permission(self):
        """Mirrors :meth:`Overview.handle_no_permission`: a private dataset the requester may
        not change answers 404, not 403, so this address does not become an existence oracle for
        embargoed metadata alongside the dataset's own page. Falls through to the inherited
        behaviour once the dataset is public — a refusal for some other reason on a public
        record must still say so plainly, not hide behind a 404."""
        obj = self.base_object
        if obj is not None and obj.visibility != Visibility.PUBLIC:
            raise Http404("No dataset matches the given query.")
        return super().handle_no_permission()

    def get_form_kwargs(self):
        """Add ``request`` so the project field is narrowed to the researcher's own projects,
        on the same terms as the creation page (FR-026)."""
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_success_url(self):
        return self.base_object.get_absolute_url()


@plugins.register(Dataset, label=_("Overview"), icon="view", order=0)
class Overview(CRUDDirectoryMixin, OverviewPlugin):
    """The dataset's own page: its registered overview, and the root of its collection.

    ``fairdm/core/project/plugins.py``'s ``Overview`` applied to datasets (014 plan P1, research.md
    R1): before this, ``Dataset`` had no ``Overview`` registration at all, and its own page was the
    standalone ``DatasetDetailView`` this replaces. Declaring no ``url_path`` of its own keeps it
    the root of the record's include, matching every other core record.

    ``extra_views`` carries :class:`Update` (014 US-3) — the descriptions and deletion pages are
    appended by the runs that build them (US-4, US-6), each mirroring
    :class:`~fairdm.core.project.plugins.Delete`/``Descriptions``.
    """

    url_path = None
    model = Dataset
    check = staticmethod(dataset_is_visible)
    template_name = "dataset/dataset_detail.html"
    extra_views = [Update]

    def handle_no_permission(self):
        """Preserve the not-found response the retired ``DatasetDetailView`` gave a user who may
        not see a private dataset (014 plan P1), so this address does not become an existence
        oracle for embargoed metadata: ``PermissionRequiredMixin``'s own behaviour redirects an
        anonymous visitor to sign in and gives a signed-in stranger a permission refusal, both of
        which confirm the record is there. Falls through to that inherited behaviour once the
        dataset is public — a refusal for some other reason on a public record must still say so
        plainly, not hide behind a 404.
        """
        obj = self.base_object
        if obj is not None and obj.visibility != Visibility.PUBLIC:
            raise Http404("No dataset matches the given query.")
        return super().handle_no_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ``dataset_detail.html`` predates the registration and was rendered by
        # ``DatasetDetailView``, a ``SingleObjectMixin``-based view whose ``context_object_name``
        # supplied ``dataset`` automatically. This view is a ``TemplateView`` and does not add it
        # on its own (mirrors ``project.plugins.Overview.get_context_data``).
        context["dataset"] = self.base_object
        return context
