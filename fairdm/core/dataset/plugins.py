from collections import Counter

from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from meta.views import MetadataMixin
from mvp.views import MVPFormView
from mvp.views.detail import CRUDDirectoryMixin
from mvp.views.inline import InlinesMixin

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins.access import has_perm
from fairdm.contrib.plugins.mixins import (
    PrivateRecordNotFoundMixin,
    RecordOwnPageBackFallbackMixin,
)
from fairdm.core.descriptions import VocabularyDescriptionsForm
from fairdm.core.formsets import date_ordering_formset
from fairdm.core.measurement.models import Measurement
from fairdm.core.plugins import OverviewPlugin
from fairdm.core.related_records import DatasetDateInline, DatasetIdentifierInline
from fairdm.core.sample.models import Sample
from fairdm.utils.choices import Visibility
from fairdm.views import FairDMDeleteView, FairDMUpdateView

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

# A dataset once carried two further registered pages of its own. Neither survives here:
#
# - Keywords. Keyword editing is rebuilt whole against the controlled vocabularies in a later
#   specification, so the page is removed rather than carried over (FR-063). The generic
#   ``KeywordsPlugin`` it was built on stays where it is; a sample still registers one.
# - Key Dates. A dataset's collection dates are now rows on its update page
#   (:class:`DatasetDatesInline`), so a second page editing the same records would be both a
#   duplicate and a second navigation entry (FR-062). Mirrors ``fairdm.core.project.plugins``,
#   which registers neither.


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


class Update(PrivateRecordNotFoundMixin, Plugin, InlinesMixin, FairDMUpdateView):
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

    # FR-045 — this page offers the deletion page. The shared form shell already carries the slot
    # and fills it from get_delete_url(); all this page supplies is where the three routes it
    # reverses actually live, since the interface layer's defaults name the standalone
    # `dataset-update`/`dataset-delete` routes this feature retires.
    crud_views = {
        "list": "dataset-list",
        "update": "dataset:overview-update",
        "delete": "dataset:overview-delete",
    }
    show_list_action = True

    def show_delete_action(self, user):
        """Offered on the right ``Delete`` itself requires, not on the one that opened this page:
        a user may hold ``change_dataset`` without ``delete_dataset``, and a link they cannot
        follow is worse than no link."""
        return has_perm(self.request, Delete.permission, self.base_object)

    def get_form_kwargs(self):
        """Add ``request`` so the project field is narrowed to the researcher's own projects,
        on the same terms as the creation page (FR-026)."""
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_success_url(self):
        return self.base_object.get_absolute_url()


class Descriptions(PrivateRecordNotFoundMixin, Plugin, MetadataMixin, MVPFormView):
    """The dataset's own descriptions: one editable area per concept in
    ``DatasetDescription.VOCABULARY``, generated by :class:`VocabularyDescriptionsForm`.

    An additional view belonging to :class:`Overview`, per :class:`Update` above (014 plan P7)
    — this is ``fairdm.core.project.plugins.Descriptions`` with two names changed. Supersedes
    the standalone ``Descriptions(DescriptionsPlugin)`` registration this page used to be, which
    offered add/remove rows rather than the fixed set of labelled areas this page requires. The
    generic ``fairdm.contrib.generic.plugins.DescriptionsPlugin`` is neither used nor repaired
    here: the sample pages still use it, and it is #280's business.
    """

    # An additional view inherits its owner's `check` but never its `permission`
    # (fairdm/contrib/plugins/access.py `can_open`), so one that states none is open to everyone,
    # anonymous included (mirrors project issue #279). This page writes its own.
    permission = "dataset.change_dataset"
    # Stated directly rather than inherited from Overview — inheritance does not carry to an
    # additional view (see `Update`, `visible_to_holder_of`). Bare `dataset_is_visible` rather
    # than `visible_to_holder_of`, matching `fairdm.core.project.plugins.Descriptions` exactly.
    check = staticmethod(dataset_is_visible)
    page_title = _("Descriptions")
    model = Dataset
    form_class = VocabularyDescriptionsForm
    # Set explicitly even though it is also the inherited fallback. A plain form view derives no
    # template from a model the way Update's own view does, so leaving template_name unset makes
    # Django raise before the fallback is ever reached.
    template_name = "form_view.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["related_model"] = DatasetDescription
        kwargs["instance"] = self.base_object
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return self.base_object.get_absolute_url()


