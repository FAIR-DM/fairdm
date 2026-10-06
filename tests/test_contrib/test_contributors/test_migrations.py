"""Tests for the data migration that turns stored record permissions into contribution levels.

The test database is built from the models, not from migrations, so the migration's function is
run against the historical models of the state just before it, which is what the migration
executor hands it.
"""

import importlib

import pytest
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.test import override_settings
from guardian.models import GroupObjectPermission, UserObjectPermission

from fairdm.contrib.contributors.access import RecordAccess
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Contribution
from fairdm.factories import ContributionFactory, OrganizationFactory, PersonFactory

VIEW, EDIT, MANAGE = (
    ContributionLevel.VIEW,
    ContributionLevel.EDIT,
    ContributionLevel.MANAGE,
)
MIGRATION = "0023_levels_from_stored_permissions"


@pytest.fixture
def upgrade():
    """Run the data step against the historical models, as the executor does."""
    module = importlib.import_module(
        f"fairdm.contrib.contributors.migrations.{MIGRATION}"
    )

    def run():
        with override_settings(MIGRATION_MODULES={}):
            loader = MigrationLoader(None, ignore_no_migrations=True)
            state = loader.project_state(("contributors", MIGRATION), at_end=False)
        module.convert_stored_permissions(state.apps, None)

    return run


@pytest.fixture
def somebody(db):
    return PersonFactory(is_active=True, is_claimed=True, password="x")


def store(user_or_group, codename, record, *, under=None):
    """Store a django-guardian row for a record, under its own type or the one given."""
    content_type = ContentType.objects.get_for_model(under or record)
    permission = Permission.objects.get(content_type=content_type, codename=codename)
    model = (
        GroupObjectPermission
        if isinstance(user_or_group, Group)
        else UserObjectPermission
    )
    field = "group" if isinstance(user_or_group, Group) else "user"
    # Not `create`: guardian's own save refuses a base type's permission for a subtype's record.
    return model.objects.bulk_create(
        [
            model(
                **{field: user_or_group},
                permission=permission,
                content_type=content_type,
                object_pk=str(record.pk),
            )
        ]
    )


def own_level(record, person):
    return RecordAccess(record).own_level(person)


def credit(record, person):
    return Contribution.objects.filter(
        contributor=person,
        content_type=ContentType.objects.get_for_model(
            record.get_real_instance()
            if hasattr(record, "get_real_instance")
            else record
        ),
        object_id=record.pk,
    ).first()


