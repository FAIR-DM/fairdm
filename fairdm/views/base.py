from __future__ import annotations

from django.db.models import RestrictedError
from django.utils.http import url_has_allowed_host_and_scheme
from django_filters.views import FilterView
from meta.views import MetadataMixin
from mvp.integrations.django_filters.views import MVPFilteredListView
from mvp.integrations.django_tables.views import MVPTableViewMixin
from mvp.views import (
    MVPCreateView,
    MVPDeleteView,
    MVPDetailView,
    MVPTemplateView,
    MVPUpdateView,
)


class FairDMTemplateView(MetadataMixin, MVPTemplateView):
    """Template-only page with AdminLTE layout and SEO metadata support.

    Extends :class:`mvp.views.MVPTemplateView` with
    :class:`meta.views.MetadataMixin` to inject Open Graph / Twitter Card
    metadata into every response. Use this as the base class for any
    FairDM page that renders a static or lightly dynamic template and
    needs SEO metadata — instead of Django's ``TemplateView`` or
    ``MVPTemplateView`` directly.

    Context:
        meta: Injected by ``MetadataMixin``. Contains Open Graph, Twitter
            Card, and Schema.org metadata derived from view-level attributes
            such as ``title``, ``description``, ``image``, and ``keywords``.
            See :class:`meta.views.MetadataMixin` for the full attribute list.
        page (dict): AdminLTE page configuration — ``title``, ``subtitle``,
            ``icon``, ``class``, ``breadcrumbs``. Injected by ``PageMixin``
            via ``MVPTemplateView``.

    Example::

        from fairdm.views import FairDMTemplateView


        class AboutView(FairDMTemplateView):
            template_name = "myapp/about.html"
            title = "About Us"
            description = "Learn about our research data portal."
    """

    # A default template name is set here to act as a placeholder to avoid 500 errors
    # due to this attribute being missing.
    # Can be removed after https://github.com/django-mvp/django-mvp/issues/187 is merged and released.
    template_name = "page_view.html"


class FairDMListView(MetadataMixin, MVPFilteredListView):
    """Paginated, filterable list page with card layout and SEO metadata support.

    Extends :class:`mvp.views.list.MVPFilteredListView` (which composes
    ``MVPListViewMixin`` with ``django_filters.views.FilterView``) with
    :class:`meta.views.MetadataMixin`. Use this as the base class for any
    FairDM list page that displays objects as cards or custom list items and
    supports filtering via a ``filterset_class``.

    For tabular data display (rows and columns), use
    :class:`FairDMTableView` instead.

    Config:
        paginate_by (int): Number of objects per page. Default: ``25``.
        grid (dict): Responsive grid configuration passed to the template as
            ``grid_config``. Keys map to CSS breakpoint helpers (e.g.,
            ``{"cols": 1, "gap": 2}``). Default: ``{"cols": 1, "gap": 2}``.
        list_item_template (str | None): Explicit path to the partial template
            rendered for each list item. When ``None``, auto-derived from the
            model as ``"<app_label>/<model_name>_list_item.html"``.
            Default: ``None``.
        search_fields (list[str] | None): Model field paths searched by the
            ``?q=`` query parameter. Default: ``None`` (search disabled).
        filterset_class: A ``django_filters.FilterSet`` subclass for
            advanced filtering. Default: ``None``.

    Override hooks:
        get_queryset(): Return the base queryset (add ``select_related`` /
            ``prefetch_related`` here for performance).
        get_grid_config(): Return the grid breakpoint dict.
        get_list_item_template(): Return the item partial template path.
        get_empty_state_heading() / get_empty_state_message(): Customise
            the empty-state UI.

    Context:
        meta: SEO metadata object (see :class:`meta.views.MetadataMixin`).
        grid_config (dict): Grid breakpoint configuration from ``grid``.
        list_item_template (str): Resolved item partial template path.
        empty_state (dict): ``{"heading": str, "message": str}``.
        page (dict): AdminLTE page metadata from ``PageMixin``.
        filter: Active ``FilterSet`` instance (when ``filterset_class`` set).
        object_list: The paginated queryset.

    Example::

        from fairdm.views import FairDMListView
        from .filters import ProjectFilter
        from .models import Project


        class ProjectListView(FairDMListView):
            model = Project
            filterset_class = ProjectFilter
            search_fields = ["name", "uuid"]
            grid = {"cols": 1, "sm": 2, "lg": 3}
    """

    paginate_by = 25
    grid = {"cols": 1, "gap": 2}


