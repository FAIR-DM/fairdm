"""Mixins that decide how a refused plugin page answers and where its Back control points."""

from __future__ import annotations

from django.http import Http404

from fairdm.utils.choices import Visibility


class PrivateRecordNotFoundMixin:
    """Answer 404 rather than 403 or a sign-in redirect for a private record.

    A 403 or a redirect would confirm that a private record exists at this address. The
    404 message names the record's kind from ``registered_model``.

    List this mixin before ``Plugin``, and before ``FairDMDeleteView`` on a deletion
    page, so its ``handle_no_permission`` wins in the MRO.
    """

    def handle_no_permission(self):
        """Raise a 404 for a non-public record, otherwise refuse as usual."""
        obj = self.base_object
        if obj is not None and obj.visibility != Visibility.PUBLIC:
            model = getattr(self, "registered_model", None)
            kind = model._meta.verbose_name if model is not None else "record"
            raise Http404(f"No {kind} matches the given query.")
        return super().handle_no_permission()


class RecordOwnPageBackFallbackMixin:
    """Send a deletion page's Back control to the record's own page rather than its list.

    List this mixin before ``FairDMDeleteView``, for the same MRO reason as
    :class:`PrivateRecordNotFoundMixin`.
    """

    def get_back_url_fallback(self) -> str:
        """Return the record's own page."""
        return self.base_object.get_absolute_url()
