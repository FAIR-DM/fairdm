"""Signal receivers for the contributors app.

Withdrawing a person's rights over an object when their credit on it is removed used to
be a django-lifecycle ``AFTER_DELETE`` hook on ``Contribution``. django-lifecycle runs
that hook from the model instance's own ``delete()``, which ``QuerySet.delete()``
bypasses entirely - a bulk delete never calls each instance's ``delete()``, so the
withdrawal never fired for a credit removed that way (FR-036, design review RECON-002).

``withdraw_rights_on_credit_deletion`` below is a genuine Django ``post_delete`` signal
receiver instead. Django's deletion collector sends ``post_delete`` for every row it
collects regardless of whether the delete started from an instance or a queryset -
connecting a receiver here also disables the collector's "fast delete" fast path (which
skips sending signals when nothing listens for them), so the signal is guaranteed to
fire for both. It covers every path the hook did, so the hook has been removed rather
than left to run a second time alongside it.

``refuse_off_vocabulary_role`` enforces FR-032 for the same structural reason:
``Contribution.clean()`` documents the rule, but Django's ``full_clean()`` never
validates many-to-many data, ``self.roles`` on a saved instance reads what is already
stored rather than what a caller is about to write, and no production write path calls
``full_clean()`` before writing anyway. Every write reaches ``Contribution.roles``
through ``roles.add()`` or ``roles.set()`` (``set()`` decomposes into ``remove()`` +
``add()`` internally - see Django's ``ManyRelatedManager.set()``), so an ``m2m_changed``
receiver on ``pre_add`` is the one place that sees every write before it commits.

``refuse_shipped_role_deletion`` and ``refuse_shipped_role_rename`` protect the four
roles ``fairdm.portal_roles.PortalRoles`` ships (FR-012, FR-013, research R6). A raising
``pre_delete``/``pre_save`` receiver on ``Group`` is this codebase's own idiom for a rule
the model layer cannot hold on its own, and - as with ``refuse_off_vocabulary_role`` above
- it holds for every ORM writer, not only the administration interface. It does not hold
against raw SQL, which the specification already accepts. ``refuse_shipped_role_rename``
fires only for an existing row: a brand new ``Group`` instance has no name to compare
against yet, and ``PortalRoles.reconcile()`` itself writes through
``Group.objects.get_or_create()``, whose creation branch this receiver is installed
against and must not refuse.
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from fairdm.utils.permissions import remove_all_model_perms


def withdraw_rights_on_credit_deletion(sender, instance, **kwargs):
    """Withdraw a person contributor's object-level rights over an object when their
    credit on it is deleted - including through a queryset delete (FR-036).

    ``content_object`` is ``None`` when the credited object is what is being deleted and
    the credit is following it down the cascade: the collector removes the project or
    dataset row first, so the generic reference no longer resolves by the time this
    fires. There is no object left to hold a right over, so there is nothing to
    withdraw. Rights recorded against the deleted object are cleared by
    ``clean_orphan_obj_perms``, which is where they belong - every object deletion
    leaves them behind, credited or not.
    """
    from .models import Person

    if instance.content_object is None:
        return

    if isinstance(instance.contributor, Person):
        remove_all_model_perms(instance.contributor, instance.content_object)


def refuse_off_vocabulary_role(sender, action, reverse, model, pk_set, **kwargs):
    """Refuse a role drawn from any vocabulary other than the framework's roles
    vocabulary before it is written to ``Contribution.roles`` (FR-032, design review
    SPEC-001).

    This is the backstop, not the first line of defence. A person filling in a form -
    the roles field on ``MeasurementContributionInline``, ``SampleContributionInline``
    or ``UpdateContributionForm`` - hits the vocabulary restriction each narrows its
    ``roles`` queryset to first, as an ordinary field validation error attached to the
    form. This receiver exists for every write path that never goes through one of
    those forms at all - a fixture, a management command, a raw ``roles.add()`` call -
    where there is no form to narrow and nothing else stops an off-vocabulary concept
    reaching the through table. Raising here, uncaught, is acceptable for that kind of
    caller; it would not be for a form submission, which is why the admin surfaces
    narrow their querysets instead of relying on this alone.

    Connected to ``m2m_changed`` for ``Contribution.roles.through`` with
    ``action="pre_add"``. That single action covers both ``roles.add()`` directly and
    the additive half of ``roles.set()`` - Django's ``ManyRelatedManager.set()``
    resolves into a ``remove()`` for ids no longer wanted and an ``add()`` for the new
    ones, and it is that internal ``add()`` that sends this signal. Raising here happens
    before Django's ``bulk_create`` of the through rows runs, and the surrounding
    ``add()``/``set()`` call is itself inside a transaction, so nothing in the same call
    is written - not the offending role, and not any other role passed alongside it.

    ``reverse=True`` would mean the write came from the concept side (a
    ``Concept`` instance's own manager adding itself to contributions).
    ``ConceptManyToManyField`` (``RelatedConceptMixin.__init__``) hard-codes
    ``related_name="+"`` for every field it creates, including ``Contribution.roles``,
    so no reverse accessor exists at all. That direction is not reachable through the
    ORM's public surface, so it is left unhandled here rather than guarded against.
    """
    if action != "pre_add" or reverse or not pk_set:
        return

    from .models import CONTRIBUTION_ROLES_VOCABULARY_MESSAGE

    if (
        model.objects.filter(pk__in=pk_set)
        .exclude(vocabulary__name="fairdm-roles")
        .exists()
    ):
        raise ValidationError(CONTRIBUTION_ROLES_VOCABULARY_MESSAGE)


def refuse_shipped_role_deletion(sender, instance, **kwargs):
    """Refuse to delete a shipped portal role through the ORM (FR-012, research R6).

    Connected to ``pre_delete`` for ``Group``, with no distinction between an
    instance's own ``delete()`` and a bulk ``QuerySet.delete()`` - both send
    ``pre_delete`` for every row once a receiver is connected for the model, which
    also disables the collector's fast-delete path (see the module docstring's
    ``withdraw_rights_on_credit_deletion`` note for the same mechanism).
    """
    from fairdm.portal_roles import PortalRoles

    if instance.name in PortalRoles.shipped_names():
        raise ValidationError(
            _('FairDM requires the "%(name)s" role and refuses to delete it.')
            % {"name": instance.name}
        )


def refuse_shipped_role_rename(sender, instance, **kwargs):
    """Refuse to rename a shipped portal role through the ORM (FR-013, research R6).

    Fires only for an existing row: ``instance._state.adding`` is ``True`` for a
    ``Group`` that has never been saved, which is the case for both a portal's own
    new group and the row ``PortalRoles.reconcile()`` creates through
    ``Group.objects.get_or_create()`` - this receiver must not refuse either. For an
    existing row, the name stored in the database, not the value ``instance`` is
    about to write, is what identifies a shipped role: comparing ``instance.name``
    against the declared names would miss a rename *away* from a shipped name and
    would refuse one that merely resaves it unchanged.
    """
    if instance._state.adding:
        return

    from django.contrib.auth.models import Group

    from fairdm.portal_roles import PortalRoles

    try:
        stored_name = Group.objects.get(pk=instance.pk).name
    except Group.DoesNotExist:
        return

    if stored_name in PortalRoles.shipped_names() and instance.name != stored_name:
        raise ValidationError(
            _('FairDM requires the "%(name)s" role and refuses to rename it.')
            % {"name": stored_name}
        )