class FairDMDetailView(MetadataMixin, MVPDetailView):
    """Object detail page with AdminLTE layout and SEO metadata support.

    Extends :class:`mvp.views.detail.MVPDetailView` with
    :class:`meta.views.MetadataMixin`. Use this as the base class for any
    FairDM page that displays a single model instance — instead of Django's
    ``DetailView`` or ``MVPDetailView`` directly.

    Context:
        meta: SEO metadata object (see :class:`meta.views.MetadataMixin`).
            Set view-level attributes such as ``title``, ``description``, and
            ``image`` to populate Open Graph and Twitter Card tags.
        object: The model instance being displayed.
        page (dict): AdminLTE page metadata. The default page title is
            derived from ``str(self.object)`` via ``MVPDetailView``.

    Example::

        from fairdm.views import FairDMDetailView
        from .models import Project


        class ProjectDetailView(FairDMDetailView):
            model = Project
    """


class FairDMCreateView(MetadataMixin, MVPCreateView):
    """Object creation form with AdminLTE layout and SEO metadata support.

    Thin composition of :class:`mvp.views.edit.MVPCreateView` with
    :class:`meta.views.MetadataMixin`. Adds no attributes of its own;
    all configuration is inherited from the parent classes. Use this as
    the base class for any FairDM create view — instead of Django's
    ``CreateView`` or ``MVPCreateView`` directly.

    Context:
        meta: SEO metadata object (see :class:`meta.views.MetadataMixin`).
        form: The model form instance.
        page (dict): AdminLTE page metadata. Default page title is
            ``"Create <Verbose Name>"`` via ``MVPCreateView``.

    Example::

        from fairdm.views import FairDMCreateView
        from .models import Dataset


        class DatasetCreateView(FairDMCreateView):
            model = Dataset
            fields = ["name", "description", "visibility"]
            success_url = "list"  # CRUD shorthand resolved by MVPCreateView
    """

    pass


class FairDMUpdateView(MetadataMixin, MVPUpdateView):
    """Object update form with AdminLTE layout and SEO metadata support.

    Extends :class:`mvp.views.edit.MVPUpdateView` with
    :class:`meta.views.MetadataMixin`. Use this as the base class for any
    FairDM edit/update view — instead of Django's ``UpdateView`` or
    ``MVPUpdateView`` directly.

    Context:
        meta: SEO metadata object (see :class:`meta.views.MetadataMixin`).
        form: The bound model form instance.
        object: The model instance being updated.
        delete_url (str): URL for the delete action, injected when the delete
            view is registered (see ``MVPUpdateView``).
        page (dict): AdminLTE page metadata. Default page title is
            ``"Update <Verbose Name>"`` via ``MVPUpdateView``.

    Example::

        from fairdm.views import FairDMUpdateView
        from .models import Dataset


        class DatasetUpdateView(FairDMUpdateView):
            model = Dataset
            fields = ["name", "description", "visibility"]
            success_url = "detail"  # CRUD shorthand resolved by MVPUpdateView
    """


