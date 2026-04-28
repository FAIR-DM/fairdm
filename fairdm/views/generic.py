from django.db.models.base import Model as Model
from django.utils.translation import gettext as _
from mvp.views.extra import MVPHomeView


class FairDMHomeView(MVPHomeView):
    page_title = _("Dashboard")
    page_subtitle = "FairDM"
    template_name_user = "fairdm/dashboard.html"
    template_name_anon = "fairdm/landing.html"
