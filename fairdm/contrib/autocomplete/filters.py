"""Filters that narrow a list by the records of one kind, chosen with a counted control."""

import django_filters


class RecordMultipleFilter(django_filters.ModelMultipleChoiceFilter):
    """Narrow a list to the records that point at any of several chosen records.

    The control is the multiple record field of one kind, at ``public`` scope unless told
    otherwise, so a visitor and a signed-in researcher are offered the same records. The
    field validates what it is sent against its view, never against the page's search.

    Args:
        field_class: The multiple record field to draw, such as ``DatasetMultipleChoiceField``.
        scope: How much the person may be offered. Defaults to ``"public"``.
        **kwargs: Passed to ``ModelMultipleChoiceFilter``. A ``queryset`` is not taken: the
            field's view decides what is offered.

    Example:
        ```python
        dataset = RecordMultipleFilter(DatasetMultipleChoiceField, field_name="dataset")
        ```
    """

    def __init__(self, field_class, *, scope="public", **kwargs):
        super().__init__(**kwargs)
        self.field_class = field_class
        self.extra["scope"] = scope

    @property
    def field(self):
        """Build the field and hand it the filter set's request."""
        field = super().field
        field.given_request = self.get_request()
        return field

    def for_api(self):
        """Return the plain filter the API uses in place of this one.

        The API matches records by short identifier and has no control to draw, so it takes
        a plain model filter over the records this filter offers at its scope.

        Returns:
            A ``ModelMultipleChoiceFilter`` over the same relation.
        """
        field_class = self.field_class
        scope = self.extra["scope"]

        def offered(request):
            view = field_class.view_class.for_scope(scope)()
            return view.offered(getattr(request, "user", None))

        return django_filters.ModelMultipleChoiceFilter(
            field_name=self.field_name,
            label=self.label,
            queryset=offered,
            conjoined=self.conjoined,
            distinct=self.distinct,
        )
