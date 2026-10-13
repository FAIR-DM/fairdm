"""Route smoke tests for the account, legal and ``markdownx/`` routes in ``fairdm/conf/urls.py``."""

import pytest
from django.urls import reverse
from mvp_compliance.models import Document

from fairdm.factories import UserFactory


class TestAccountCenterRoutes:
    def test_reverse_account_center_still_resolves_to_the_same_address(self):
        assert reverse("account-center") == "/account-center/"

    def test_a_signed_in_visitor_sees_the_account_center_landing_page(
        self, db, authenticated_client
    ):
        response = authenticated_client.get(reverse("account-center"))

        assert response.status_code == 200

    def test_an_anonymous_visitor_is_redirected_to_sign_in(self, db, client):
        response = client.get(reverse("account-center"))

        assert response.status_code == 302

    def test_the_allauth_login_page_still_renders_under_the_same_prefix(
        self, db, client
    ):
        response = client.get("/account-center/login/")

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "url_name",
        [
            "account_email",
            "account_change_password",
            "socialaccount_connections",
            "mfa_index",
            "usersessions_list",
        ],
    )
    def test_each_account_management_page_renders_in_the_account_center(
        self, db, authenticated_client, url_name
    ):
        response = authenticated_client.get(reverse(url_name))

        assert response.status_code == 200
        assert "mvp/account/base.html" in [t.name for t in response.templates]


class TestLegalDocumentRoutes:
    @pytest.fixture
    def document(self, db):
        document = Document.objects.create(name="Terms", slug="terms")
        document.versions.create(markdown="Be kind.").publish()
        return document

    def test_a_published_document_is_a_page_anyone_can_read(self, client, document):
        response = client.get(reverse("mvp_compliance:document", args=["terms"]))

        assert response.status_code == 200
        assert response.context["object"] == document

    def test_a_signed_in_person_is_asked_to_agree_before_using_the_portal(
        self, db, authenticated_client, document
    ):
        response = authenticated_client.get(reverse("home"))

        assert response.status_code == 302
        assert response["Location"] == reverse("mvp_compliance:agree") + "?next=%2F"

    def test_the_agreements_page_is_in_the_account_center(
        self, db, authenticated_client
    ):
        response = authenticated_client.get(reverse("mvp_compliance:agreed"))

        assert response.status_code == 200
        assert reverse("mvp_compliance:agreed").encode() in response.content

    def test_an_administrator_acting_as_a_person_who_has_not_agreed_can_stop(
        self, client, document
    ):
        administrator = UserFactory(is_superuser=True, is_staff=True)
        person = UserFactory()
        client.force_login(administrator)
        client.post(reverse("hijack:acquire"), {"user_pk": person.pk})
        assert client.session["_auth_user_id"] == str(person.pk)

        client.post(reverse("hijack:release"))

        assert client.session["_auth_user_id"] == str(administrator.pk)


class TestMarkdownxRoutes:
    def test_markdownify_endpoint_renders_posted_content(self, db, client):
        response = client.post("/markdownx/markdownify/", {"content": "**bold**"})

        assert response.status_code == 200
        assert b"<strong>bold</strong>" in response.content

    def test_markdownify_endpoint_rejects_get(self, db, client):
        response = client.get("/markdownx/markdownify/")

        assert response.status_code == 405

    def test_image_upload_endpoint_is_not_exposed(self, db, client):
        # The library's upload view writes to media storage without authenticating anyone.
        response = client.post(
            "/markdownx/upload/", {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        assert response.status_code == 404
