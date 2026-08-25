"""The dataset's update page: an extra view of its ``Overview`` registration (014 plan P1, P3).

T034 - the update page is reachable at a stable address identifying the dataset, requiring
       sign-in.
T035 - it refuses a user who does not hold `dataset.change_dataset` on the record, and does not
       disclose a private dataset's existence to a user with no grant at all.
T036 - it covers exactly image, name, project, license, reference and visibility.
T037 - each of those attributes persists when changed.
T038 - the project field offers only projects the researcher may use.
T039 - identifiers are added, changed and removed through the shared row-set facility.
T040 - collection start and collection end dates are set, changed and removed the same way.
T041 - a collection end earlier than the collection start is refused.
T042 - an identifier value already recorded against another record is refused, and nothing in
       the submission is saved.
T043 - the page offers no descriptions, keywords, tags or contributors.
T045 - a successful submission arrives at the dataset's own page.
T046 - identifiers and dates are edited through `mvp.views.inline.InlinesMixin`, not a
       hand-written equivalent.
T047 - the form declares `helper_attrs = {"form_tag": False}` so the page renders one form
       element, not one nested inside another.
T048 - the descriptions page is reachable at a stable address of its own, identifying the
       dataset by its identifier, and requires the visitor to be signed in.
T049 - it refuses a user who does not hold permission to change that dataset.
T050 - it offers one editable area per description type in the dataset description vocabulary,
       labelled with the type's name and explained by its definition.
T051 - saving text into an area records a description of that type; a dataset never holds more
       than one description of any type.
T052 - clearing an area removes that description.
T053 - an area left empty creates nothing.
T054 - a successful submission arrives at the dataset's own page.
T055 - the page is built on the vocabulary-driven form (T009), not the row-based editor it used
       to be registered on.

Mirrors `tests/test_core/test_project/test_plugins.py` and
`tests/test_core/test_project/test_views.py`'s `TestAttributesIdentifierRowSet` /
`TestAttributesDateRowSet`, adapted to the dataset's own field set and identifier vocabulary
(DOI alone, `fairdm/core/dataset/models.py:480`). The descriptions test classes below mirror
`tests/test_core/test_project/test_plugins.py`'s `TestDescriptions*` classes, adapted to the
dataset's own vocabulary and to the not-found visibility rule 014 US-3 established for private
datasets (`fairdm.core.dataset.plugins.Update.handle_no_permission`), which project's reference
implementation does not need.
"""

import re

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse
from guardian.shortcuts import assign_perm
from licensing.models import License

