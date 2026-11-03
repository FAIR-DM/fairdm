# How to filter projects by vocabulary keywords

This guide gives the project list one filter for each controlled vocabulary you choose, so visitors can narrow projects by science keywords, platforms, instruments or any other vocabulary your portal uses. It covers filtering only. It does not cover how a project gets its keywords.

## Before you start

- The vocabulary is loaded into the portal, declared in `CONTROLLED_VOCABULARIES` and loaded with `python manage.py sync_vocabularies`. See [How to use a controlled vocabulary in a model](use-a-controlled-vocabulary-in-a-model.md). For what a controlled vocabulary is, see [Controlled vocabularies](../../explanation/controlled-vocabularies.md).
- You know the address of the vocabulary's concept scheme.
- At least one project carries a concept of the vocabulary as a keyword. The filter offers only the concepts that a project uses.

## Steps

1. Open the settings module that calls `fairdm.setup()`.

2. After the `fairdm.setup()` call, set `FAIRDM_PROJECT` with the address of each vocabulary under `"keywords"`.

   ```python
   import fairdm

   fairdm.setup()

   FAIRDM_PROJECT = {
       "keywords": [
           "https://vocab.example.org/science-keywords",
           "https://vocab.example.org/instruments",
       ],
   }
   ```

   The general rule for overriding a FairDM setting is in [How to override a FairDM setting](override-a-fairdm-setting.md). The setting itself is described in [Settings](../reference/settings.md).

3. Restart the portal.

## The result

The filter panel of the project list shows one filter for each vocabulary you listed. Each filter is named from the last part of its vocabulary's address, with the prefix `keywords_`, so `https://vocab.example.org/science-keywords` becomes `keywords_science-keywords`. The vocabulary's own name is its label, and the filter offers only the concepts of that vocabulary.

Each filter is a searchable list with a tick beside each chosen concept and a count in place of the chosen names. It lists only the concepts that at least one project uses.

Choosing two keywords in one filter keeps the projects that carry both, so each further keyword narrows the list. A keyword chosen in one vocabulary's filter and another chosen in a second vocabulary's filter also keep the projects that carry both.

FairDM sets `"keywords"` to an empty list. The project list then has one `keywords` filter that spans every vocabulary and draws as a plain checkbox list.