@pytest.mark.django_db
class TestConvertStoredPermissions:
    def test_view_change_and_delete_make_a_manager(
        self, upgrade, record_chain, somebody
    ):
        for codename in ("view_dataset", "change_dataset", "delete_dataset"):
            store(somebody, codename, record_chain.dataset)

        upgrade()

        assert own_level(record_chain.dataset, somebody) == MANAGE

    def test_change_alone_makes_an_editor(self, upgrade, record_chain, somebody):
        store(somebody, "change_dataset", record_chain.dataset)

        upgrade()

        assert own_level(record_chain.dataset, somebody) == EDIT

    def test_view_alone_makes_a_viewer(self, upgrade, record_chain, somebody):
        store(somebody, "view_project", record_chain.project)

        upgrade()

        assert own_level(record_chain.project, somebody) == VIEW

    @pytest.mark.parametrize(
        ("codenames", "level"),
        [
            (["view_dataset", "import_data"], EDIT),
            (["modify_metadata"], EDIT),
            (["change_dataset_metadata"], EDIT),
            (["add_contributor"], MANAGE),
            (["change_dataset_settings"], MANAGE),
            (["can_publish"], MANAGE),
        ],
    )
    def test_every_permission_maps_to_the_level_the_table_gives(
        self, upgrade, record_chain, somebody, codenames, level
    ):
        for codename in codenames:
            store(somebody, codename, record_chain.dataset)

        upgrade()

        assert own_level(record_chain.dataset, somebody) == level

    def test_rights_on_each_kind_of_record_are_read(
        self, upgrade, record_chain, somebody
    ):
        store(somebody, "change_project", record_chain.project)
        store(
            somebody,
            "view_sample",
            record_chain.sample,
            under=record_chain.sample.type_of,
        )
        store(
            somebody,
            "delete_measurement",
            record_chain.measurement,
            under=record_chain.measurement.type_of,
        )

        upgrade()

        assert own_level(record_chain.project, somebody) == EDIT
        assert own_level(record_chain.sample, somebody) == VIEW
        assert own_level(record_chain.measurement, somebody) == MANAGE

    def test_a_person_with_rows_and_no_contribution_is_listed(
        self, upgrade, record_chain, somebody
    ):
        store(somebody, "view_dataset", record_chain.dataset)
        assert credit(record_chain.dataset, somebody) is None

        upgrade()

        listed = credit(record_chain.dataset, somebody)
        assert listed is not None
        assert listed.level == VIEW
        assert listed.roles.count() == 0

    def test_a_new_entry_is_placed_after_the_ones_already_there(
        self, upgrade, record_chain, somebody
    ):
        first = ContributionFactory(content_object=record_chain.dataset)
        store(somebody, "view_dataset", record_chain.dataset)

        upgrade()

        assert credit(record_chain.dataset, somebody).order > first.order

    def test_a_contributor_with_no_rows_gets_the_view_level(
        self, upgrade, record_chain, somebody
    ):
        contribution = ContributionFactory(
            content_object=record_chain.dataset, contributor=somebody
        )

        upgrade()

        contribution.refresh_from_db()
        assert contribution.level == VIEW

    def test_a_level_already_stored_is_kept_when_it_is_higher(
        self, upgrade, record_chain, somebody
    ):
        contribution = ContributionFactory(
            content_object=record_chain.dataset, contributor=somebody, level=MANAGE
        )
        store(somebody, "view_dataset", record_chain.dataset)

        upgrade()

        contribution.refresh_from_db()
        assert contribution.level == MANAGE

    def test_a_level_already_stored_is_raised_when_the_rows_are_higher(
        self, upgrade, record_chain, somebody
    ):
        contribution = ContributionFactory(
            content_object=record_chain.dataset, contributor=somebody, level=VIEW
        )
        store(somebody, "change_dataset", record_chain.dataset)

        upgrade()

        contribution.refresh_from_db()
        assert contribution.level == EDIT

    def test_an_organization_gets_no_level(self, upgrade, record_chain):
        organization = OrganizationFactory()
        contribution = ContributionFactory(
            content_object=record_chain.dataset, contributor=organization
        )

        upgrade()

        contribution.refresh_from_db()
        assert contribution.level is None

    def test_a_member_of_a_group_holding_rows_gets_the_level_they_map_to(
        self, upgrade, record_chain, somebody
    ):
        other = PersonFactory(is_active=True, is_claimed=True, password="x")
        outsider = PersonFactory(is_active=True, is_claimed=True, password="x")
        group = Group.objects.create(name="field team")
        group.user_set.add(somebody, other)
        store(group, "view_dataset", record_chain.dataset)
        store(group, "change_dataset", record_chain.dataset)

        upgrade()

        assert own_level(record_chain.dataset, somebody) == EDIT
        assert own_level(record_chain.dataset, other) == EDIT
        assert own_level(record_chain.dataset, outsider) is None
        assert credit(record_chain.dataset, outsider) is None

    def test_the_higher_of_a_users_rows_and_a_groups_applies(
        self, upgrade, record_chain, somebody
    ):
        group = Group.objects.create(name="field team")
        group.user_set.add(somebody)
        store(group, "delete_dataset", record_chain.dataset)
        store(somebody, "view_dataset", record_chain.dataset)

        upgrade()

        assert own_level(record_chain.dataset, somebody) == MANAGE

    def test_a_registered_subtype_is_read_from_the_base_and_its_own_rows(
        self, upgrade, record_chain, somebody
    ):
        sample = record_chain.sample
        store(somebody, "view_sample", sample, under=sample.type_of)
        store(somebody, "change_rocksample", sample)

        upgrade()

        listed = credit(sample, somebody)
        assert listed.level == EDIT
        assert listed.content_type == ContentType.objects.get_for_model(type(sample))
        assert own_level(sample, somebody) == EDIT

    def test_the_stored_rows_are_gone(self, upgrade, record_chain, somebody):
        group = Group.objects.create(name="field team")
        group.user_set.add(somebody)
        store(somebody, "view_dataset", record_chain.dataset)
        store(group, "view_project", record_chain.project)
        store(somebody, "change_rocksample", record_chain.sample)

        upgrade()

        assert not UserObjectPermission.objects.exists()
        assert not GroupObjectPermission.objects.exists()

    def test_rows_on_something_that_is_not_a_core_record_are_left(
        self, upgrade, record_chain, somebody
    ):
        organization = OrganizationFactory()
        content_type = ContentType.objects.get_for_model(organization)
        permission = Permission.objects.get(
            content_type=content_type, codename="change_organization"
        )
        UserObjectPermission.objects.create(
            user=somebody,
            permission=permission,
            content_type=content_type,
            object_pk=str(organization.pk),
        )

        upgrade()

        assert UserObjectPermission.objects.filter(user=somebody).count() == 1

    def test_a_superuser_is_not_listed(self, upgrade, record_chain):
        admin = PersonFactory(is_active=True, is_superuser=True, password="x")
        store(admin, "view_dataset", record_chain.dataset)

        upgrade()

        assert credit(record_chain.dataset, admin) is None
        assert not UserObjectPermission.objects.exists()

    def test_a_person_without_an_active_account_keeps_what_their_rows_gave(
        self, upgrade, record_chain
    ):
        away = PersonFactory(is_active=False, password="x")
        store(away, "change_dataset", record_chain.dataset)

        upgrade()

        assert RecordAccess(record_chain.dataset).level_of(away) is None
        assert credit(record_chain.dataset, away).level == EDIT

    def test_a_database_with_no_rows_runs_through(self, upgrade, record_chain):
        upgrade()

        assert not UserObjectPermission.objects.exists()

    def test_it_can_run_again_without_changing_anything(
        self, upgrade, record_chain, somebody
    ):
        store(somebody, "change_dataset", record_chain.dataset)
        upgrade()
        before = list(
            Contribution.objects.order_by("pk").values_list("pk", "level", "order")
        )

        upgrade()

        after = list(
            Contribution.objects.order_by("pk").values_list("pk", "level", "order")
        )
        assert after == before


