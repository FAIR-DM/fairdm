"""Route smoke tests for the ``markdownx/`` routes in ``fairdm/conf/urls.py``,
which replace the ``martor/`` include they superseded (issue #266).
"""

from django.urls import reverse


class TestAccountCenterRoutes:
    """T038 (django-accounts-center 0.8 BREAKING 3): the Account Center landing
    page is now served by django-mvp's own ``mvp.urls``, mounted beside
    ``dac.urls`` at the same ``account-center/`` prefix so the address and the
    ``account-center`` URL name are unchanged, while the allauth management
    pages ``dac.urls`` still authors keep rendering under that prefix too."""

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


class TestMarkdownxRoutes:
    def test_markdownify_endpoint_renders_posted_content(self, db, client):
        response = client.post("/markdownx/markdownify/", {"content": "**bold**"})

        assert response.status_code == 200
        assert b"<strong>bold</strong>" in response.content

    def test_markdownify_endpoint_rejects_get(self, db, client):
        response = client.get("/markdownx/markdownify/")

        assert response.status_code == 405

    def test_image_upload_endpoint_is_not_exposed(self, db, client):
        """The editor offers no image upload, and the library's upload view writes
        to media storage without authenticating anyone, so it must not be routable."""
        response = client.post("/markdownx/upload/", {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        assert response.status_code == 404