from fairdm import plugins
from fairdm.contrib.plugins.access import can_open
from fairdm.contrib.plugins.base import Plugin
from fairdm.core.dataset.forms import DatasetForm
from fairdm.core.dataset.models import Dataset, DatasetDescription
from fairdm.core.dataset.plugins import Delete, Descriptions, Overview, Update
from fairdm.core.descriptions import VocabularyDescriptionsForm
from fairdm.factories import (
    DatasetDateFactory,
    DatasetFactory,
    DatasetIdentifierFactory,
    LiteratureItemFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility

pytestmark = pytest.mark.django_db


def _request_for(user, path="/"):
    request = RequestFactory().get(path)
    request.user = user
    return request


def _dataset_field_data(dataset):
    """The attributes form's own field values, unchanged from `dataset`."""
    return {
        "name": dataset.name,
        "project": dataset.project_id or "",
        "license": dataset.license_id,
        "visibility": dataset.visibility,
    }


def _identifier_management_data(total=0, initial=0):
    """Management-form boilerplate for the identifiers row set (`DatasetIdentifierInline`,
    prefix `identifiers` from `AbstractIdentifier.Meta.default_related_name`)."""
    return {
        "identifiers-TOTAL_FORMS": str(total),
        "identifiers-INITIAL_FORMS": str(initial),
        "identifiers-MIN_NUM_FORMS": "0",
        "identifiers-MAX_NUM_FORMS": "1000",
    }


def _date_management_data(total=0, initial=0):
    """Management-form boilerplate for the dates row set (`DatasetDatesInline`, prefix `dates`
    from `AbstractDate.Meta.default_related_name`)."""
    return {
        "dates-TOTAL_FORMS": str(total),
        "dates-INITIAL_FORMS": str(initial),
        "dates-MIN_NUM_FORMS": "0",
        "dates-MAX_NUM_FORMS": "1000",
    }


class TestUpdateIsAnExtraViewOfTheOverview:
    """T046 - identifiers and dates are edited through the shared row-set facility, wired onto
    the update page as `mvp.views.inline.InlinesMixin`, not a hand-written formset."""

    def test_the_update_page_resolves_as_an_extra_view_of_the_overview(self):
        dataset = DatasetFactory()
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        assert url.endswith(f"{dataset.uuid}/update/")

    def test_the_dataset_menu_carries_no_entry_for_update(self):
        plugins.registry.get_urls_for_model(Dataset)
        menu = plugins.registry.get_plugin_menu_for_model(Dataset)
        labels = [item.extra_context.get("label") for item in menu.children]
        assert "Update dataset" not in labels

    def test_update_uses_the_shared_inlines_mixin_not_a_hand_written_formset(self):
        from mvp.views.inline import InlineFormSet, InlinesMixin

        assert issubclass(Update, InlinesMixin)
        assert len(Update.inlines) == 2
        for declaration in Update.inlines:
            assert issubclass(declaration, InlineFormSet)


class TestUpdateStatesItsOwnPermission:
    """T035/FR-024 - an additional view inherits its owner's `check` but never its
    `permission` (`fairdm/contrib/plugins/access.py` `can_open`), so this page states its own,
    matching `fairdm.core.project.plugins.Update`."""

    def test_refuses_a_signed_in_user_without_change_permission(self):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        request = _request_for(user)
        assert can_open(Update, request, dataset) is False

    def test_admits_a_user_holding_change_permission(self):
        dataset = DatasetFactory()
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        request = _request_for(user)
        assert can_open(Update, request, dataset) is True

    def test_refuses_an_anonymous_request(self):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        request = _request_for(AnonymousUser())
        assert can_open(Update, request, dataset) is False


class TestUpdatePageDoesNotDiscloseAPrivateDataset:
    """T035 - the update page's own visibility rule (`visible_to_holder_of`), not merely its
    permission, since inheriting `Overview`'s `check` does not carry to an additional view."""

    def test_a_model_level_holder_with_no_record_level_grant_is_refused(self, client):
        """A user holding `dataset.change_dataset` at the model level and no grant at all on
        this particular private dataset is refused with 404, matching `Overview` — the scenario
        `visible_to_holder_of` exists to still admit is a *record-level* grant."""
        from django.contrib.auth.models import Permission

        dataset = DatasetFactory()  # private, per the model default
        user = UserFactory()
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="dataset", codename="change_dataset"
            )
        )
        client.force_login(user)

        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        assert response.status_code == 404

    def test_a_model_level_holder_with_view_rights_is_admitted(self, client):
        """The same model-level holder, once also granted `view_dataset` at record level (as a
        real grant path always provides — dataset creation grants all five rights at once), is
        admitted: the *permission* check still asks twice, model level then record
        (`fairdm/contrib/plugins/access.py` `has_perm`)."""
        from django.contrib.auth.models import Permission

        dataset = DatasetFactory()
        user = UserFactory()
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="dataset", codename="change_dataset"
            )
        )
        assign_perm("view_dataset", user, dataset)
        client.force_login(user)

        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        assert response.status_code == 200


class TestUpdatePageFieldSet:
    """T036/T043/FR-025/FR-031 - the update page covers exactly the dataset's own attributes,
    and offers none of descriptions, keywords, tags or contributors."""

    ATTRIBUTES_FIELDS = {"image", "name", "project", "license", "reference", "visibility"}
    EXCLUDED_FIELDS = {"descriptions", "keywords", "tags", "contributors"}

    def test_the_rendered_form_offers_exactly_the_attributes_field_set(self, client):
        dataset = DatasetFactory()
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.get(url)

        assert response.status_code == 200
        assert set(response.context["form"].fields) == self.ATTRIBUTES_FIELDS

    def test_the_declared_form_class_offers_no_excluded_field(self):
        fields = set(DatasetForm.Meta.fields)
        assert not fields & self.EXCLUDED_FIELDS

    def test_exactly_one_page_offers_the_attributes_field_set(self):
        """Mirrors `tests/test_core/test_project/test_plugins.py`'s
        `TestExactlyOnePageOffersTheProjectsOwnAttributes` - no second registered page against
        `Dataset` overlaps this field set."""
        pages = []
        for plugin_cls, _kwargs in plugins.registry.get_plugins_for_model(Dataset):
            pages.append(plugin_cls)
            pages.extend(plugin_cls.get_extra_views())

        offering_pages = []
        for page in pages:
            form_class = getattr(page, "form_class", None)
            fields = getattr(getattr(form_class, "Meta", None), "fields", None)
            if fields and self.ATTRIBUTES_FIELDS & set(fields):
                offering_pages.append(page)

        assert offering_pages == [Update]