@pytest.mark.django_db
class TestConvertAffiliations:
    def test_an_organization_a_person_is_credited_from_is_listed_on_the_record(
        self, upgrade, record_chain, somebody
    ):
        organization = OrganizationFactory()
        ContributionFactory(
            content_object=record_chain.dataset,
            contributor=somebody,
            affiliation=organization,
        )
        assert credit(record_chain.dataset, organization) is None

        upgrade()

        listed = credit(record_chain.dataset, organization)
        assert listed is not None
        assert listed.level is None

    def test_the_affiliation_is_kept(self, upgrade, record_chain, somebody):
        organization = OrganizationFactory()
        contribution = ContributionFactory(
            content_object=record_chain.dataset,
            contributor=somebody,
            affiliation=organization,
        )

        upgrade()

        contribution.refresh_from_db()
        assert contribution.affiliation == organization

    def test_an_organization_already_listed_is_not_listed_twice(
        self, upgrade, record_chain, somebody
    ):
        organization = OrganizationFactory()
        ContributionFactory(
            content_object=record_chain.dataset, contributor=organization
        )
        ContributionFactory(
            content_object=record_chain.dataset,
            contributor=somebody,
            affiliation=organization,
        )

        upgrade()

        assert (
            Contribution.objects.filter(
                contributor=organization,
                object_id=record_chain.dataset.pk,
            ).count()
            == 1
        )

    def test_an_entry_with_none_is_left_with_none(
        self, upgrade, record_chain, somebody
    ):
        primary = OrganizationFactory()
        from fairdm.factories import AffiliationFactory

        AffiliationFactory(person=somebody, organization=primary, is_primary=True)
        contribution = ContributionFactory(
            content_object=record_chain.dataset, contributor=somebody
        )

        upgrade()

        contribution.refresh_from_db()
        assert contribution.affiliation is None
        assert credit(record_chain.dataset, primary) is None
