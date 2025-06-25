from cotton_bs5.views import CottonBS5ComponentMixin


class BaseLayout(CottonBS5ComponentMixin):
    """Base class for layouts

    Attributes:
        sidebar_primary (dict): Configuration object for the primary sidebar.
        sidebar_secondary (dict): Configuration object for the secondary sidebar.
    """

    sections = {
        "sidebar_primary": "sections.sidebar.primary",
        "sidebar_secondary": "sections.sidebar.secondary",
        "header": "layouts.header",
        "heading": "sections.heading",
    }
    sidebar_primary_config = {
        "breakpoint": "md",
        "class": "border-end",
        "width": "16rem",
    }
    # Config object provided to the primary sidebar

    sidebar_secondary_config = {
        "breakpoint": "md",
        "class": "border-start",
        "width": "15rem",
    }


class PageLayout(BaseLayout):
    """Base class for page layouts"""

    sections = {
        "heading": "sections.heading",
    }


class ApplicationLayout(BaseLayout):
    """Base class for application layouts"""

    layout = {
        "content_class": "h-100",
        "container_class": "px-0",
    }
    sections = {
        "sidebar_primary": False,
        "sidebar_secondary": False,
        "header": False,
    }


class FormLayout(PageLayout):
    """Base class for form layouts"""

    sections = {
        "sidebar_primary": "sections.sidebar.empty",
        "sidebar_secondary": "sections.sidebar.empty",  # hide the secondary sidebar
        "form": "components.form.default",
        "header": False,
    }
    # sidebar_primary_config = {
    #     "breakpoint": "md",
    #     "header": {
    #         "title": "",
    #     },
    # }
