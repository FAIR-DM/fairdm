"""Base form and the manager-only fields mixin shared by the core forms."""

from django.forms import ModelForm


class ManagerOnlyFieldsMixin:
    """Leave the fields that decide who gets into a record out of its form, for anyone who cannot manage it.

    Visibility and the record a record sits under (a project's owner, a dataset's project, a
    sample's or measurement's dataset) change who holds rights over it, so only someone who can
    manage it is offered them. A form for a new record leaves nothing out.

    Attributes:
        manager_only_fields: The names of the fields to leave out.
    """

    manager_only_fields: tuple[str, ...] = ()

    def withhold_manager_only_fields(self, request):
        """Remove the manager-only fields unless the request's user can manage the record.

        Args:
            request: The current request, or None, which counts as someone who cannot manage it.
        """
        from fairdm.contrib.contributors.access import RecordAccess

        user = getattr(request, "user", None)
        if self.instance.pk is None or (
            user is not None and RecordAccess(self.instance).can_manage(user)
        ):
            return
        for name in self.manager_only_fields:
            self.fields.pop(name, None)


class BaseForm(ModelForm):
    """Model form that accepts the request and drops declared fields missing from ``Meta.fields``.

    Args:
        *args: Positional arguments passed to ``ModelForm``.
        **kwargs: Keyword arguments passed to ``ModelForm``. ``request`` is removed first and
            sets ``self.request`` and ``self.user``.
    """

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.user = None
        if self.request:
            self.user = self.request.user

        super().__init__(*args, **kwargs)
        allowed = set(self._meta.fields)
        for name in list(self.fields):
            if name not in allowed:
                del self.fields[name]
