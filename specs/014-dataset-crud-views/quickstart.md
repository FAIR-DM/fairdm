# Quick-Start: Dataset CRUD Views

**Branch**: `014-dataset-crud-views` | **Date**: 2026-05-12

This guide is a developer-oriented cheat-sheet for implementing the Dataset CRUD views feature. It summarises what to build, where to put it, and what patterns to follow — without re-explaining the rationale (see [research.md](research.md) and [data-model.md](data-model.md) for that).

---

## 1. Add DatasetCreateForm to forms.py

**File**: `fairdm/core/dataset/forms.py`

Add after the existing `DatasetForm` class:

```python
class DatasetCreateForm(DatasetForm):
    """Restricted form for initial dataset creation.

    Exposes only the minimum fields needed at creation time. All
    other fields (image, reference, doi) are available after creation
    via the full DatasetForm on the update view.
    """

    class Meta(DatasetForm.Meta):
        fields = ["name", "project", "license"]
```

No changes to `DatasetForm` itself.

---

## 2. Write failing tests first (TDD)

**File**: `tests/test_core/test_dataset/test_views.py` (create new)

Minimum required tests (smoke + behaviour):

```python
import pytest
from django.test import Client
from django.urls import reverse

from fairdm.factories import DatasetFactory, UserFactory


@pytest.mark.django_db
class TestDatasetListView:
    def test_anonymous_get(self, client):
        url = reverse("dataset-list")
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestDatasetCreateView:
    def test_anonymous_redirects_to_login(self, client):
        url = reverse("dataset-create")
        response = client.get(url)
        assert response.status_code == 302

    def test_authenticated_get(self, client, django_user_model):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("dataset-create"))
        assert response.status_code == 200


@pytest.mark.django_db
class TestDatasetUpdateView:
    def test_anonymous_redirects_to_login(self, client):
        dataset = DatasetFactory()
        url = reverse("dataset-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 302

    def test_no_permission_returns_403(self, client):
        user = UserFactory()
        dataset = DatasetFactory()
        client.force_login(user)
        url = reverse("dataset-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 403

    def test_with_permission_returns_200(self, client):
        from guardian.shortcuts import assign_perm
        user = UserFactory()
        dataset = DatasetFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestDatasetDeleteView:
    def test_anonymous_redirects_to_login(self, client):
        dataset = DatasetFactory()
        url = reverse("dataset-delete", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 302

    def test_no_permission_returns_403(self, client):
        user = UserFactory()
        dataset = DatasetFactory()
        client.force_login(user)
        url = reverse("dataset-delete", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 403

    def test_with_permission_returns_200(self, client):
        from guardian.shortcuts import assign_perm
        user = UserFactory()
        dataset = DatasetFactory()
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset-delete", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 200
```

---

## 3. Add DatasetUpdateView and DatasetDeleteView to views.py

**File**: `fairdm/core/dataset/views.py`

Add imports at the top:

```python
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy

from fairdm.views import FairDMDeleteView, FairDMUpdateView
from .forms import DatasetCreateForm, DatasetForm
```

Add after existing views:

```python
class DatasetUpdateView(LoginRequiredMixin, FairDMUpdateView):
    model = Dataset
    form_class = DatasetForm
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_object(self, queryset=None):
        uuid = self.kwargs.get("uuid")
        dataset = get_object_or_404(Dataset, uuid=uuid)
        if not self.request.user.has_perm("change_dataset", dataset):
            raise PermissionDenied("You do not have permission to edit this dataset.")
        return dataset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_success_url(self):
        return reverse("dataset-detail", kwargs={"uuid": self.object.uuid})


class DatasetDeleteView(LoginRequiredMixin, FairDMDeleteView):
    model = Dataset
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    success_url = reverse_lazy("dataset-list")
    require_confirmation = True

    def get_object(self, queryset=None):
        uuid = self.kwargs.get("uuid")
        dataset = get_object_or_404(Dataset, uuid=uuid)
        if not self.request.user.has_perm("delete_dataset", dataset):
            raise PermissionDenied("You do not have permission to delete this dataset.")
        return dataset

    def get_confirmation_value(self):
        return self.object.name
```

Also modify `DatasetCreateView`:
- Change `form_class = DatasetForm` → `form_class = DatasetCreateForm`
- Remove the `get_initial()` override entirely

---

## 4. Register URL patterns

**File**: `fairdm/core/dataset/urls.py`

Add to imports:

```python
from .views import DatasetUpdateView, DatasetDeleteView
```

Add to `urlpatterns`:

```python
path("datasets/<str:uuid>/update/", DatasetUpdateView.as_view(), name="dataset-update"),
path("datasets/<str:uuid>/delete/", DatasetDeleteView.as_view(), name="dataset-delete"),
```

---

## 5. Verify

```bash
python manage.py check
pytest tests/test_core/test_dataset/test_views.py -v
```

All smoke tests should pass. Then implement → verify green.
