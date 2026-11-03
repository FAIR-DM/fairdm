# How to customise the profile form

A person edits their own profile, an organization's owner and administrators edit its profile, and a Community Manager edits the profiles nobody else can. This guide changes which fields that editing page offers, by replacing the shipped form with a subclass of your own. Use it when your portal needs a field the page leaves out, or wants to hide one it shows.

## Steps

1. Subclass the shipped form for the kind of contributor you are changing. This form adds the person's `config` field, which the shipped form leaves out, and puts it under a heading of its own. `config` is a field of `Person`, so the model form saves it with no further code.

   ```python
   # myportal/forms.py
   from django.utils.translation import gettext_lazy as _

   from fairdm.contrib.contributors.forms.profile import (
       PersonProfileForm as BasePersonProfileForm,
   )


   class PersonProfileForm(BasePersonProfileForm):
       class Meta(BasePersonProfileForm.Meta):
           fields = [*BasePersonProfileForm.Meta.fields, "config"]

       sections = (
           *BasePersonProfileForm.sections,
           (_("Portal settings"), ["config"]),
       )
   ```

   A field that no section names is drawn after the last section, so `sections` is only needed to give the field a heading or a place of its own.

2. To hide a field, leave it out of `Meta.fields`. This form drops the languages:

   ```python
   class PersonProfileForm(BasePersonProfileForm):
       class Meta(BasePersonProfileForm.Meta):
           fields = [
               name for name in BasePersonProfileForm.Meta.fields if name != "lang"
           ]
   ```

   A field declared on the form but missing from `Meta.fields` is removed from the form. The organization form needs one more rule: if you keep `website`, keep `links` as well, because the website is stored as the first of the links.

3. Name your form in `FAIRDM_PROFILE_FORMS`. The setting maps the kind of contributor, `person` or `organization`, to a dotted path. A kind you leave out keeps the shipped form.

   ```python
   # settings.py
   FAIRDM_PROFILE_FORMS = {
       "person": "myportal.forms.PersonProfileForm",
   }
   ```

   To set the setting without replacing FairDM's other values, see [How to override a FairDM setting](override-a-fairdm-setting.md).

4. Open a person's editing page. `Contributor.get_update_url()` gives its address. Sign in as the person to see their own page.

## The result

The editing page shows your form for the kind of contributor you named. It saves what is entered and returns to the profile. The form needs no `<form>` tag or buttons, which the page supplies. A field you added from the model is saved with the profile.

For the fields of the shipped forms and the rules of `sections` and `LinesField`, see [Contributor models](../reference/contributor-models.md#profile-forms). For the setting, see [Settings](../reference/settings.md).
