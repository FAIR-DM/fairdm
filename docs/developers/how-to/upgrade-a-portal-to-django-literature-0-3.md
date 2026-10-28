# How to upgrade a portal to django-literature 0.3

FairDM now installs [django-literature](https://pypi.org/project/django-literature/) 0.3.1 from PyPI, which stores each reference as a `literature.Item` instead of a `literature.LiteratureItem`. You follow this guide once, when you move a portal that already holds references to the FairDM release that includes the change.

## Before you start

- Back up the database, and read [How to back up a portal](back-up-a-portal.md) if the scheduled backups are not running. The command in step 4 changes the tables of the `literature` app, and a backup is the only way back.
- Run the whole procedure against a copy of the database first.
- Read the package's own guide, [Upgrade a database from the LiteratureItem schema](https://fair-dm.github.io/django-literature/how-to/upgrade-a-database-from-the-literatureitem-schema.html). It lists what the command converts, what it refuses to convert, and how it reports a reference it cannot read. This guide does not repeat it.

## Steps

1. Find every field in the portal's own models that points at the old model.

   ```bash
   grep -rn "literature.LiteratureItem\|literature.literatureitem" myportal/
   ```

   Change each `ForeignKey`, `OneToOneField` and `ManyToManyField` so that it names `literature.Item`.

   ```python
   reference = models.ForeignKey(
       "literature.Item",
       on_delete=models.SET_NULL,
       null=True,
       blank=True,
   )
   ```

   Change the code that reads the old model as well. An `Item` has the CSL variables as fields, so `item.title` stays and the dictionary in `item.item` is gone. Use `item.doi` and `item.year` in place of the DOI and the issued date, and `item.authors` for the names credited as authors.

2. Rewrite the portal's migrations that name the old schema. Edit them in place:

   - In `dependencies`, replace every `("literature", "<old migration>")` with `("literature", "0001_initial")`.
   - In `operations`, replace `to="literature.literatureitem"` with `to="literature.item"`.

   Do not create a new migration for the switch. Run `python manage.py makemigrations --check`. It reports no changes when every reference is rewritten.

3. Install the new FairDM release.

   ```bash
   pip install --upgrade fairdm
   ```

   The release depends on `django-literature[ui]` 0.3.1 or later, so the package and its front end arrive with it. django-select2 is no longer installed. If the portal's own code imports it, add it to the portal's dependencies.

4. Move the database across. Run `upgrade_literature` before anything else touches the database, then migrate.

   ```bash
   python manage.py upgrade_literature
   python manage.py migrate
   ```

   The command keeps every reference's primary key, so the links from your datasets stay in place. If it stops and names references it cannot convert, correct or delete them as the package's guide describes, and run it again.

   A portal that runs in a container migrates as soon as its web container starts, and that migration fails on the old tables. Stop the old web, worker and scheduler containers, then run the command in a one-off container of the new image before starting the new ones:

   ```bash
   docker run --rm --env-file /etc/my-portal/portal.env my-portal python manage.py upgrade_literature
   ```

   The web container then runs `migrate` itself when it starts. See [How to deploy a portal in a container](deploy-a-portal-in-a-container.md).

5. Remove the stale content types of the old model.

   ```bash
   python manage.py remove_stale_contenttypes
   ```

   It asks before it deletes, and lists permissions that were granted on the old model.

6. Grant the catalogue's maintainers the permissions they need. The catalogue's add, import, edit and delete pages now require `literature.add_item`, `literature.change_item` and `literature.delete_item`. Until now any visitor could use them. Grant the permissions to the people or groups who look after the references, in the admin under **Users** or **Groups**. Reading the catalogue stays open to everyone.

## The result

Every reference is a `literature.Item` with its authors, dates and identifiers in related tables, and every dataset keeps the publication it had. The **Literature** entry of the main menu opens the catalogue at `/literature/`. The old `/django-literature/` addresses are gone.

If the portal mounts the catalogue's addresses itself, point `path("literature/", include("literature.ui.urls"))` at the new URLconf in place of `literature.urls`.
