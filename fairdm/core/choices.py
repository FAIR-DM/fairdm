"""Choice enumerations shared by the core records."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class ProjectStatus(models.IntegerChoices):
    """The stages a project moves through, from idea to completion."""

    CONCEPT = 0, _("Concept")
    PLANNING = 1, _("Planning")
    IN_PROGRESS = 2, _("In progress")
    COMPLETE = 3, _("Complete")
    SEARCHING_FOR_COLLABORATORS = 4, _("Searching for collaborators")