class TestUpdatePageAttributesPersist:
    """T037/FR-025 - each attribute the page covers is changed and submitted, and each
    persists, asserted one field at a time against a fresh copy of the same starting dataset."""

    def test_changing_name_project_license_visibility_and_reference_each_persists(
        self, client
    ):
        original_project = None
        license_a = License.objects.get_or_create(name="CC BY 4.0")[0]
        license_b = License.objects.get_or_create(name="CC0 1.0")[0]
        reference = LiteratureItemFactory()
        user = UserFactory()

        from fairdm.factories import ProjectFactory

        changed_project = ProjectFactory()
        changed_project.add_contributor(user)

        changes = {
            "name": "Changed Name",
            "license": license_b.pk,
            "visibility": Visibility.PUBLIC,
            "reference": reference.pk,
            "project": changed_project.pk,
        }

        for field, new_value in changes.items():
            dataset = DatasetFactory(
                name="Original Name",
                license=license_a,
                visibility=Visibility.PRIVATE,
                project=original_project,
            )
            assign_perm("change_dataset", user, dataset)
            client.force_login(user)
            url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
            data = {
                **_dataset_field_data(dataset),
                field: new_value,
                **_identifier_management_data(),
                **_date_management_data(),
            }

            response = client.post(url, data=data)

            assert response.status_code == 302, response.context["form"].errors
            dataset.refresh_from_db()
            if field in ("project", "license", "reference"):
                assert getattr(dataset, f"{field}_id") == new_value
            else:
                assert getattr(dataset, field) == new_value

    def test_submitting_an_empty_name_reports_an_error_and_saves_nothing(self, client):
        """FR-032 - a dataset cannot be saved without a name."""
        dataset = DatasetFactory(name="Original Name", project=None)
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                "name": "",
                **_identifier_management_data(),
                **_date_management_data(),
            },
        )

        assert response.status_code == 200
        assert "name" in response.context["form"].errors
        dataset.refresh_from_db()
        assert dataset.name == "Original Name"


class TestUpdatePageProjectField:
    """T038/FR-026 - the project field offers only projects the researcher may use, on the same
    terms as the creation page (`DatasetForm.__init__`, `request.user.projects.all()`)."""

    def test_the_project_field_is_narrowed_to_the_researchers_own_projects(self, client):
        from fairdm.contrib.contributors.models import Contribution
        from fairdm.factories import ProjectFactory

        dataset = DatasetFactory()
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)

        own_project = ProjectFactory(name="Researcher's Own Project")
        other_project = ProjectFactory(name="Someone Else's Project")
        Contribution.add_to(user, own_project, roles=["Contributor"])

        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        project_queryset = response.context["form"].fields["project"].queryset
        assert own_project in project_queryset
        assert other_project not in project_queryset


@pytest.mark.django_db
class TestAttributesIdentifierRowSet:
    """T039/FR-027/FR-030 - the update page's identifier row set: existing identifiers presented
    one row each, added, changed, removed and checked for collisions against other records."""

    def test_existing_identifiers_are_presented_one_row_each_with_no_blank_row_beyond_them(
        self, client
    ):
        dataset = DatasetFactory(name="Has Identifier", project=None)
        DatasetIdentifierFactory(related=dataset, type="DOI", value="10.1/existing")
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.get(url)

        assert response.status_code == 200
        formsets = {formset.prefix: formset for formset in response.context["inlines"]}
        identifier_formset = formsets["identifiers"]
        assert identifier_formset.initial_form_count() == 1
        assert len(identifier_formset.forms) == 1

    def test_adding_an_identifier_of_a_chosen_type_records_it_against_the_dataset(
        self, client
    ):
        dataset = DatasetFactory(name="No Identifiers Yet", project=None)
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                **_identifier_management_data(total=1, initial=0),
                **_date_management_data(),
                "identifiers-0-type": "DOI",
                "identifiers-0-value": "10.1/new-identifier",
            },
        )

        assert response.status_code == 302, response.context["form"].errors
        assert dataset.identifiers.filter(
            type="DOI", value="10.1/new-identifier"
        ).exists()

    def test_changing_an_existing_identifiers_value_persists(self, client):
        dataset = DatasetFactory(name="Has Identifier", project=None)
        identifier = DatasetIdentifierFactory(
            related=dataset, type="DOI", value="10.1/original"
        )
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                **_identifier_management_data(total=1, initial=1),
                **_date_management_data(),
                "identifiers-0-id": identifier.pk,
                "identifiers-0-type": "DOI",
                "identifiers-0-value": "10.1/changed",
            },
        )

        assert response.status_code == 302, response.context["form"].errors
        identifier.refresh_from_db()
        assert identifier.value == "10.1/changed"

    def test_removing_an_identifier_row_deletes_it_from_the_dataset(self, client):
        dataset = DatasetFactory(name="Has Identifier", project=None)
        identifier = DatasetIdentifierFactory(
            related=dataset, type="DOI", value="10.1/to-remove"
        )
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                **_identifier_management_data(total=1, initial=1),
                **_date_management_data(),
                "identifiers-0-id": identifier.pk,
                "identifiers-0-type": "DOI",
                "identifiers-0-value": "10.1/to-remove",
                "identifiers-0-DELETE": "on",
            },
        )

        assert response.status_code == 302, response.context["form"].errors
        assert not dataset.identifiers.filter(pk=identifier.pk).exists()

    def test_a_value_already_recorded_against_a_different_dataset_is_refused(self, client):
        """T042/FR-030 - the collision is reported on the field, and nothing in the submission
        is saved, including the dataset's own attribute changes in the same submission
        (`AbstractIdentifier.clean()`, `fairdm/core/abstract.py`, checks `value` across every
        concrete subclass)."""
        other_dataset = DatasetFactory(name="Other Dataset")
        DatasetIdentifierFactory(related=other_dataset, type="DOI", value="10.1/taken")
        dataset = DatasetFactory(name="Original Name", project=None)
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                "name": "Renamed",
                **_identifier_management_data(total=1, initial=0),
                **_date_management_data(),
                "identifiers-0-type": "DOI",
                "identifiers-0-value": "10.1/taken",
            },
        )

        assert response.status_code == 200
        formsets = {formset.prefix: formset for formset in response.context["inlines"]}
        assert "value" in formsets["identifiers"].forms[0].errors
        assert not dataset.identifiers.filter(value="10.1/taken").exists()
        dataset.refresh_from_db()
        assert dataset.name == "Original Name"


