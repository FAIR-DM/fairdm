from django.conf import settings
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from mvp.views.detail import CRUDDirectoryMixin

from fairdm import plugins
from fairdm.contrib.generic.plugins import (
    DescriptionsPlugin,
    KeyDatesPlugin,
    KeywordsPlugin,
)
from fairdm.contrib.plugins.access import has_perm
from fairdm.core.plugins import OverviewPlugin
from fairdm.utils.choices import Visibility
from fairdm.utils.utils import user_guide

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


@plugins.register(Dataset, label=_("Overview"), icon="view", order=0)
class Overview(CRUDDirectoryMixin, OverviewPlugin):
    """The dataset's own page: its registered overview, and the root of its collection.

    ``fairdm/core/project/plugins.py``'s ``Overview`` applied to datasets (014 plan P1, research.md
    R1): before this, ``Dataset`` had no ``Overview`` registration at all, and its own page was the
    standalone ``DatasetDetailView`` this replaces. Declaring no ``url_path`` of its own keeps it
    the root of the record's include, matching every other core record.

    ``extra_views`` is empty for now (014 T056) — the update, descriptions and deletion pages are
    appended by the runs that build them (US-3, US-4, US-6), each mirroring
    :class:`~fairdm.core.project.plugins.Update`/``Delete``/``Descriptions``.
    """

    url_path = None
    model = Dataset
    check = staticmethod(dataset_is_visible)
    template_name = "dataset/dataset_detail.html"
    extra_views = []

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
