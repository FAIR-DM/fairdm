"""The project's own pages: one registered collection, per 013 plan P1.

T063 - the project's own page is a registration against ``Project``, so the portal's per-record
       navigation offers an entry for it, and that entry is selected while on the page.
T064 - its attributes and deletion pages are extra views of that registration, not registrations
       of their own, so the navigation strip gains no entry for either.
T065 - each of those pages states its own permission, since an additional view inherits its
       owner's predicate but never its permission.
T066 - the registration's own visibility check refuses a private project to anyone without
       `project.view_project`, since a registered page resolves its record past the filtered
       manager on the assumption that the page gates itself.
T067 - a user who may change a project is offered its attributes and descriptions pages from the
       project's own page; one who may not is offered neither.
T068 - a user who may delete a project is offered its deletion page from the project's own page;
       one who may not is not.
T069 - the deletion page's back control is a working link to a real address.
T070 - the attributes, descriptions and deletion pages each offer a working link back to the
       project itself.
T071 - every link drawn by each page this feature owns resolves to a real address, none empty.
"""

import re

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from fairdm import plugins
from fairdm.contrib.plugins.access import can_open
from fairdm.core.project.models import Project
from fairdm.core.project.plugins import Attributes, Delete, Descriptions, Overview
from fairdm.core.utils import assign_perm
from fairdm.factories import ProjectFactory, UserFactory
from fairdm.utils.choices import Visibility


def _hrefs(content: str) -> list[str]:
    """Every ``href="..."`` attribute value in rendered HTML, in document order."""
    return re.findall(r'href="([^"]*)"', content)


def _request_for(user, path="/"):
    request = RequestFactory().get(path)
    request.user = user
    return request


def _entry_labels(model):
    # Rebuilds the menu now, rather than relying on it having been built already by the root
    # urlconf's own import — the same reason ``tests/test_contrib/test_plugins/test_menus.py``
    # calls this before every assertion.
    plugins.registry.get_urls_for_model(model)
    menu = plugins.registry.get_plugin_menu_for_model(model)
    return [item.extra_context.get("label") for item in menu.children]


@pytest.mark.django_db
class TestOverviewIsTheProjectsOwnRegistration:
    """The project's own page used to sit outside the registration namespace, so the per-record
    navigation could never offer an entry for it and no tab was ever selected while on it
    (013 plan P1)."""

    def test_the_project_menu_carries_an_overview_entry(self):
        assert "Overview" in _entry_labels(Project)

    def test_the_overview_entry_is_selected_while_on_the_projects_page(
        self, public_project
    ):
        menu = plugins.registry.get_plugin_menu_for_model(Project)
        url = reverse("project:overview", kwargs={"uuid": public_project.uuid})
        request = _request_for(AnonymousUser(), path=url)
        processed = menu.process(
            request, object=public_project, uuid=public_project.uuid
        )
        overview_item = next(
            child
            for child in processed.children
            if child.extra_context.get("label") == "Overview"
        )
        assert overview_item.selected is True

    def test_the_overview_declares_no_path_segment_of_its_own(self, public_project):
        """It stays the root of the record's include, the same convention the contributor
        pages already use."""
        url = reverse("project:overview", kwargs={"uuid": public_project.uuid})
        # Nothing follows the record's own identifier in the address.
        assert url.split(str(public_project.uuid))[-1] == "/"


@pytest.mark.django_db
class TestAttributesAndDeletionAreExtraViewsNotEntries:
    """A registration carries one menu entry for the whole collection; the attributes and
    deletion pages hang off the overview's registration rather than registering themselves, so
    the strip does not fill with an entry per addon (013 plan P1)."""

    def test_the_attributes_page_resolves_as_an_extra_view_of_the_overview(
        self, public_project
    ):
        url = reverse(
            "project:overview-attributes", kwargs={"uuid": public_project.uuid}
        )
        assert url.endswith(f"{public_project.uuid}/attributes/")

    def test_the_deletion_page_resolves_as_an_extra_view_of_the_overview(
        self, public_project
    ):
        url = reverse("project:overview-delete", kwargs={"uuid": public_project.uuid})
        assert url.endswith(f"{public_project.uuid}/delete/")

    def test_the_project_menu_carries_no_entry_for_attributes_or_deletion(self):
        labels = _entry_labels(Project)
        assert "Attributes" not in labels
        assert "Delete" not in labels

    def test_the_project_menu_carries_exactly_one_entry_for_the_collection(self):
        """Superseded ``ProjectConfigure`` (013 plan P1) is retired along with the standalone
        pages it duplicated, so the collection is carried by ``Overview`` alone."""
        labels = _entry_labels(Project)
        assert labels.count("Overview") == 1
        assert "Configure" not in labels


