"""Singleton models holding the portal's branding and governing authority."""

from django.contrib import admin
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.fields import ThumbnailerImageField
from parler.models import TranslatableModel, TranslatedFields
from solo.models import SingletonModel


def brand_asset_path(instance, filename: str) -> str:
    """Return the upload path for a brand asset (logo or icon).

    Args:
        instance: The Authority or Identity being saved.
        filename: The uploaded file's name.

    Returns:
        ``identity/<model name>_<filename>``, for example ``identity/portal-identity_logo.svg``.
    """
    # `upload_to` does not receive the field name, so the path uses the model name.
    model_name = slugify(instance._meta.verbose_name)
    return f"identity/{model_name}_{filename}"


class BrandAssets(models.Model):
    """Abstract model adding light and dark theme variants of a logo and an icon.

    Attributes:
        logo_light: Logo for light theme backgrounds.
        logo_dark: Logo for dark theme backgrounds.
        icon_light: Small icon or favicon for the light theme.
        icon_dark: Small icon or favicon for the dark theme.
    """

    logo_light = ThumbnailerImageField(
        verbose_name=_("Logo (Light Theme)"),
        upload_to=brand_asset_path,
        blank=True,
        null=True,
        help_text=_("Logo displayed on light backgrounds. SVG recommended."),
    )
    logo_dark = ThumbnailerImageField(
        verbose_name=_("Logo (Dark Theme)"),
        upload_to=brand_asset_path,
        blank=True,
        null=True,
        help_text=_("Logo displayed on dark backgrounds. SVG recommended."),
    )
    icon_light = ThumbnailerImageField(
        verbose_name=_("Icon (Light Theme)"),
        upload_to=brand_asset_path,
        blank=True,
        null=True,
        help_text=_("Small icon/favicon for light theme. ICO or PNG recommended."),
    )
    icon_dark = ThumbnailerImageField(
        verbose_name=_("Icon (Dark Theme)"),
        upload_to=brand_asset_path,
        blank=True,
        null=True,
        help_text=_("Small icon/favicon for dark theme. ICO or PNG recommended."),
    )

    class Meta:
        abstract = True


class Authority(BrandAssets, SingletonModel, TranslatableModel):
    """Governing authority or organization managing the portal."""

    url = models.URLField(
        _("URL"),
        blank=True,
        null=True,
        help_text=_("Website URL of the governing authority."),
    )
    contact = models.EmailField(
        _("Contact"),
        blank=True,
        null=True,
        help_text=_("Contact email for the governing authority."),
    )

    translations = TranslatedFields(
        name=models.CharField(_("Name"), max_length=255),
        short_name=models.CharField(
            _("Short Name"), max_length=255, blank=True, null=True
        ),
        description=models.TextField(_("Description")),
    )

    class Meta:
        verbose_name = _("Governing Authority")


class Identity(BrandAssets, SingletonModel, TranslatableModel):
    """Portal identity configuration including branding and metadata."""

    keywords: models.ManyToManyField = models.ManyToManyField(
        "research_vocabs.Concept",
        verbose_name=_("Keywords"),
        help_text=_(
            "A set of keywords from controlled vocabularies describing the portal."
        ),
        blank=True,
    )

    translations = TranslatedFields(
        name=models.CharField(_("Name"), max_length=255),
        short_name=models.CharField(
            _("Short Name"), max_length=255, blank=True, null=True
        ),
        description=models.TextField(_("Description")),
    )

    class Meta:
        db_table = "identity_database"
        verbose_name = _("Portal Identity")

    def save(self, *args, **kwargs):
        """Save, then use the portal name as the admin site header and title."""
        super().save(*args, **kwargs)
        name = self.safe_translation_getter("name", default="FairDM")
        admin.site.site_header = name
        admin.site.site_title = name

    def __str__(self):
        """Return a fixed label, since the portal has one identity."""
        return "Portal Identity"