@pytest.mark.django_db
class TestAttributesDateRowSet:
    """T040/T041/FR-028/FR-029 - the update page's date row set, built from
    `DatasetDatesInline` (`fairdm/core/dataset/plugins.py`), which pairs the shared
    `DatasetDateInline` declaration with the date-ordering rule parameterised on
    `DatasetDate.START_TYPE`/`END_TYPE`."""

    def test_existing_dates_are_presented_one_row_each_with_no_blank_row_beyond_them(
        self, client
    ):
        dataset = DatasetFactory(name="Has Date", project=None)
        DatasetDateFactory(related=dataset, type="CollectionStart", value="2020-01-01")
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.get(url)

        assert response.status_code == 200
        formsets = {formset.prefix: formset for formset in response.context["inlines"]}
        date_formset = formsets["dates"]
        assert date_formset.initial_form_count() == 1
        assert len(date_formset.forms) == 1

    def test_adding_a_date_of_a_chosen_type_records_it_against_the_dataset(self, client):
        dataset = DatasetFactory(name="No Dates Yet", project=None)
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                **_identifier_management_data(),
                **_date_management_data(total=1, initial=0),
                "dates-0-type": "CollectionStart",
                "dates-0-value": "2020-01-01",
            },
        )

        assert response.status_code == 302, response.context["form"].errors
        assert dataset.dates.filter(type="CollectionStart", value="2020-01-01").exists()

    def test_changing_an_existing_dates_value_persists(self, client):
        dataset = DatasetFactory(name="Has Date", project=None)
        date = DatasetDateFactory(
            related=dataset, type="CollectionStart", value="2020-01-01"
        )
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                **_identifier_management_data(),
                **_date_management_data(total=1, initial=1),
                "dates-0-id": date.pk,
                "dates-0-type": "CollectionStart",
                "dates-0-value": "2021-06-15",
            },
        )

        assert response.status_code == 302, response.context["form"].errors
        date.refresh_from_db()
        assert str(date.value) == "2021-06-15"

    def test_removing_a_date_row_deletes_it_from_the_dataset(self, client):
        dataset = DatasetFactory(name="Has Date", project=None)
        date = DatasetDateFactory(
            related=dataset, type="CollectionStart", value="2020-01-01"
        )
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                **_identifier_management_data(),
                **_date_management_data(total=1, initial=1),
                "dates-0-id": date.pk,
                "dates-0-type": "CollectionStart",
                "dates-0-value": "2020-01-01",
                "dates-0-DELETE": "on",
            },
        )

        assert response.status_code == 302, response.context["form"].errors
        assert not dataset.dates.filter(pk=date.pk).exists()

    def test_a_backwards_pair_both_newly_added_is_refused_and_saves_nothing(self, client):
        """T041 - a collection end earlier than the collection start, both submitted as new
        rows in the same submission, is refused by the formset-level rule
        (`date_ordering_formset`) - a per-row check alone would see neither, since each looks
        its sibling up in the database and finds no unsaved sibling."""
        dataset = DatasetFactory(name="Backwards Pair", project=None)
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                **_identifier_management_data(),
                **_date_management_data(total=2, initial=0),
                "dates-0-type": "CollectionStart",
                "dates-0-value": "2020-06-01",
                "dates-1-type": "CollectionEnd",
                "dates-1-value": "2010-01-01",
            },
        )

        assert response.status_code == 200
        formsets = {formset.prefix: formset for formset in response.context["inlines"]}
        assert formsets["dates"].non_form_errors()
        assert not dataset.dates.exists()

    def test_a_backwards_pair_with_the_start_already_stored_is_refused_and_saves_nothing(
        self, client
    ):
        """T041 - here the per-row model check (`DatasetDate.clean()`) already catches it,
        since the sibling is in the database."""
        dataset = DatasetFactory(name="Backwards Pair", project=None)
        start = DatasetDateFactory(
            related=dataset, type="CollectionStart", value="2020-06-01"
        )
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                **_identifier_management_data(),
                **_date_management_data(total=2, initial=1),
                "dates-0-id": start.pk,
                "dates-0-type": "CollectionStart",
                "dates-0-value": "2020-06-01",
                "dates-1-type": "CollectionEnd",
                "dates-1-value": "2010-01-01",
            },
        )

        assert response.status_code == 200
        formsets = {formset.prefix: formset for formset in response.context["inlines"]}
        assert not formsets["dates"].is_valid()
        assert not dataset.dates.filter(type="CollectionEnd").exists()

    def test_a_start_date_with_no_end_date_is_accepted(self, client):
        dataset = DatasetFactory(name="Start Only", project=None)
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                **_identifier_management_data(),
                **_date_management_data(total=1, initial=0),
                "dates-0-type": "CollectionStart",
                "dates-0-value": "2020-06-01",
            },
        )

        assert response.status_code == 302, response.context["form"].errors
        assert dataset.dates.filter(type="CollectionStart", value="2020-06-01").exists()