@pytest.mark.django_db
class TestEachExtraViewStatesItsOwnPermission:
    """FR-051 / issue #279: an additional view inherits its owner's ``check`` but never its
    ``permission`` (fairdm/contrib/plugins/access.py ``can_open``), so a page that states none
    is open to everyone, including an anonymous visitor. Each page here names the right it
    needs, matching the standalone pages it replaces (013 plan P1)."""

    def test_attributes_refuses_a_signed_in_user_without_change_permission(
        self, public_project, user_with_no_permission
    ):
        request = _request_for(user_with_no_permission)
        assert can_open(Attributes, request, public_project) is False

    def test_attributes_admits_a_user_holding_change_permission(
        self, user_with_change_permission
    ):
        request = _request_for(user_with_change_permission)
        assert (
            can_open(Attributes, request, user_with_change_permission.project) is True
        )

    def test_attributes_refuses_an_anonymous_request(self, public_project):
        request = _request_for(AnonymousUser())
        assert can_open(Attributes, request, public_project) is False

    def test_deletion_refuses_a_signed_in_user_without_delete_permission(
        self, public_project, user_with_no_permission
    ):
        request = _request_for(user_with_no_permission)
        assert can_open(Delete, request, public_project) is False

    def test_deletion_admits_a_user_holding_delete_permission(
        self, user_with_delete_permission
    ):
        request = _request_for(user_with_delete_permission)
        assert can_open(Delete, request, user_with_delete_permission.project) is True

    def test_deletion_refuses_an_anonymous_request(self, public_project):
        request = _request_for(AnonymousUser())
        assert can_open(Delete, request, public_project) is False


@pytest.mark.django_db
class TestTheOverviewGuardsAPrivateProjectsVisibility:
    """The regression this restructuring is most likely to introduce (013 plan P1): a
    registered page resolves its record through machinery that reads past the filtered manager,
    on the assumption that the page gates itself. Without the visibility check carried across, a
    private project becomes readable by anyone holding its address."""

    def test_a_private_project_refuses_a_user_who_may_not_view_it(
        self, private_project, user_with_no_permission
    ):
        request = _request_for(user_with_no_permission)
        assert can_open(Overview, request, private_project) is False

    def test_a_private_project_refuses_an_anonymous_request(self, private_project):
        request = _request_for(AnonymousUser())
        assert can_open(Overview, request, private_project) is False

    def test_a_private_project_admits_a_user_holding_view_permission(
        self, private_project, user_with_no_permission
    ):
        assign_perm("view_project", user_with_no_permission, private_project)
        request = _request_for(user_with_no_permission)
        assert can_open(Overview, request, private_project) is True

    def test_a_public_project_admits_an_anonymous_request(self, public_project):
        request = _request_for(AnonymousUser())
        assert can_open(Overview, request, public_project) is True

    def test_the_attributes_page_inherits_the_visibility_check_from_its_owner(
        self, private_project, user_with_change_permission
    ):
        """A user holding change rights on a *different* project still cannot reach a private
        project's attributes page: an additional view inherits its owner's `check`, so the
        visibility guard applies there too."""
        request = _request_for(user_with_change_permission)
        assert can_open(Attributes, request, private_project) is False


