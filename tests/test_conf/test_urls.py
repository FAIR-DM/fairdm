"""Route smoke tests for ``fairdm/conf/urls.py``'s ``markdownx/`` include,
which replaces the ``martor/`` include it superseded (issue #266).
"""


class TestMarkdownxRoutes:
    def test_markdownify_endpoint_renders_posted_content(self, db, client):
        response = client.post("/markdownx/markdownify/", {"content": "**bold**"})

        assert response.status_code == 200
        assert b"<strong>bold</strong>" in response.content

    def test_markdownify_endpoint_rejects_get(self, db, client):
        response = client.get("/markdownx/markdownify/")

        assert response.status_code == 405

    def test_upload_endpoint_rejects_an_invalid_ajax_upload(self, db, client):
        response = client.post(
            "/markdownx/upload/", {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        assert response.status_code == 400
