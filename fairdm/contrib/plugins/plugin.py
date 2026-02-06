from __future__ import annotations

from django import urls
from django.db.models.base import Model as Model
from django.forms.widgets import Media
from django.utils.translation import gettext_lazy as _

from .config import PluginConfig, PluginMenuItem

# Plugin category constants
EXPLORE = "explore"
ACTIONS = "actions"
MANAGEMENT = "management"


class FairDMPlugin:
    """
    Base mixin for FairDM plugins.

    All plugin classes must inherit from this mixin to access the parent view's
    menus and other functionality.

    Plugins can be configured using either the new PluginConfig approach or
    the legacy attribute approach:

    New way (preferred):
        class OverviewPlugin(FairDMPlugin, TemplateView):
            config = PluginConfig(
                title=_("Overview"),
                icon="view",
                category=plugins.EXPLORE,
            )

    Legacy way (still supported):
        class OverviewPlugin(FairDMPlugin, TemplateView):
            title = "Overview"
            menu_item = PluginMenuItem(name="Overview", icon="view", category=plugins.EXPLORE)
    """

    config: PluginConfig | None = None
    menu_item: PluginMenuItem | None = None
    title: str = "Unnamed Plugin"

    def get_config(self) -> PluginConfig | None:
        """Get the plugin configuration, checking config first then falling back to attributes."""
        if self.config is not None:
            return self.config
        return None

    def get_title(self) -> str:
        """Get the plugin title from config or fallback to title attribute."""
        if self.config is not None:
            return self.config.title
        return self.title

    def get_menu_item(self) -> PluginMenuItem | None:
        """Get the menu item from config or fallback to menu_item attribute."""
        if self.config is not None:
            return self.config.get_menu_item()
        return self.menu_item

    def get_about(self) -> str | None:
        """Get the about text from config or fallback to about attribute."""
        if self.config is not None:
            return self.config.about
        return getattr(self, "about", None)

    def get_learn_more(self) -> str | None:
        """Get the learn_more link from config or fallback to learn_more attribute."""
        if self.config is not None:
            return self.config.learn_more
        return getattr(self, "learn_more", None)

    @property
    def media(self):
        """
        Return the Media object for this plugin if defined.

        Plugins can define a Media inner class with custom CSS and JS files.
        This property checks for the Media class and returns it if available.
        """
        if hasattr(self.__class__, "Media"):
            return Media(self.__class__.Media)
        return Media()

    def get_breadcrumbs(self) -> list[dict[str, str]]:
        """
        Return a list of breadcrumb items for navigation.

        Each breadcrumb is a dictionary with:
        - 'text': The display text for the breadcrumb (required)
        - 'href': The URL for the breadcrumb (optional)

        Breadcrumb logic:
        1. First item: Points to user's base_model list view if user is a contributor
           and object is editable (not published), otherwise points to public list view
        2. Second item: Truncated object.__str__ representation pointing to overview plugin
        3. Additional items: Page title with no href

        Example:
            [
                {'text': 'My Projects', 'href': '/user/projects/'},
                {'text': 'My Research Project', 'href': '/project/abc123/overview/'},
                {'text': 'Datasets'}  # Current page title
            ]

        Returns:
            list[dict[str, str]]: List of breadcrumb dictionaries
        """
        breadcrumbs = []

        # Only generate breadcrumbs if we have a base_object
        if not hasattr(self, "base_object") or not self.base_object:
            return breadcrumbs

        base_object = self.base_object
        model_name = base_object._meta.model_name
        model_verbose_name_plural = base_object._meta.verbose_name_plural

        # Determine the namespace - for polymorphic models, use the base model
        # The base_model attribute is set on the PluggableView subclass
        namespace = model_name
        if hasattr(self, "base_model") and self.base_model:
            namespace = self.base_model._meta.model_name

        # Determine if user is contributor and object is editable
        # user = getattr(self.request, "user", None)
        # is_contributor = user and user.is_authenticated and base_object.is_contributor(user)

        # Check if object is editable (not published/public)
        # For projects, check visibility; for other models, you might check different fields
        # is_editable = True
        # if hasattr(base_object, "visibility"):
        #     from fairdm.utils.choices import Visibility

        #     is_editable = base_object.visibility != Visibility.PUBLIC

        # Point to public list view
        breadcrumbs.append(
            {"text": _(f"All {model_verbose_name_plural.title()}"), "href": urls.reverse(f"{model_name}-list")}
        )

        # Second breadcrumb: Object overview with truncated name
        object_str = str(base_object)
        # Truncate to 50 characters
        if len(object_str) > 30:
            object_str = object_str[:27] + "..."

        breadcrumbs.append(
            {"text": object_str, "href": urls.reverse(f"{namespace}:overview", kwargs={"uuid": base_object.uuid})}
        )

        # Third breadcrumb: Current page title (no href)
        title = self.get_title() if hasattr(self, "get_title") else getattr(self, "title", None)
        if title:
            breadcrumbs.append({"text": str(title)})

        return breadcrumbs

    def get_context_data(self, **kwargs):
        """Add plugin menus to the template context."""
        context = super().get_context_data(**kwargs)
        context["menus"] = self.menus
        # context["breadcrumbs"] = self.get_breadcrumbs()
        context["plugin_media"] = self.media
        # Add title to context using get_title() method
        if hasattr(self, "get_title"):
            context["title"] = self.get_title()
        return context
