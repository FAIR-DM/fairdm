"""Route smoke tests for the ``markdownx/`` routes in ``fairdm/conf/urls.py``,
which replace the ``martor/`` include they superseded (issue #266).
"""


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
