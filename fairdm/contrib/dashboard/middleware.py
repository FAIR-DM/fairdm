"""Count each open of a project or dataset page and each download of its records."""

from django.contrib.contenttypes.models import ContentType
from django.db.models import F
from django.utils import timezone

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project

OPENS = {"project:overview": Project, "dataset:overview": Dataset}
DOWNLOADS = {
    "project:samples": Project,
    "project:measurements": Project,
    "dataset:samples": Dataset,
    "dataset:measurements": Dataset,
}


def every_record(model):
    """Return every project, or every dataset private ones included."""
    return model.all_objects.all() if model is Dataset else model.objects.all()


class RecordUseMiddleware:
    """After a page answers, add one open or one download to its record's count for today."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            self.count(request, response)
        except Exception:  # noqa: BLE001 - counting never breaks a page
            pass
        return response

    def count(self, request, response):
        match = getattr(request, "resolver_match", None)
        if request.method != "GET" or response.status_code != 200 or match is None:
            return
        view = match.view_name
        if view in OPENS and not request.headers.get("HX-Request"):
            model, field = OPENS[view], "views"
        elif view in DOWNLOADS and "export" in request.GET:
            model, field = DOWNLOADS[view], "exports"
        else:
            return
        every = every_record(model)
        record = every.filter(uuid=match.kwargs.get("uuid")).first()
        if record is None:
            return
        user = request.user
        if user.is_authenticated and every.with_level(
            user, ContributionLevel.VIEW
        ).filter(pk=record.pk).exists():
            return
        from fairdm.contrib.dashboard.models import RecordUse

        use, _ = RecordUse.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(model),
            object_id=record.pk,
            day=timezone.localdate(),
        )
        RecordUse.objects.filter(pk=use.pk).update(**{field: F(field) + 1})
