"""Admin registration for role groups, protecting the roles the portal ships."""

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from django.utils.translation import gettext_lazy as _

from fairdm.portal_roles import PortalRoles


class ShippedRoleGroupForm(forms.ModelForm):
    """Group form that reports an attempt to rename a shipped role as a field error."""

    class Meta:
        model = Group
        fields = "__all__"

    def clean_name(self):
        """Refuse to rename a shipped role."""
        name = self.cleaned_data["name"]
        if self.instance.pk:
            stored_name = Group.objects.get(pk=self.instance.pk).name
            if stored_name in PortalRoles.shipped_names() and name != stored_name:
                raise ValidationError(
                    _('FairDM requires the "%(name)s" role and refuses to rename it.')
                    % {"name": stored_name}
                )
        return name


admin.site.unregister(Group)


@admin.register(Group)
class ShippedRoleGroupAdmin(DjangoGroupAdmin):
    """Group admin that blocks deleting or renaming a shipped role.

    Groups a portal created for itself are unaffected.
    """

    form = ShippedRoleGroupForm

    def has_delete_permission(self, request, obj=None):
        """Withhold delete permission for a shipped role."""
        if obj is not None and obj.name in PortalRoles.shipped_names():
            return False
        return super().has_delete_permission(request, obj)

    def delete_view(self, request, object_id, extra_context=None):
        """Refuse deleting a shipped role with a 403 that names the role."""
        group = self.get_object(request, object_id)
        if group is not None and group.name in PortalRoles.shipped_names():
            return HttpResponseForbidden(
                _('FairDM requires the "%(name)s" role and refuses to delete it.')
                % {"name": group.name}
            )
        return super().delete_view(request, object_id, extra_context)
