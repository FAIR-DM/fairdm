from django.contrib import admin
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.fields import ThumbnailerImageField
from parler.models import TranslatableModel, TranslatedFields
from solo.models import SingletonModel


def brand_asset_path(instance, filename: str) -> str:
    """
    Generate upload paths for brand assets (logos and icons).

    Creates predictable paths for identity branding files to enable
    reliable URL resolution in templates and settings.

    Args:
        instance: The model instance (Authority or Identity)
        filename: The original uploaded filename

    Returns:
        Path in format: identity/{model_name}_{field}.{ext}
        Example: identity/portal_logo_light.svg
    """
    # Get the field name that's being saved (e.g., 'logo_light', 'icon_dark')
    # This is a bit tricky since we don't have direct access to the field name
    # We'll use a simpler approach: slugify model name + filename
    model_name = slugify(instance._meta.verbose_name)
    return f"identity/{model_name}_{filename}"


class BrandAssets(models.Model):
    """
    Abstract mixin providing brand asset fields for light/dark theme variants.

    Provides logo and icon fields with theme-specific variants to support
    both light and dark color schemes. Uses ThumbnailerImageField for
    automatic thumbnail generation.

    Fields:
        logo_light: Logo optimized for light theme backgrounds
        logo_dark: Logo optimized for dark theme backgrounds
        icon_light: Small icon/favicon for light theme
        icon_dark: Small icon/favicon for dark theme
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
        short_name=models.CharField(_("Short Name"), max_length=255, blank=True, null=True),
        description=models.TextField(_("Description")),
    )

    class Meta:
        verbose_name = _("Governing Authority")

    # def __str__(self):
    #     return force_str(self.name)


class Identity(BrandAssets, SingletonModel, TranslatableModel):
    """Portal identity configuration including branding and metadata."""

    keywords: models.ManyToManyField = models.ManyToManyField(
        "research_vocabs.Concept",
        verbose_name=_("Keywords"),
        help_text=_("A set of keywords from controlled vocabularies describing the portal."),
        blank=True,
    )

    translations = TranslatedFields(
        name=models.CharField(_("Name"), max_length=255),
        short_name=models.CharField(_("Short Name"), max_length=255, blank=True, null=True),
        description=models.TextField(_("Description")),
    )

    class Meta:
        db_table = "identity_database"  # Preserve existing table name
        verbose_name = _("Portal Identity")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update admin site branding with portal name
        name = self.safe_translation_getter("name", default="FairDM")
        admin.site.site_header = name
        admin.site.site_title = name

    def __str__(self):
        return "Portal Identity"


# class Configuration(SingletonModel):
#     logo = models.ImageField(
#         _("Logo"),
#         null=True,
#         blank=True,
#     )
#     icon = models.ImageField(
#         _("Icon"),
#         null=True,
#         blank=True,
#     )
#     theme = models.JSONField(
#         _("theme"),
#         default=dict,
#     )

#     class Meta:
#         verbose_name = _("Site Configuration")

#     def __str__(self):
#         return force_str(_("Site Configuration"))