class Delete(
    PrivateRecordNotFoundMixin, RecordOwnPageBackFallbackMixin, Plugin, FairDMDeleteView
):
    """The dataset's own deletion page, confirmed by typing its name and previewing what it
    takes with it through the shell's own cascade preview (014 plan P7, US-6) — mirrors
    ``fairdm.core.project.plugins.Delete``, minus that page's protected-object guard: FR-048
    holds a dataset's visibility never blocks its own deletion on its own, and a dataset has no
    descendant record equivalent to a project's public datasets for such a guard to protect.

    An additional view belonging to :class:`Overview`, per :class:`Update` and
    :class:`Descriptions` above.
    """

    url_path = "delete"
    # An additional view inherits its owner's `check` but never its `permission`
    # (fairdm/contrib/plugins/access.py `can_open`), so one that states none is open to everyone,
    # anonymous included (mirrors project issue #279). This page writes its own.
    permission = "dataset.delete_dataset"
    # Stated directly rather than inherited from Overview — inheritance does not carry to an
    # additional view (see `Update`, `visible_to_holder_of`). `visible_to_holder_of` rather than
    # bare `dataset_is_visible`: this page's own permission is `delete_dataset`, not
    # `view_dataset`, and a record-level grant of it is already evidence of legitimate access.
    check = staticmethod(visible_to_holder_of("dataset.delete_dataset"))
    page_title = _("Delete dataset")
    model = Dataset
    require_confirmation = True
    # FR-046 — the shell's own cascade preview (`MVPDeleteView.show_related_objects`), not a
    # hand-written count of samples and measurements.
    show_related_objects = True
    success_url = reverse_lazy("dataset-list")

    def get_confirmation_value(self):
        return self.base_object.name

    def _collect_deletion_data(self):
        """Cache the collector's walk for the life of the request. The shell calls it once to
        decide ``is_protected``, and :meth:`related_objects_summary` needs the same result to
        count by type — on a dataset carrying data the walk loads every sample and measurement
        into memory, so running it twice doubles the most expensive thing this page does.
        """
        if not hasattr(self, "deletion_data"):
            self.deletion_data = super()._collect_deletion_data()
        return self.deletion_data

    def get_context_data(self, **kwargs):
        """FR-047/T088 — replace the shell's own instance-by-instance cascade preview with a
        count-only summary of samples and measurements, the two things that mean anything to a
        researcher confirming a deletion. Everything else the collector also reports
        (contributors, contribution roles, descriptions, dates, identifiers) is cascade-deleted
        along with the dataset but never shown here — on a real dataset it would run to
        thousands of lines. An empty dataset (no samples, no measurements) gets no
        related-records warning at all, since an empty ``related_objects`` renders nothing
        (``delete_view.html``).

        Left untouched when the object is protected: ``protected_objects``/``is_protected``
        name what is *blocking* deletion, not what deletion would remove, and US-6 settled that
        path already.
        """
        context = super().get_context_data(**kwargs)
        if self.show_related_objects and not context["is_protected"]:
            context["related_objects"] = self.related_objects_summary()
        return context

    def related_objects_summary(self):
        """Count instances by their own concrete class, not the collector's dict key: Sample
        and Measurement are polymorphic, multi-table-inherited models, so deleting one concrete
        row (e.g. a ``RockSample``) is reported by Django's ``Collector`` as two entries — the
        base ``Sample``/``Measurement`` parent-link row and the concrete subclass row for the
        same underlying record. Counting by ``type(instance)`` and skipping the bare base class
        avoids counting that one row twice.
        """
        related_map, _protected = self._collect_deletion_data()
        sample_counts = Counter()
        measurement_counts = Counter()
        for instances in related_map.values():
            for instance in instances:
                concrete = type(instance)
                if concrete is Sample or concrete is Measurement:
                    continue
                if isinstance(instance, Sample):
                    sample_counts[concrete] += 1
                elif isinstance(instance, Measurement):
                    measurement_counts[concrete] += 1

        groups = []
        for label, counts in (
            (_("Samples"), sample_counts),
            (_("Measurements"), measurement_counts),
        ):
            if not counts:
                continue
            lines = [
                f"{concrete._meta.verbose_name_plural.title()} ({count})"
                for concrete, count in sorted(
                    counts.items(), key=lambda item: item[0]._meta.verbose_name_plural
                )
            ]
            groups.append((label, lines, 0))
        return groups


@plugins.register(Dataset, label=_("Overview"), icon="view", order=0)
class Overview(PrivateRecordNotFoundMixin, CRUDDirectoryMixin, OverviewPlugin):
    """The dataset's own page: its registered overview, and the root of its collection.

    ``fairdm/core/project/plugins.py``'s ``Overview`` applied to datasets (014 plan P1, research.md
    R1): before this, ``Dataset`` had no ``Overview`` registration at all, and its own page was the
    standalone ``DatasetDetailView`` this replaces. Declaring no ``url_path`` of its own keeps it
    the root of the record's include, matching every other core record.

    ``extra_views`` carries :class:`Update` (014 US-3), :class:`Delete` (014 US-6) and
    :class:`Descriptions` (014 US-4).

    Mixes in the interface layer's own action-link mechanism (014 plan P7, US-5) rather than a
    hand-rolled one — mirrors ``fairdm.core.project.plugins.Overview`` exactly: ``directory``
    names the three actions its extra views need an entry for, and ``crud_views`` reverses each
    to :class:`Update`'s, :class:`Delete`'s and :class:`Descriptions`'s own registered names.
    ``update`` and ``delete`` are drawn by the shared ``detail_view.html`` shell as its "Edit"
    and "Delete" buttons; the shell has no generic slot for a third action, so ``descriptions``
    is drawn by this page's own ``dataset_detail.html`` (014 plan P7, mirrors project D13).
    """

    url_path = None
    model = Dataset
    check = staticmethod(dataset_is_visible)
    template_name = "dataset/dataset_detail.html"
    extra_views = [Update, Delete, Descriptions]

    directory = ["update", "delete", "descriptions"]
    crud_views = {
        "update": "dataset:overview-update",
        "delete": "dataset:overview-delete",
        "descriptions": "dataset:overview-descriptions",
    }

    def show_update_action(self, user):
        return has_perm(self.request, Update.permission, self.base_object)

    def show_delete_action(self, user):
        return has_perm(self.request, Delete.permission, self.base_object)

    def show_descriptions_action(self, user):
        return has_perm(self.request, Descriptions.permission, self.base_object)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ``dataset_detail.html`` predates the registration and was rendered by
        # ``DatasetDetailView``, a ``SingleObjectMixin``-based view whose ``context_object_name``
        # supplied ``dataset`` automatically. This view is a ``TemplateView`` and does not add it
        # on its own (mirrors ``project.plugins.Overview.get_context_data``).
        context["dataset"] = self.base_object
        return context
