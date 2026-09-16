# Note: Waffle models (Flag, Sample, Switch) are registered by django-waffle
# when WAFFLE_ENABLE_ADMIN_PAGES is True (default). The waffle admin classes
# provide more features than basic ModelAdmin (custom actions, logging, etc.)

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from fairdm.portal_roles import PortalRoles


class ShippedRoleGroupForm(forms.ModelForm):
    """T022/T023: turns the ``pre_save`` guard's raise (T021) into a field error naming
    the role, so an administrator renaming a shipped role sees why rather than a 500 -
    the receiver stays the enforcement (research R6) and never actually fires through
    this form, since the rename is caught here first."""

    class Meta:
        model = Group
        fields = "__all__"

    def clean_name(self):
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
    """FR-012/FR-013: no delete action or button for a shipped role, and a field
    error rather than a server error for a rename attempt. FR-014: a group a portal
    created for itself is unaffected either way."""

    form = ShippedRoleGroupForm

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.name in PortalRoles.shipped_names():
            return False
        return super().has_delete_permission(request, obj)