class TestAttributesSaveIsOneAtomicSubmission:
    """The attributes page saves the parent and every row set inside one transaction
    (`mvp.views.inline.InlinesMixin.form_valid`): an invalid row anywhere refuses the whole
    submission, including changes to the dataset's own fields."""

    def test_an_invalid_identifier_row_blocks_the_datasets_own_field_changes_too(self, client):
        dataset = DatasetFactory(name="Original Name", project=None)
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                "name": "Renamed",
                **_identifier_management_data(total=1, initial=0),
                **_date_management_data(),
                "identifiers-0-type": "DOI",
                "identifiers-0-value": "",
            },
        )

        assert response.status_code == 200
        assert dataset.identifiers.count() == 0
        dataset.refresh_from_db()
        assert dataset.name == "Original Name"


class TestASuccessfulSubmissionRedirectsToTheDatasetsOwnPage:
    """T045/FR-033 - on successful submission the researcher arrives at the dataset's page."""

    def test_the_redirect_target_is_the_datasets_own_overview_url(self, client):
        dataset = DatasetFactory(name="Original Name", project=None)
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                "name": "Renamed",
                **_identifier_management_data(),
                **_date_management_data(),
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("dataset:overview", kwargs={"uuid": dataset.uuid})


class TestUpdatePageEmitsExactlyOneFormElement:
    """T047/FR-025 - `DatasetForm.Meta.helper_attrs = {"form_tag": False}` stops the shared
    render tag emitting a second `<form>` inside the one the page has already opened."""

    def test_the_form_declares_no_form_tag(self):
        # `BaseMetaClass` pops `helper_attrs` off `Meta` at class-creation time onto
        # `_custom_conf`, so it is asserted there, not on `Meta` itself.
        assert DatasetForm._custom_conf["helper_attrs"] == {"form_tag": False}
        form = DatasetForm()
        assert form.helper.form_tag is False

    def test_the_rendered_page_carries_exactly_one_form_element(self, client):
        dataset = DatasetFactory()
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert len(re.findall(r"<form[ >]", content)) == 1


@pytest.mark.django_db
class TestDescriptionsIsAnExtraViewNotARegistrationOfItsOwn:
    """T048 — the descriptions page is an additional view belonging to ``Overview``, exactly
    like ``Update``, rather than the standalone registration it used to be (014 plan P7,
    mirrors ``fairdm.core.project.plugins.Descriptions``)."""

    def test_reversed_by_name_it_resolves_at_an_address_keyed_by_the_datasets_identifier(
        self, public_dataset
    ):
        url = reverse(
            "dataset:overview-descriptions", kwargs={"uuid": public_dataset.uuid}
        )
        assert url == f"/datasets/{public_dataset.uuid}/descriptions/"

    def test_an_anonymous_visitor_is_redirected_to_sign_in(self, client, public_dataset):
        url = reverse(
            "dataset:overview-descriptions", kwargs={"uuid": public_dataset.uuid}
        )
        response = client.get(url)
        assert response.status_code == 302
        assert reverse("account_login") in response.url


