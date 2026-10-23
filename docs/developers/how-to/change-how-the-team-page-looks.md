# How to change how the team page looks

The **Team** page, under **Community**, lists each portal role with the active people who hold it. This guide changes how each person is drawn, by giving the page a card template of your own. Use it when the shipped contributor card does not fit your portal's design.

What the page lists is not configurable. It reads `PortalRoles`, so the page and the rights always agree.

## Steps

1. Write the card template. The page draws it once for each holder, and passes the person as `object`.

   ```django
   {# myportal/templates/myportal/team_member.html #}
   <div class="card bg-base-100 shadow-sm">
     <div class="card-body">
       <h3 class="card-title">
         <a href="{{ object.get_absolute_url }}">{{ object.name }}</a>
       </h3>
       {% if object.primary_organization %}
         <p>{{ object.primary_organization }}</p>
       {% endif %}
     </div>
   </div>
   ```

   The page prefetches each person's affiliations, identifiers and groups, so reading `primary_organization` costs no query per person.

2. Subclass `TeamView` and point `list_item_template` at your template. To change the grid the cards sit in, set `grid_config` too.

   ```python
   # myportal/views.py
   from fairdm.contrib.contributors.views.team import TeamView


   class PortalTeamView(TeamView):
       """The same people, drawn with the portal's own card."""

       list_item_template = "myportal/team_member.html"
       grid_config = {"cols": 1, "md": 2, "lg": 3, "gap": 6}
   ```

3. Route the same address to your view, ahead of FairDM's URLs. Django uses the first pattern that matches, so your route has to come before the include.

   ```python
   # config/urls.py
   from django.urls import include, path

   from myportal.views import PortalTeamView

   urlpatterns = [
       path("community/team/", PortalTeamView.as_view(), name="team"),
       path("", include("fairdm.conf.urls")),
   ]
   ```

   The name `team` is the one the **Community** menu reverses, so the menu entry keeps working.

4. Open **Community**, then **Team**.

## The result

The **Team** page draws each holder with your card, in your grid. The page still lists the same people and roles, in the order of the roles. The attributes of `TeamView` are listed in [Portal roles in code](../reference/portal-roles.md#teamview). To use FairDM's own card in your template, see [Components](../reference/components.md).