@pytest.mark.django_db
class TestAPrivateProjectsPageThroughARealRequest:
    """`can_open()` answering False is a claim about the predicate, not about the page. These
    go through the URL and the response, which is the composition a visitor actually meets."""

    def test_an_anonymous_visitor_is_refused_a_private_project(
        self, client, private_project
    ):
        response = client.get(
            reverse("project:overview", kwargs={"uuid": private_project.uuid})
        )
        assert response.status_code in (302, 403, 404)
        if response.status_code == 302:
            assert reverse("account_login") in response.url

    def test_a_signed_in_visitor_without_view_rights_is_refused(
        self, client, private_project, user_with_no_permission
    ):
        client.force_login(user_with_no_permission)
        response = client.get(
            reverse("project:overview", kwargs={"uuid": private_project.uuid})
        )
        assert response.status_code in (403, 404)

    def test_an_anonymous_visitor_reaches_a_public_project(self, client, public_project):
        response = client.get(
            reverse("project:overview", kwargs={"uuid": public_project.uuid})
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestAttributesPageOverHTTP:
    """The attributes page (013 plan P3) resolves as an additional view of the project's own
    registration rather than an address of its own, keyed by the project's identifier."""

    def test_the_attributes_page_is_keyed_by_the_projects_identifier_not_its_own_address(
        self, public_project
    ):
        """T026 — Reversed by name, the attributes page's URL carries the project's own
        identifier rather than resolving to an address of its own."""
        url = reverse(
            "project:overview-attributes", kwargs={"uuid": public_project.uuid}
        )
        assert url == f"/projects/{public_project.uuid}/attributes/"

    def test_an_anonymous_visitor_opening_the_attributes_page_is_redirected_to_sign_in(
        self, client, public_project
    ):
        """T026 — Opened directly (not merely reversed), the attributes page redirects an
        anonymous visitor to sign in rather than admitting them or 404ing."""
        url = reverse(
            "project:overview-attributes", kwargs={"uuid": public_project.uuid}
        )
        response = client.get(url)
        assert response.status_code == 302
        assert reverse("account_login") in response.url

    def test_a_user_holding_change_permission_at_the_model_level_is_admitted(
        self, client
    ):
        """T028 — A user holding `project.change_project` at the model level, granted through
        no individual record, is admitted to a project they hold no per-object grant on. This
        is the retiring standalone page's behaviour and must survive: the check has to ask
        twice, model level then record (`fairdm/contrib/plugins/access.py` `has_perm`), or a
        model-level-only holder is refused."""
        from django.contrib.auth.models import Permission

        from fairdm.factories import ProjectFactory, UserFactory

        project = ProjectFactory()
        user = UserFactory()
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="project", codename="change_project"
            )
        )
        client.force_login(user)

        url = reverse("project:overview-attributes", kwargs={"uuid": project.uuid})
        response = client.get(url)

        assert response.status_code == 200


@pytest.mark.django_db
class TestExactlyOnePageOffersTheProjectsOwnAttributes:
    """T049 — `ProjectConfigure` is retired (013 plan P1); this keeps it retired by asserting
    no second registered page ever offers a form overlapping the attributes page's own field
    set."""

    ATTRIBUTES_FIELDS = {"image", "name", "status", "visibility", "owner"}

    def _all_pages(self):
        """Every page reachable against `Project`: top-level registrations plus each one's
        extra views (`fairdm.contrib.plugins.base.Plugin.get_extra_views`)."""
        pages = []
        for plugin_cls, _kwargs in plugins.registry.get_plugins_for_model(Project):
            pages.append(plugin_cls)
            pages.extend(plugin_cls.get_extra_views())
        return pages

    def test_exactly_one_page_offers_the_attributes_field_set(self):
        offering_pages = []
        for page in self._all_pages():
            form_class = getattr(page, "form_class", None)
            fields = getattr(getattr(form_class, "Meta", None), "fields", None)
            if fields and self.ATTRIBUTES_FIELDS & set(fields):
                offering_pages.append(page)

        assert offering_pages == [Attributes]


@pytest.mark.django_db
class TestDescriptionsPageIsARegistrationOfItsOwn:
    """T051 — unlike the attributes and deletion pages, the descriptions page is a registration
    of its own rather than an additional view, matching Dataset and Sample (013 plan P2)."""

    def test_reversed_by_name_it_resolves_at_an_address_keyed_by_the_projects_identifier(
        self, public_project
    ):
        url = reverse("project:descriptions", kwargs={"uuid": public_project.uuid})
        assert url == f"/projects/{public_project.uuid}/descriptions/"

    def test_an_anonymous_visitor_is_redirected_to_sign_in(self, client, public_project):
        url = reverse("project:descriptions", kwargs={"uuid": public_project.uuid})
        response = client.get(url)
        assert response.status_code == 302
        assert reverse("account_login") in response.url


@pytest.mark.django_db
class TestDescriptionsPageStatesItsOwnPermission:
    """T052 — the descriptions page declares ``project.change_project`` for itself: a registered
    page that states none is open to everyone, anonymous included, since the record is fetched
    through an unfiltered manager on the assumption that the page checks for itself."""

    def test_refuses_a_signed_in_user_without_change_permission(
        self, public_project, user_with_no_permission
    ):
        request = _request_for(user_with_no_permission)
        assert can_open(Descriptions, request, public_project) is False

    def test_admits_a_user_holding_change_permission(self, user_with_change_permission):
        request = _request_for(user_with_change_permission)
        assert (
            can_open(Descriptions, request, user_with_change_permission.project) is True
        )

    def test_refuses_an_anonymous_request(self, public_project):
        request = _request_for(AnonymousUser())
        assert can_open(Descriptions, request, public_project) is False


