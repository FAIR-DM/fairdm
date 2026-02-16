"""Integration test to verify all registered models' admin add pages load."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from fairdm.registry import registry

User = get_user_model()


@pytest.mark.django_db
class TestAllAdminAddPages:
    """Test that all registered models' admin add pages load successfully."""

    def test_all_registered_model_admin_add_pages_load(self):
        """Test that all registered models have working admin add pages."""
        # Create a superuser
        user = User.objects.create_superuser(
            email="admin@test.com",
            password="testpass123",
        )
        client = Client()
        client.force_login(user)

        # Get all registered models
        configs = registry.get_all_configs()

        failed_pages = []

        for config in configs:
            model = config.model
            app_label = model._meta.app_label
            model_name = model._meta.model_name

            url = f"/admin/{app_label}/{model_name}/add/"

            try:
                response = client.get(url)
                if response.status_code != 200:
                    failed_pages.append((url, response.status_code, "Non-200 status"))
                print(f"✓ {model.__name__}: {url} (status {response.status_code})")
            except Exception as e:
                failed_pages.append((url, None, str(e)))
                print(f"✗ {model.__name__}: {url} - {e}")

        # Assert all pages loaded successfully
        if failed_pages:
            failure_msg = "\n".join([f"  - {url}: {error}" for url, status, error in failed_pages])
            pytest.fail(f"The following admin add pages failed to load:\n{failure_msg}")
