# How to filter projects by vocabulary keywords

This guide gives the project list one filter for each controlled vocabulary you choose, so visitors can narrow projects by science keywords, platforms, instruments or any other vocabulary your portal uses. It covers filtering only. It does not cover how a project gets its keywords.

## Before you start

- You have a vocabulary class, a `VocabularyBuilder` subclass from `research_vocabs`, whose concepts are in the database. To write one, see [How to use a controlled vocabulary in a model](use-a-controlled-vocabulary-in-a-model.md). For what a controlled vocabulary is, see [Controlled vocabularies](../../explanation/controlled-vocabularies.md).
- At least one project carries a concept of the vocabulary as a keyword. The filter offers only the concepts that a project uses.

## Steps

1. Open the settings module that calls `fairdm.setup()`.

2. After the `fairdm.setup()` call, set `FAIRDM_PROJECT` with the dotted import path of each vocabulary class under `"keywords"`.

   ```python
   import fairdm

   fairdm.setup()

   FAIRDM_PROJECT = {
       "keywords": [
           "myportal.vocabularies.ScienceKeywords",
           "myportal.vocabularies.Instruments",
       ],
   }
   ```

   The general rule for overriding a FairDM setting is in [How to override a FairDM setting](override-a-fairdm-setting.md). The setting itself is described in [Settings](../reference/settings.md).

3. Restart the portal.

## The result

The filter panel of the project list shows one filter for each vocabulary you listed. Each filter is named from its class, with the prefix `keywords_`, so `myportal.vocabularies.ScienceKeywords` becomes `keywords_ScienceKeywords`. The class name is its label, and the vocabulary's own `Meta.name` scopes the concepts the filter offers.

Each filter is a searchable list with a tick beside each chosen concept and a count in place of the chosen names. It lists only the concepts that at least one project uses.

Choosing two keywords in one filter keeps the projects that carry both, so each further keyword narrows the list. A keyword chosen in one vocabulary's filter and another chosen in a second vocabulary's filter also keep the projects that carry both.

If you set `"keywords"` to an empty list, the project list falls back to one `keywords` filter that spans every vocabulary and draws as a plain checkbox list.