@pytest.mark.django_db
class TestDescriptionsPageOffersOneAreaPerVocabularyType:
    """T053 — for a project with no descriptions, the page offers exactly one empty area per
    concept in ``ProjectDescription.VOCABULARY``, the count read from the vocabulary itself
    rather than written as a literal (013 plan P2: built on ``VocabularyDescriptionsForm``,
    already built and tested)."""

    def test_the_field_set_matches_the_vocabulary_exactly(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert list(form.fields) == list(ProjectDescription.VOCABULARY.values)

    def test_every_area_starts_empty_for_a_project_with_no_descriptions(
        self, client, user_with_change_permission
    ):
        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert all(field.initial in (None, "") for field in form)


@pytest.mark.django_db
class TestDescriptionsPageAreasAreLabelledFromTheVocabulary:
    """T054 — each area is labelled with its concept's name and carries that concept's
    definition as help text, asserted against the vocabulary's own label and definition rather
    than a copied string."""

    def test_the_first_areas_label_and_help_text_match_its_concept(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type = ProjectDescription.VOCABULARY.values[0]
        concept = ProjectDescription.VOCABULARY.get_concept(first_type)

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert form.fields[first_type].label == concept.label()
        assert form.fields[first_type].help_text == concept.definition()


@pytest.mark.django_db
class TestSavingTextIntoOneAreaRecordsOnlyThatType:
    """T055 — saving text into exactly one area records one description of that type and
    creates no description of any other type."""

    def test_saving_one_area_creates_exactly_one_description_of_that_type(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type = ProjectDescription.VOCABULARY.values[0]

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
        client.post(url, data={first_type: "Some abstract text."})

        assert ProjectDescription.objects.filter(related=project).count() == 1
        row = ProjectDescription.objects.get(related=project)
        assert row.type == first_type
        assert row.value == "Some abstract text."


@pytest.mark.django_db
class TestExistingDescriptionsShowInTheirOwnArea:
    """T056 — a project holding an existing description shows that text in the area for its
    own type and no other."""

    def test_the_existing_description_appears_in_its_own_area_and_others_stay_empty(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type, second_type = ProjectDescription.VOCABULARY.values[:2]
        ProjectDescription.objects.create(
            related=project, type=first_type, value="Existing abstract."
        )

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert form.fields[first_type].initial == "Existing abstract."
        assert form.fields[second_type].initial in (None, "")


@pytest.mark.django_db
class TestEditingAnExistingDescriptionPersists:
    """T057 — changing an existing description's text and submitting persists the change."""

    def test_the_changed_text_persists(self, client, user_with_change_permission):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type = ProjectDescription.VOCABULARY.values[0]
        row = ProjectDescription.objects.create(
            related=project, type=first_type, value="Original text."
        )

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
        client.post(url, data={first_type: "Changed text."})

        row.refresh_from_db()
        assert row.value == "Changed text."
        assert ProjectDescription.objects.filter(related=project).count() == 1


@pytest.mark.django_db
class TestClearingAnAreaRemovesTheDescription:
    """T058 — clearing an area and submitting removes that description from the project."""

    def test_clearing_the_area_deletes_the_row(self, client, user_with_change_permission):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type = ProjectDescription.VOCABULARY.values[0]
        ProjectDescription.objects.create(
            related=project, type=first_type, value="Existing text."
        )

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
        client.post(url, data={first_type: ""})

        assert not ProjectDescription.objects.filter(
            related=project, type=first_type
        ).exists()


@pytest.mark.django_db
class TestRepeatSubmissionNeverDuplicatesAType:
    """T060 — a project never holds two descriptions of the same type through this page, even
    across repeated submissions to the same area. Asserted on the count per type, not merely
    that the save succeeds."""

    def test_submitting_the_same_area_three_times_leaves_exactly_one_row(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type = ProjectDescription.VOCABULARY.values[0]

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
        client.post(url, data={first_type: "First."})
        client.post(url, data={first_type: "Second."})
        client.post(url, data={first_type: "Third."})

        assert ProjectDescription.objects.filter(related=project, type=first_type).count() == 1
        assert (
            ProjectDescription.objects.get(related=project, type=first_type).value
            == "Third."
        )


@pytest.mark.django_db
class TestEmptyAndWhitespaceOnlyAreasCreateNothing:
    """T059 — an area left empty creates nothing, and an area containing only whitespace is
    treated as empty: nothing created, and any row already stored for that type removed."""

    def test_leaving_an_area_empty_creates_no_description(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
        client.post(url, data={})

        assert not ProjectDescription.objects.filter(related=project).exists()

    def test_whitespace_only_is_treated_as_empty_and_removes_a_stored_row(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type = ProjectDescription.VOCABULARY.values[0]
        ProjectDescription.objects.create(
            related=project, type=first_type, value="Existing text."
        )

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
        client.post(url, data={first_type: "   \n  "})

        assert not ProjectDescription.objects.filter(
            related=project, type=first_type
        ).exists()


@pytest.mark.django_db
class TestASuccessfulSubmissionRedirectsToTheProjectsPage:
    """T061 — a successful submission redirects to the project's own page, asserted by exact
    route reversal rather than a substring of the address."""

    def test_the_redirect_target_is_the_projects_own_overview_url(
        self, client, user_with_change_permission
    ):
        from fairdm.core.project.models import ProjectDescription

        project = user_with_change_permission.project
        client.force_login(user_with_change_permission)
        first_type = ProjectDescription.VOCABULARY.values[0]

        url = reverse("project:descriptions", kwargs={"uuid": project.uuid})
        response = client.post(url, data={first_type: "Some text."})

        assert response.status_code == 302
        assert response.url == reverse("project:overview", kwargs={"uuid": project.uuid})


@pytest.mark.django_db
class TestProjectsOwnPageOffersAttributesAndDescriptionsLinks:
    """T067 — a user who may change the project is offered links to its attributes and
    descriptions pages from the project's own page; a signed-in user who may not is offered
    neither. The attributes link switches on the interface layer's existing action-link
    mechanism (``mvp.views.detail.CRUDDirectoryMixin``, read into ``directory`` and drawn by
    the shared ``detail_view.html`` shell) rather than a hand-rolled one (013 plan P5); the
    descriptions link is the registration's own tab, already gated by the same ``can_open`` the
    page itself checks."""

    def test_a_user_who_may_change_the_project_is_offered_both_links(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        assign_perm("change_project", user, project)
        client.force_login(user)

        response = client.get(
            reverse("project:overview", kwargs={"uuid": project.uuid})
        )

        attributes_url = reverse(
            "project:overview-attributes", kwargs={"uuid": project.uuid}
        )
        descriptions_url = reverse(
            "project:descriptions", kwargs={"uuid": project.uuid}
        )
        assertContains(response, f'href="{attributes_url}"')
        assertContains(response, f'href="{descriptions_url}"')

    def test_a_signed_in_user_who_may_not_change_it_is_offered_neither(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        client.force_login(user)

        response = client.get(
            reverse("project:overview", kwargs={"uuid": project.uuid})
        )

        attributes_url = reverse(
            "project:overview-attributes", kwargs={"uuid": project.uuid}
        )
        descriptions_url = reverse(
            "project:descriptions", kwargs={"uuid": project.uuid}
        )
        assertNotContains(response, f'href="{attributes_url}"')
        assertNotContains(response, f'href="{descriptions_url}"')


@pytest.mark.django_db
class TestProjectsOwnPageOffersTheDeletionLink:
    """T068 — a user who may delete the project is offered a link to its deletion page from the
    project's own page; a signed-in user who may not is not. Same mechanism as T067's attributes
    link — the shell's own "Delete" button, drawn from ``directory.delete_url``."""

    def test_a_user_who_may_delete_the_project_is_offered_the_link(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        assign_perm("delete_project", user, project)
        client.force_login(user)

        response = client.get(
            reverse("project:overview", kwargs={"uuid": project.uuid})
        )

        delete_url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        assertContains(response, f'href="{delete_url}"')

    def test_a_signed_in_user_who_may_not_delete_it_is_not_offered_the_link(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        client.force_login(user)

        response = client.get(
            reverse("project:overview", kwargs={"uuid": project.uuid})
        )

        delete_url = reverse("project:overview-delete", kwargs={"uuid": project.uuid})
        assertNotContains(response, f'href="{delete_url}"')
