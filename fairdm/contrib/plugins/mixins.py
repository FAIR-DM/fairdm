"""Refusal-shape mixins shared by more than one core record's plugin pages.

Companion to :mod:`fairdm.contrib.plugins.access`, which decides *whether* a request
may open a page. These decide what a *refused* request is told, and where its "Back"
control points — both were copy-pasted between ``fairdm.core.dataset.plugins`` and
``fairdm.core.project.plugins`` before this module existed (T089/T090).
"""

from __future__ import annotations

from django.http import Http404

from fairdm.utils.choices import Visibility


class PrivateRecordNotFoundMixin:
    """A record the requester may not act on answers 404, not 403 and not a sign-in
    redirect, unless it is public.

    Without this, ``PermissionRequiredMixin``'s own ``handle_no_permission`` gives a
    signed-in stranger a 403 and redirects an anonymous visitor to sign in — both of
    which confirm a record with this address exists, even though it is private. A
    record's own overview page already refuses to make that confirmation; every
    additional view belonging to it (update, delete, descriptions, …) needs the same
    refusal shape, since each is reachable at its own address regardless of what its
    owner does.

    The 404 message names the kind of record from ``self.registered_model`` — set by
    ``Plugin.get_urls`` on every mount — so a project's pages never say "dataset" and
    vice versa without each page having to state the word itself.

    Must be listed before ``Plugin`` (and, on a deletion page, before
    ``FairDMDeleteView``) in a consumer's base classes: Python resolves
    ``handle_no_permission`` to the first class in the MRO that defines it, and
    ``PermissionRequiredMixin`` — reached through ``Plugin`` — defines it too.
    """

    def handle_no_permission(self):
        obj = self.base_object
        if obj is not None and obj.visibility != Visibility.PUBLIC:
            model = getattr(self, "registered_model", None)
            kind = model._meta.verbose_name if model is not None else "record"
            raise Http404(f"No {kind} matches the given query.")
        return super().handle_no_permission()


class RecordOwnPageBackFallbackMixin:
    """A deletion page's "Back" falls back to the record's own page rather than the
    record's list.

    ``FairDMDeleteView.get_back_url`` reads ``?back``, validates it against the
    current host, and only then falls back to ``get_back_url_fallback()`` — this
    mixin supplies just that last hook, so the query-string handling and its
    open-redirect guard stay written once, upstream. The list fallback
    ``FairDMDeleteView`` itself provides doesn't work for a deletion page that
    carries no ``list`` entry in its own ``directory`` (every core record's
    deletion page): the shell would draw the control as a destination-less link
    instead. From a record's own deletion page, "back" means back to the record
    being considered for deletion.

    Must be listed before ``FairDMDeleteView`` in a consumer's base classes, for the
    same MRO reason as :class:`PrivateRecordNotFoundMixin`.
    """

    def get_back_url_fallback(self) -> str:
        return self.base_object.get_absolute_url()
