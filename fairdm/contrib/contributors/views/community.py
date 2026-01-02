"""Community dashboard view for contributor statistics and insights."""

import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Count
from django.utils import timezone
from django.utils.translation import gettext as _

from fairdm.views import FairDMTemplateView

from ..choices import DefaultGroups
from ..models import Contribution, Contributor, Organization, OrganizationMember, Person

User = get_user_model()


class CommunityDashboardView(FairDMTemplateView):
    """Dashboard view showing community statistics and contributor insights.

    Displays comprehensive statistics about:
    - Contributors (people and organizations)
    - Active users and portal team
    - Contributions and collaborations
    - Geographic distribution
    - Recent activity trends
    """

    template_name = "pages/community_dashboard.html"
    title = _("Community Dashboard")
    heading_config = {
        "icon": "speedometer2",
        "title": _("Community Dashboard"),
        "description": _(
            "Overview of our research community including contributors, organizations, "
            "collaborations, and recent activity."
        ),
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # === Contributor Statistics ===
        total_contributors = Contributor.objects.count()
        total_people = Person.objects.count()
        total_organizations = Organization.objects.count()

        # Active contributors (those with at least one contribution)
        active_contributors = Contributor.objects.filter(contributions__isnull=False).distinct().count()

        # Contributors with external identifiers
        contributors_with_identifiers = Contributor.objects.filter(identifiers__isnull=False).distinct().count()

        context.update(
            {
                "total_contributors": total_contributors,
                "total_people": total_people,
                "total_organizations": total_organizations,
                "active_contributors": active_contributors,
                "contributors_with_identifiers": contributors_with_identifiers,
            }
        )

        # === User Statistics ===
        total_users = User.objects.filter(is_active=True, is_superuser=False).count()
        verified_users = (
            User.objects.filter(is_active=True, is_superuser=False, emailaddress__verified=True).distinct().count()
        )

        # Recent users (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_users = User.objects.filter(is_active=True, is_superuser=False, date_joined__gte=thirty_days_ago).count()

        context.update(
            {
                "total_users": total_users,
                "verified_users": verified_users,
                "recent_users": recent_users,
            }
        )

        # === Portal Team Statistics ===
        portal_admins = Group.objects.get(name=DefaultGroups.PORTAL_ADMIN).user_set.count()
        data_admins = Group.objects.get(name=DefaultGroups.DATA_ADMIN).user_set.count()
        developers = Group.objects.get(name=DefaultGroups.DEVELOPERS).user_set.count()

        context.update(
            {
                "portal_admins": portal_admins,
                "data_admins": data_admins,
                "developers": developers,
                "total_staff": portal_admins + data_admins + developers,
            }
        )

        # === Contribution Statistics ===
        total_contributions = Contribution.objects.count()

        # Contributions by content type
        contribution_breakdown = (
            Contribution.objects.values("content_type__model").annotate(count=Count("id")).order_by("-count")
        )

        context.update(
            {
                "total_contributions": total_contributions,
                "contribution_breakdown": contribution_breakdown,
            }
        )

        # === Organization & Affiliation Statistics ===
        total_affiliations = OrganizationMember.objects.count()
        current_affiliations = OrganizationMember.objects.filter(is_current=True).count()

        # Organizations by country (top 10)
        from django_countries import countries

        orgs_by_country = (
            Organization.objects.exclude(country="")
            .values("country")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # Serialize country data for chart
        country_chart_data = [
            {
                "country": countries.name(item["country"]),
                "count": item["count"],
            }
            for item in orgs_by_country
        ]

        context.update(
            {
                "total_affiliations": total_affiliations,
                "current_affiliations": current_affiliations,
                "orgs_by_country": orgs_by_country,
                "country_chart_data_json": json.dumps(country_chart_data),
            }
        )

        # === Top Contributors ===
        top_contributors = (
            Contributor.objects.annotate(contribution_count=Count("contributions"))
            .filter(contribution_count__gt=0)
            .order_by("-contribution_count")[:10]
        )

        # Separate lists for people and organizations
        top_people = (
            Person.objects.annotate(contribution_count=Count("contributions"))
            .filter(contribution_count__gt=0)
            .order_by("-contribution_count")[:10]
        )

        top_organizations = (
            Organization.objects.annotate(contribution_count=Count("contributions"))
            .filter(contribution_count__gt=0)
            .order_by("-contribution_count")[:10]
        )

        context.update(
            {
                "top_contributors": top_contributors,
                "top_people": top_people,
                "top_organizations": top_organizations,
            }
        )

        # === Recent Activity ===
        recent_contributors = Contributor.objects.order_by("-added")[:5]

        context.update({"recent_contributors": recent_contributors})

        # === Identifier Statistics ===
        orcid_count = Contributor.objects.filter(identifiers__type="ORCID").distinct().count()
        ror_count = Contributor.objects.filter(identifiers__type="ROR").distinct().count()

        context.update(
            {
                "orcid_count": orcid_count,
                "ror_count": ror_count,
            }
        )

        # === Growth Data for Charts (last 12 months) ===
        monthly_data = []
        for i in range(11, -1, -1):
            month_start = timezone.now().replace(day=1) - timedelta(days=30 * i)
            month_end = (month_start + timedelta(days=32)).replace(day=1)

            contributors_count = Contributor.objects.filter(added__gte=month_start, added__lt=month_end).count()

            users_count = User.objects.filter(
                date_joined__gte=month_start, date_joined__lt=month_end, is_superuser=False
            ).count()

            monthly_data.append(
                {
                    "month": month_start.strftime("%b %Y"),
                    "contributors": contributors_count,
                    "users": users_count,
                }
            )

        context.update({"monthly_data": monthly_data})

        # Serialize monthly data for JavaScript
        context["monthly_data_json"] = json.dumps(monthly_data)

        return context
