"""
Unit tests for Sample model permissions.

Tests verify that Sample integrates with django-guardian for object-level permissions and
inherits permissions from its parent Dataset - across a concrete specimen type, never the base
``Sample`` record, which cannot be instantiated directly (005-core-samples T030).
"""

import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from fairdm.core.sample.models import Sample
from fairdm.core.utils import assign_perm, remove_perm


@pytest.mark.django_db
class TestSampleDeclaredPermissions:
    """FR-033: every right any check consults must be declared on the record."""

    def test_the_rights_the_dataset_inheritance_map_consults_are_declared(self):
        codenames = set(
            Permission.objects.filter(
                content_type=ContentType.objects.get_for_model(Sample)
            ).values_list("codename", flat=True)
        )
        assert {
            "view_sample",
            "change_sample",
            "delete_sample",
            "add_sample",
            "import_data",
        } <= codenames


@pytest.mark.django_db
class TestSampleDirectPermissions:
    """FR-032: a right granted directly on one specimen holds for that specimen and not another."""

    def test_direct_grant_holds_for_the_granted_specimen(self, rock_sample, user):
        assign_perm("change_sample", user, rock_sample)

        assert user.has_perm("sample.change_sample", rock_sample) is True

    def test_direct_grant_does_not_hold_for_another_specimen(
        self, rock_sample, water_sample, user
    ):
        assign_perm("view_sample", user, rock_sample)

        assert user.has_perm("sample.view_sample", water_sample) is False

    def test_direct_grant_can_be_removed(self, rock_sample, user):
        assign_perm("view_sample", user, rock_sample)
        assert user.has_perm("sample.view_sample", rock_sample) is True

        remove_perm("view_sample", user, rock_sample)
        assert user.has_perm("sample.view_sample", rock_sample) is False


@pytest.mark.django_db
class TestSamplePermissionInheritance:
    """FR-031: rights over a sample derive from rights over its dataset."""

    def test_view_dataset_confers_view_sample(self, rock_sample, user):
        assign_perm("view_dataset", user, rock_sample.dataset)

        assert user.has_perm("sample.view_sample", rock_sample) is True

    def test_change_dataset_confers_change_sample(self, rock_sample, user):
        assign_perm("change_dataset", user, rock_sample.dataset)

        assert user.has_perm("sample.change_sample", rock_sample) is True

    def test_change_dataset_confers_delete_sample(self, rock_sample, user):
        assign_perm("change_dataset", user, rock_sample.dataset)

        assert user.has_perm("sample.delete_sample", rock_sample) is True

    def test_change_dataset_confers_add_sample(self, rock_sample, user):
        assign_perm("change_dataset", user, rock_sample.dataset)

        assert user.has_perm("sample.add_sample", rock_sample) is True

    def test_view_dataset_alone_does_not_confer_change_sample(self, rock_sample, user):
        assign_perm("view_dataset", user, rock_sample.dataset)

        assert user.has_perm("sample.change_sample", rock_sample) is False

    def test_every_sample_in_the_dataset_inherits_the_same_grant(self, dataset, user):
        from fairdm_demo.factories import RockSampleFactory, WaterSampleFactory

        sample1 = RockSampleFactory(dataset=dataset)
        sample2 = WaterSampleFactory(dataset=dataset)

        assign_perm("view_dataset", user, dataset)

        assert user.has_perm("sample.view_sample", sample1) is True
        assert user.has_perm("sample.view_sample", sample2) is True


@pytest.mark.django_db
class TestSampleNoRights:
    """A user holding rights on neither the specimen nor its dataset holds none over it - and the
    check must return False, not raise (research.md R2: guardian raises WrongAppError on a
    specimen instance before this backend's fix)."""

    def test_no_rights_anywhere_refuses_every_right(self, rock_sample, user):
        assert user.has_perm("sample.view_sample", rock_sample) is False
        assert user.has_perm("sample.change_sample", rock_sample) is False
        assert user.has_perm("sample.delete_sample", rock_sample) is False

    def test_a_right_on_a_different_dataset_does_not_leak(self, rock_sample, dataset, user):
        from fairdm.factories import DatasetFactory

        other_dataset = DatasetFactory(project=dataset.project)
        assign_perm("change_dataset", user, other_dataset)

        assert user.has_perm("sample.change_sample", rock_sample) is False


@pytest.mark.django_db
class TestObjectPermissionsSurvive:
    """The shared backend is registered directly, not reached by delegation (D-018) - these are
    the record types that lose their answering backend when the raw one is removed, and nothing
    else in this work would notice if they stopped resolving."""

    def test_dataset_grant_still_resolves(self, dataset, user):
        assign_perm("view_dataset", user, dataset)

        assert user.has_perm("dataset.view_dataset", dataset) is True

    def test_project_grant_still_resolves(self, project, user):
        assign_perm("view_project", user, project)

        assert user.has_perm("project.view_project", project) is True

    def test_organization_grant_still_resolves(self, user):
        from fairdm.factories import OrganizationFactory

        organization = OrganizationFactory()
        assign_perm("view_organization", user, organization)

        assert user.has_perm("contributors.view_organization", organization) is True
