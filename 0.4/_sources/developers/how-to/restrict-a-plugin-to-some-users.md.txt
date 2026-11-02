# How to restrict a plugin to some users

A plugin's tab and its page are open to everyone who can reach the record until you give it a rule. You restrict one when only some people should see the tab or open the page.

## Before you start

You need a plugin. See [How to create a plugin](create-a-plugin.md).

A plugin has two settings that decide who gets in, and they are one guarantee. A page that is not shown cannot be reached, and a page that cannot be reached is not shown. The tab and the page both ask the same function, which reads the plugin's `check` and `permission`. See [Plugins](../reference/plugins.md) for both.

## Steps

1. To hide the plugin from records it does not suit, or from people it is not for, set `check`. It receives the request and the record, and returns a bool.

   ```python
   from fairdm import plugins
   from fairdm.core.sample.models import Sample
   from fairdm.plugins import Plugin, is_instance_of
   from fairdm.views import FairDMTemplateView
   from myapp.models import CoreSample


   @plugins.register(Sample, label="Petrology")
   class Petrology(Plugin, FairDMTemplateView):
       check = staticmethod(is_instance_of(CoreSample))
   ```

   `CoreSample` stands for a sample type of your own. The tab appears only on samples of that type.

   Write `check` as a plain function, a lambda or a `staticmethod`. Registration refuses a `classmethod`, because it is truthy but cannot be called and would let everyone in.

2. To require a permission, set `permission` on the plugin or on each view.

   ```python
   from fairdm.views import FairDMUpdateView


   @plugins.register(Sample, label="Curate")
   class Curate(Plugin, FairDMUpdateView):
       permission = "sample.change_sample"
   ```

   A permission counts when the user holds it for the whole portal or on this record. Give a list to require all of them.

3. If the record can be private, write its visibility rule yourself. A plugin reads its record through the model's `all_objects` manager when the model has one, which skips the filtering of the default manager. A private record therefore reaches the plugin, and the plugin must refuse it. This is the rule FairDM's project pages use:

   ```python
   from fairdm.plugins import has_perm
   from fairdm.utils.choices import Visibility


   def project_is_visible(request, obj):
       """A public project always, a private one only with project.view_project."""
       if obj is None:
           return True
       if obj.visibility == Visibility.PUBLIC:
           return True
       return has_perm(request, "project.view_project", obj)
   ```

   Set it as `check = staticmethod(project_is_visible)` on every plugin registered against projects.

4. To answer 404 for a private record instead of a sign-in redirect or a permission error, list `PrivateRecordNotFoundMixin` before `Plugin`.

   ```python
   from fairdm.contrib.plugins.mixins import PrivateRecordNotFoundMixin
   from fairdm.core.project.models import Project


   @plugins.register(Project, label="Review")
   class Review(PrivateRecordNotFoundMixin, Plugin, FairDMTemplateView):
       check = staticmethod(project_is_visible)
   ```

   A 403 or a redirect would tell whoever typed the address that something exists there. A refusal on a public record is the usual one, so the person is told why. The mixin reads `visibility` from the record, so it suits projects and datasets.

## The result

A person who fails the rule does not see the tab. If they type the address, they get the refusal: a sign-in redirect when they are signed out, a permission error when they are signed in, or a 404 with the mixin on a private record.

Each page states its own rule. An additional view in `extra_views` takes nothing from its plugin, so give each one its own `check` or `permission`. See [How to add pages to a plugin](add-pages-to-a-plugin.md). The reason is recorded in [Every page states its own access rules](../../adr/0012-every-page-states-its-own-access-rules.md).

How a person comes to hold a permission on a record is explained in [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).
