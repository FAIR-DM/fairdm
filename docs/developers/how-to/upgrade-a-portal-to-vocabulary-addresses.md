# How to upgrade a portal to vocabulary addresses

FairDM now stores every controlled term as the address of a concept in a published vocabulary, through [django-controlled-vocabularies](https://pypi.org/project/django-controlled-vocabularies/) 0.3. It no longer installs django-research-vocabs, which stored a term by its name, such as `Abstract` or `unknown`, and kept keywords and contributor roles in tables of its own. You follow this guide once, when you move a portal that already holds data to the FairDM release that includes the change. A new portal needs none of it: `migrate` and then `sync_vocabularies` set it up.

## Before you start

- Back up the database, and read [How to back up a portal](back-up-a-portal.md) if the scheduled backups are not running. The command in step 5 changes the tables of every record that carries a description, date, identifier, keyword, contributor role or sample status, and a backup is the only way back.
- Run the whole procedure against a copy of the database first.
- On PostgreSQL, the database user that runs the migrations must be allowed to create the `pg_trgm` extension, or the extension must exist already. A migration of django-controlled-vocabularies enables it for concept search. To create it once as a superuser:

  ```bash
  psql --dbname my_portal --command "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
  ```

## Steps

1. Change the portal's own code that names a term. A description, date or identifier type, a contributor role and a sample status are now concepts, stored by their address:

   ```python
   from fairdm.core.vocabularies import ABSTRACT, CREATOR, DOI, DESCRIPTION_TYPES

   dataset.descriptions.filter(type=ABSTRACT)
   dataset.descriptions.create(type_id=f"{DESCRIPTION_TYPES}/methods", value="...")
   project.add_contributor(person, with_roles=[CREATOR])
   ```

   The `type` of a description, date or identifier row and `Sample.status` return the concept. Read `row.type_id` for its address and `row.get_type_label()` for its name. The roles of a contribution and the keywords of a record are concepts too. A concept's address is its vocabulary's address, a slash and the concept's identifier, and the name it used to be stored under is its `skos:notation` in the vocabulary's file: `Abstract` is `https://w3id.org/fairdm/vocabularies/description-types/abstract`. [Controlled vocabularies](../../explanation/controlled-vocabularies.md) explains the layout.

2. Change the `FAIRDM_PROJECT["keywords"]` setting, if the portal sets it, so that it lists the addresses of the keyword vocabularies rather than Python classes:

   ```python
   FAIRDM_PROJECT = {
       "keywords": ["https://vocab.example.org/research-topics"],
   }
   ```

3. Install the new FairDM release. It depends on django-controlled-vocabularies 0.3.1 or a later 0.3 release from PyPI and no longer on django-research-vocabs. If the portal's own code imports `research_vocabs`, port it to [django-controlled-vocabularies' concept fields](https://github.com/FAIR-DM/django-controlled-vocabularies/blob/main/docs/how-to/attach-a-concept-to-a-model.md) first. Remove `research_vocabs` from the portal's own `INSTALLED_APPS` if it lists it. FairDM adds `controlled_vocabularies` itself.

4. Declare the vocabularies the portal loads. FairDM's fields name their vocabularies by address. Until those addresses are published, download the nine files in `vocabularies/` from [FAIR-DM/fairdm-vocabularies](https://github.com/FAIR-DM/fairdm-vocabularies), keep them with the portal, and declare each one:

   ```python
   CONTROLLED_VOCABULARIES = {
       slug: {"source": BASE_DIR / "vocabularies" / f"{slug}.ttl"}
       for slug in (
           "contributor-roles",
           "date-types",
           "description-types",
           "identifier-types",
           "organization-types",
           "project-status",
           "relation-types",
           "sample-relation-types",
           "sample-status",
       )
   }
   ```

   Declare every other vocabulary the portal's keywords come from as well, by a file the vocabulary's publisher provides. A keyword whose vocabulary is not loaded cannot be converted.

5. Move the database across. `upgrade_vocabularies` runs before anything else touches the database. Its first run creates the tables of django-controlled-vocabularies and stops, so that the vocabularies can be loaded into them. Then load them, run the command again, and migrate:

   ```bash
   python manage.py upgrade_vocabularies
   python manage.py sync_vocabularies
   python manage.py upgrade_vocabularies
   python manage.py migrate
   ```

   The second run matches every stored term before it writes anything:

   - A description, date or identifier type and a sample status are matched to the concept of their field's vocabulary whose `skos:notation` is the stored name.
   - A keyword or role from one of FairDM's own vocabularies is matched by notation in the same way. One from any other vocabulary is matched by the address django-research-vocabs held for it.

   If any stored term has no match, the command lists every one of them and changes nothing. Load the vocabulary it comes from, or correct the stored value, and run it again. Once it succeeds, the tables of django-research-vocabs are gone.

   A portal that runs in a container migrates as soon as its web container starts, and that migration fails on the old tables. Stop the old web, worker and scheduler containers, then run the three commands in one-off containers of the new image before starting the new ones:

   ```bash
   docker run --rm --env-file /etc/my-portal/portal.env my-portal python manage.py upgrade_vocabularies
   docker run --rm --env-file /etc/my-portal/portal.env my-portal python manage.py sync_vocabularies
   docker run --rm --env-file /etc/my-portal/portal.env my-portal python manage.py upgrade_vocabularies
   ```

   The web container then runs `migrate` itself when it starts. See [How to deploy a portal in a container](deploy-a-portal-in-a-container.md).

6. Remove the stale content types of the old app.

   ```bash
   python manage.py remove_stale_contenttypes
   ```

   It asks before it deletes.

7. Run `python manage.py sync_vocabularies` on every deploy from now on, so a portal picks up new terms when the vocabularies are released again.

## The result

Every term a record carries is stored as the address of a concept, which can be followed to its definition and its translations, and the keywords and roles of every record point at the vocabularies the portal has loaded. The descriptions, key dates and identifiers pages offer the same types as before, in the same order.
