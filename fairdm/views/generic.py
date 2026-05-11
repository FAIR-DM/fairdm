from django.db.models.base import Model as Model
from django.utils.translation import gettext as _
from mvp.views import MVPHomeView

FAIRDM_LANDING_PAGE_HERO = {
    "title": _("Welcome to FairDM"),
    "subtitle": _("Community Portal"),
    "lead": _("A FairDM-powered portal for FAIR-data driven communities."),
    "image": "fairdm/landing_hero.png",
}


class FairDMHomeView(MVPHomeView):
    page_subtitle = "Welcome"
    page_title = "Getting started"
    template_name_user = "fairdm/dashboard.html"
    template_name_anon = "fairdm/landing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hero_content"] = FAIRDM_LANDING_PAGE_HERO
        return context

    def get_page_subtitle(self):
        if self.request.user.is_authenticated:
            return f"Welcome, {self.request.user.first_name or self.request.user.username}!"
        return self.page_title

    def get_page_title(self):
        if self.request.user.is_authenticated:
            return _("My Dashboard")
        return self.page_title
