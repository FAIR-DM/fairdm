from django.conf import settings
from django.http import Http404
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from meta.views import MetadataMixin
from mvp.views import MVPFormView
from mvp.views.detail import CRUDDirectoryMixin
from mvp.views.inline import InlinesMixin

from fairdm import plugins
from fairdm.contrib.generic.plugins import KeyDatesPlugin, KeywordsPlugin
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins.access import has_perm
from fairdm.core.descriptions import VocabularyDescriptionsForm
from fairdm.core.formsets import date_ordering_formset
from fairdm.core.plugins import OverviewPlugin
from fairdm.core.related_records import DatasetDateInline, DatasetIdentifierInline
from fairdm.utils.choices import Visibility
from fairdm.utils.utils import user_guide
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


class Descriptions(Plugin, MetadataMixin, MVPFormView):
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

    def handle_no_permission(self):
        """Mirrors :meth:`Update.handle_no_permission`: a private dataset the requester may not
        change answers 404, not a permission refusal or a sign-in redirect, so this address does
        not become a second existence oracle for embargoed metadata alongside the dataset's own
        page and its update page (014 US-3, carried forward to this page)."""
        obj = self.base_object
        if obj is not None and obj.visibility != Visibility.PUBLIC:
            raise Http404("No dataset matches the given query.")
        return super().handle_no_permission()

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


class Delete(Plugin, FairDMDeleteView):
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

    def handle_no_permission(self):
        """Mirrors :meth:`Update.handle_no_permission`: a private dataset the requester may not
        delete answers 404, not a permission refusal or a sign-in redirect, so this address does
        not become a third existence oracle for embargoed metadata alongside the dataset's own
        page and its update page."""
        obj = self.base_object
        if obj is not None and obj.visibility != Visibility.PUBLIC:
            raise Http404("No dataset matches the given query.")
        return super().handle_no_permission()

    def get_confirmation_value(self):
        return self.base_object.name

    def get_back_url(self) -> str:
        """The confirmation page's own "Back" falls back to the dataset itself rather than the
        dataset list (FR-052/FR-053), mirroring ``fairdm.core.project.plugins.Delete``:
        ``MVPDeleteView``'s own fallback is ``resolve_crud_url("list")``, which this page never
        shows (it carries no ``list`` entry in its ``directory``), so the shell drew that control
        as an empty ``href=""``. From a dataset's own deletion page, "back" means back to the
        record being considered for deletion. The ``?back`` query-string override above this in
        the MRO is preserved unchanged.
        """
        candidate = self.request.GET.get("back")
        if candidate and url_has_allowed_host_and_scheme(
            url=candidate,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return candidate
        return self.base_object.get_absolute_url()


@plugins.register(Dataset, label=_("Overview"), icon="view", order=0)
class Overview(CRUDDirectoryMixin, OverviewPlugin):
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