@pytest.mark.django_db
class TestDescriptionsPageStatesItsOwnPermission:
    """T049 — an additional view inherits its owner's ``check`` but never its ``permission``
    (``fairdm/contrib/plugins/access.py`` ``can_open``), so this page states its own, matching
    ``Update`` and ``fairdm.core.project.plugins.Descriptions``."""

    def test_refuses_a_signed_in_user_without_change_permission(
        self, public_dataset, user_with_no_permission
    ):
        request = _request_for(user_with_no_permission)
        assert can_open(Descriptions, request, public_dataset) is False

    def test_admits_a_user_holding_change_permission(self, user_with_change_permission):
        request = _request_for(user_with_change_permission)
        assert (
            can_open(Descriptions, request, user_with_change_permission.dataset) is True
        )

    def test_refuses_an_anonymous_request(self, public_dataset):
        request = _request_for(AnonymousUser())
        assert can_open(Descriptions, request, public_dataset) is False


@pytest.mark.django_db
class TestDescriptionsPageDoesNotDiscloseAPrivateDataset:
    """014 US-3 established that a private dataset answers not-found rather than a permission
    refusal or a sign-in redirect at every one of its addresses
    (``fairdm.core.dataset.plugins.Update.handle_no_permission``). This page carries the same
    rule so it does not become a second existence oracle for embargoed metadata alongside the
    dataset's own page and its update page."""

    def test_a_model_level_holder_with_no_record_level_grant_is_refused(self, client):
        from django.contrib.auth.models import Permission

        dataset = DatasetFactory()  # private, per the model default
        user = UserFactory()
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="dataset", codename="change_dataset"
            )
        )
        client.force_login(user)

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        assert response.status_code == 404

    def test_a_model_level_holder_with_view_rights_is_admitted(self, client):
        from django.contrib.auth.models import Permission

        dataset = DatasetFactory()
        user = UserFactory()
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="dataset", codename="change_dataset"
            )
        )
        assign_perm("view_dataset", user, dataset)
        client.force_login(user)

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        assert response.status_code == 200

    def test_an_anonymous_visitor_to_a_private_dataset_gets_not_found(self, client):
        dataset = DatasetFactory()  # private, per the model default
        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestDescriptionsPageOffersOneAreaPerVocabularyType:
    """T050 — for a dataset with no descriptions, the page offers exactly one empty area per
    concept in ``DatasetDescription.VOCABULARY``, the count read from the vocabulary itself
    rather than written as a literal."""

    def test_the_field_set_matches_the_vocabulary_exactly(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert list(form.fields) == list(DatasetDescription.VOCABULARY.values)

    def test_every_area_starts_empty_for_a_dataset_with_no_descriptions(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert all(field.initial in (None, "") for field in form)


@pytest.mark.django_db
class TestDescriptionsPageAreasAreLabelledFromTheVocabulary:
    """T050 — each area is labelled with its concept's name and carries that concept's
    definition as help text, asserted against the vocabulary's own label and definition rather
    than a copied string."""

    def test_the_first_areas_label_and_help_text_match_its_concept(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        first_type = DatasetDescription.VOCABULARY.values[0]
        concept = DatasetDescription.VOCABULARY.get_concept(first_type)

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert form.fields[first_type].label == concept.label()
        assert form.fields[first_type].help_text == concept.definition()


@pytest.mark.django_db
class TestSavingTextIntoOneAreaRecordsOnlyThatType:
    """T051 — saving text into exactly one area records one description of that type and
    creates no description of any other type."""

    def test_saving_one_area_creates_exactly_one_description_of_that_type(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        first_type = DatasetDescription.VOCABULARY.values[0]

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        client.post(url, data={first_type: "Some abstract text."})

        assert DatasetDescription.objects.filter(related=dataset).count() == 1
        row = DatasetDescription.objects.get(related=dataset)
        assert row.type == first_type
        assert row.value == "Some abstract text."


@pytest.mark.django_db
class TestExistingDescriptionsShowInTheirOwnArea:
    def test_the_existing_description_appears_in_its_own_area_and_others_stay_empty(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        first_type, second_type = DatasetDescription.VOCABULARY.values[:2]
        DatasetDescription.objects.create(
            related=dataset, type=first_type, value="Existing abstract."
        )

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert form.fields[first_type].initial == "Existing abstract."
        assert form.fields[second_type].initial in (None, "")


@pytest.mark.django_db
class TestEditingAnExistingDescriptionPersists:
    def test_the_changed_text_persists(self, client, user_with_change_permission):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        first_type = DatasetDescription.VOCABULARY.values[0]
        row = DatasetDescription.objects.create(
            related=dataset, type=first_type, value="Original text."
        )

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        client.post(url, data={first_type: "Changed text."})

        row.refresh_from_db()
        assert row.value == "Changed text."
        assert DatasetDescription.objects.filter(related=dataset).count() == 1


@pytest.mark.django_db
class TestRepeatSubmissionNeverDuplicatesAType:
    """T051 — a dataset never holds two descriptions of the same type through this page, even
    across repeated submissions to the same area."""

    def test_submitting_the_same_area_three_times_leaves_exactly_one_row(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        first_type = DatasetDescription.VOCABULARY.values[0]

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        client.post(url, data={first_type: "First."})
        client.post(url, data={first_type: "Second."})
        client.post(url, data={first_type: "Third."})

        assert (
            DatasetDescription.objects.filter(related=dataset, type=first_type).count()
            == 1
        )
        assert (
            DatasetDescription.objects.get(related=dataset, type=first_type).value
            == "Third."
        )


@pytest.mark.django_db
class TestClearingAnAreaRemovesTheDescription:
    """T052 — clearing an area and submitting removes that description from the dataset."""

    def test_clearing_the_area_deletes_the_row(self, client, user_with_change_permission):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        first_type = DatasetDescription.VOCABULARY.values[0]
        DatasetDescription.objects.create(
            related=dataset, type=first_type, value="Existing text."
        )

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        client.post(url, data={first_type: ""})

        assert not DatasetDescription.objects.filter(
            related=dataset, type=first_type
        ).exists()


@pytest.mark.django_db
class TestEmptyAndWhitespaceOnlyAreasCreateNothing:
    """T053 — an area left empty creates nothing, and an area containing only whitespace is
    treated as empty: nothing created, and any row already stored for that type removed."""

    def test_leaving_an_area_empty_creates_no_description(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        client.post(url, data={})

        assert not DatasetDescription.objects.filter(related=dataset).exists()

    def test_whitespace_only_is_treated_as_empty_and_removes_a_stored_row(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        first_type = DatasetDescription.VOCABULARY.values[0]
        DatasetDescription.objects.create(
            related=dataset, type=first_type, value="Existing text."
        )

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        client.post(url, data={first_type: "   \n  "})

        assert not DatasetDescription.objects.filter(
            related=dataset, type=first_type
        ).exists()


@pytest.mark.django_db
class TestASuccessfulSubmissionRedirectsToTheDatasetsPage:
    """T054 — a successful submission redirects to the dataset's own page, asserted by exact
    route reversal rather than a substring of the address."""

    def test_the_redirect_target_is_the_datasets_own_overview_url(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        first_type = DatasetDescription.VOCABULARY.values[0]

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        response = client.post(url, data={first_type: "Some text."})

        assert response.status_code == 302
        assert response.url == reverse("dataset:overview", kwargs={"uuid": dataset.uuid})


class TestDescriptionsUsesTheVocabularyDrivenForm:
    """T055 — built on the shared vocabulary-driven form (T009), not the row-based editor
    (``fairdm.contrib.generic.plugins.DescriptionsPlugin``) this page used to be registered
    on."""

    def test_the_declared_form_class_is_the_vocabulary_driven_form(self):
        assert Descriptions.form_class is VocabularyDescriptionsForm

    def test_the_page_is_not_built_on_the_generic_row_based_plugin(self):
        from fairdm.contrib.generic.plugins import DescriptionsPlugin

        assert not issubclass(Descriptions, DescriptionsPlugin)


def _hrefs(content: str) -> list[str]:
    """Every ``href="..."`` attribute value in rendered HTML, in document order."""
    return re.findall(r'href="([^"]*)"', content)


@pytest.mark.django_db
class TestUpdatePageOffersTheDeletionLink:
    """T070 / FR-045 — the update page offers the deletion page to a user who may delete the
    dataset, and offers it to nobody else. `fairdm.core.project.plugins.Update`'s equivalent,
    applied to datasets: the shared `form_view.html` shell already carries the slot and fills it
    from `get_delete_url()`, so this page supplies only the route names and the permission gate."""

    def test_a_user_who_may_delete_the_dataset_is_offered_the_link(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)

        response = client.get(
            reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        )

        delete_url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        assert any(
            href.startswith(delete_url) for href in _hrefs(response.content.decode())
        )

    def test_a_user_who_may_change_but_not_delete_is_offered_no_link(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)

        response = client.get(
            reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        )

        delete_url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        assert not any(
            href.startswith(delete_url) for href in _hrefs(response.content.decode())
        )


class TestTheSingularAddressNoLongerAnswers:
    """T058/FR-057 — every address names the record type in the plural. The singular
    ``dataset/<uuid>/`` mount ``fairdm/core/dataset/urls.py`` used to have is retired in favour
    of the plural ``datasets/<uuid>/`` include (014 plan P2)."""

    def test_a_request_to_the_singular_address_is_not_found(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        response = client.get(f"/dataset/{dataset.uuid}/")
        assert response.status_code == 404


class TestEachOfTheFourPagesStatesItsOwnPermission:
    """T060/FR-060 — ``can_open`` (``fairdm/contrib/plugins/access.py``) reads ``permission``
    straight off ``view_class``, never off the owning plugin
    (``getattr(view_class, "permission", None)``), so an additional view that states none is
    never treated as inheriting its owner's. ``Overview`` itself states none — reaching it is
    gated by visibility alone — and each of its three additional views states its own."""

    def test_the_overview_states_no_permission_of_its_own(self):
        assert "permission" not in Overview.__dict__

    def test_update_delete_and_descriptions_each_declare_their_own_permission(self):
        assert Update.__dict__.get("permission") == "dataset.change_dataset"
        assert Delete.__dict__.get("permission") == "dataset.delete_dataset"
        assert Descriptions.__dict__.get("permission") == "dataset.change_dataset"

    def test_a_page_stating_no_permission_does_not_inherit_its_owners(self):
        """Proven directly against the real mechanism rather than assumed: an owner declaring a
        permission, and a child that states none, is admitted anonymously — ``can_open`` never
        reads ``permission`` from ``plugin_class``."""

        class _OwnerWithPermission(Plugin):
            permission = "dataset.delete_dataset"

        class _ChildStatingNone(Plugin):
            plugin_class = _OwnerWithPermission
            check = staticmethod(lambda request, obj: True)

        request = _request_for(AnonymousUser())
        assert can_open(_ChildStatingNone, request, None) is True


@pytest.mark.django_db
class TestEachOfTheFourPagesGuardsAPrivateDatasetsVisibility:
    """T061/FR-061 — each of the dataset's four pages states its own visibility rule rather than
    relying on inheriting ``Overview``'s (an additional view's ``check`` is read from the owning
    plugin at call time, but that alone does not prove any *page* carrying it as an additional
    view actually refuses a real request — this goes through HTTP at all four addresses). The
    scenario that motivates it: a user holding ``dataset.change_dataset`` at the model level and
    no grant at all on this particular private dataset."""

    def test_every_page_refuses_a_model_level_holder_with_no_grant_on_this_record(
        self, client
    ):
        from django.contrib.auth.models import Permission

        dataset = DatasetFactory()  # private, per the model default
        user = UserFactory()
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="dataset", codename="change_dataset"
            )
        )
        client.force_login(user)

        for name in (
            "dataset:overview",
            "dataset:overview-update",
            "dataset:overview-descriptions",
            "dataset:overview-delete",
        ):
            url = reverse(name, kwargs={"uuid": dataset.uuid})
            response = client.get(url)
            assert response.status_code == 404, name


@pytest.mark.django_db
class TestTheDatasetsPagesContributeExactlyOneNavigationEntry:
    """T062/FR-062 — ``Update``, ``Delete`` and ``Descriptions`` are additional views of
    ``Overview``'s own registration rather than registrations of their own, so the per-record
    navigation gains no entry for any of them (mirrors
    ``fairdm.core.project.plugins.Overview``'s equivalent). Asserts the entry count, not the
    entry names, so a page renamed later still fails here if it starts registering its own
    entry."""

    def test_overview_contributes_exactly_one_entry(self):
        plugins.registry.get_urls_for_model(Dataset)
        menu = plugins.registry.get_plugin_menu_for_model(Dataset)
        labels = [item.extra_context.get("label") for item in menu.children]
        assert labels.count("Overview") == 1

    def test_update_descriptions_and_deletion_contribute_no_entry_of_their_own(self):
        plugins.registry.get_urls_for_model(Dataset)
        menu = plugins.registry.get_plugin_menu_for_model(Dataset)
        labels = [item.extra_context.get("label") for item in menu.children]
        assert "Update dataset" not in labels
        assert "Descriptions" not in labels
        assert "Delete dataset" not in labels
