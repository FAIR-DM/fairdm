from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class FairDMConfig(AppConfig):
    name = "fairdm"

    def ready(self) -> None:
        # adds a default renderer to all forms to keep a consistent look across the site. This way we don't have to specify it every time
        # patch django-filters to not use crispy forms. should be safe to remove on the
        # next release of fairdm

        autodiscover_modules("config")
        autodiscover_modules("plugins")

        from django_filters import compat

        compat.is_crispy = lambda: False

        return super().ready()
