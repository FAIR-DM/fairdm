"""Management command that runs every model's ``preload`` hook."""

import logging

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Call ``preload()`` on each installed model that defines one."""

    def handle(self, *args, **options):
        """Call ``preload()`` on every model that defines it."""
        for model in apps.get_models():
            if hasattr(model, "preload"):
                model.preload()
