"""Tagging model for core objects."""

from django.db import models
from django.utils.translation import gettext as _
from taggit.models import CommonGenericTaggedItemBase, TaggedItemBase


class TaggedItem(CommonGenericTaggedItemBase, TaggedItemBase):
    """Tagged item whose ``object_id`` is a string, for core models with a ShortUUID primary key."""

    object_id: str = models.CharField(
        max_length=23, verbose_name=_("object ID"), db_index=True
    )  # type: ignore[assignment]
    natural_key_fields = ["object_id"]