class FairDMDeleteView(MetadataMixin, MVPDeleteView):
    """Object deletion confirmation page with AdminLTE layout and SEO metadata support.

    Extends :class:`mvp.views.edit.MVPDeleteView` with
    :class:`meta.views.MetadataMixin`. Use this as the base class for any
    FairDM deletion confirmation view — instead of Django's ``DeleteView``
    or ``MVPDeleteView`` directly.

    Config:
        success_url (str): Required. URL to redirect to after deletion.
            Accepts literal URL paths or CRUD shorthands (e.g. ``"list"``).

    Context:
        meta: SEO metadata object (see :class:`meta.views.MetadataMixin`).
        object: The model instance to be deleted.
        page (dict): AdminLTE page metadata.

    Example::

        from fairdm.views import FairDMDeleteView
        from .models import Dataset


        class DatasetDeleteView(FairDMDeleteView):
            model = Dataset
            success_url = "list"  # CRUD shorthand resolved by MVPDeleteView
    """

    def _collect_deletion_data(self):
        """Treat a restricted relation as a refusal, the same as a protected one.

        ``MVPDeleteView`` catches ``ProtectedError`` and turns it into the refusal the template
        already draws — the blocking records listed, no submit button. It does not catch
        ``RestrictedError``, which is a sibling under ``IntegrityError`` rather than a subclass,
        so a ``RESTRICT`` relation raises straight out of the page instead. ``Measurement.sample``
        is one, so a dataset whose samples are measured by another dataset reaches this.

        Remove once django-mvp#308 lands.
        """
        try:
            return super()._collect_deletion_data()
        except RestrictedError as exc:
            return {}, list(exc.restricted_objects)

    def get_back_url(self) -> str:
        """``MVPDeleteView``'s own "Back", with its destination behind an overridable hook.

        The upstream method reads ``?back``, validates it against the current host, and then
        falls back to the list page in the same body. A page that wants a different fallback
        has nowhere to say so, so it has to restate the query-string handling — including the
        open-redirect guard — to change the last line. Splitting the two means the guard is
        written once and a subclass overrides :meth:`get_back_url_fallback` alone.

        Remove once django-mvp#309 lands.
        """
        candidate: str | None = self.request.GET.get("back")
        if candidate and url_has_allowed_host_and_scheme(
            url=candidate,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return candidate
        return self.get_back_url_fallback()

    def get_back_url_fallback(self) -> str:
        """Where "Back" points when the request carries no usable ``?back``.

        Keeps ``MVPDeleteView``'s own answer — the registered list page.
        """
        return self.resolve_crud_url("list") or ""


class FairDMTableView(MetadataMixin, MVPTableViewMixin, FilterView):
    """Filtered table list page with AdminLTE layout and SEO metadata support.

    Composes :class:`mvp.views.table.MVPTableViewMixin`,
    :class:`django_filters.views.FilterView`, and
    :class:`meta.views.MetadataMixin`. Use this when objects should be
    displayed in a rows-and-columns table (powered by ``django-tables2``)
    rather than as cards or custom list items.

    For card-style or custom-item list pages, use :class:`FairDMListView`
    instead.

    Config:
        table_class (type): **Required.** A ``django_tables2.Table`` subclass
            that defines the columns to display.
        filterset_class: A ``django_filters.FilterSet`` subclass for column
            filtering. Optional but strongly recommended.
        template_name (str): The template responsible for rendering the
            ``{{ table }}`` object. The template must explicitly render the
            table — no automatic table rendering is provided.
        paginate_by (int): Number of rows per page. Default: ``100``.
            ``paginate_by`` is the only page-size control a table view has —
            ``MVPTableViewMixin`` switches pagination off entirely when it is
            unset, and passes it explicitly when it is set, which takes
            precedence over ``Table.Meta.per_page``.

    Context:
        meta: SEO metadata object (see :class:`meta.views.MetadataMixin`).
        table: The rendered ``django_tables2.Table`` instance.
        filter: Active ``FilterSet`` instance (when ``filterset_class`` set).
        page (dict): AdminLTE page metadata.

    Example::

        import django_tables2 as tables
        from fairdm.views import FairDMTableView
        from .filters import MeasurementFilter
        from .models import Measurement


        class MeasurementTable(tables.Table):
            class Meta:
                model = Measurement
                fields = ["name", "value", "unit", "created"]


        class MeasurementTableView(FairDMTableView):
            model = Measurement
            table_class = MeasurementTable
            filterset_class = MeasurementFilter
            template_name = "measurements/measurement_table.html"
    """

    paginate_by = 100
