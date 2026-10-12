# Planning notes: people, organizations and a record's credits can be read through the API

Suggestions from the maintainer for research and planning, in his words. The plan answers each one
by name.

## Mirror DataCite for credits

"I would just probably try and mirror how DataCite does this, how they list contributors in their
metadata schema. From memory I think that they store first name, last name, probably an ORCID, a
primary affiliation I think in most cases. You can go online and find out what DataCite collects
exactly for these things. In essence, we want our records to be showing contributions that reflect
pretty much or pretty close to the DataCite standards. And we might throw in a few other things
there as well. We probably add in our own role types."

## Credits are for attribution only

"For contributions we don't want to show everything about the contributor. We don't need to show
their bio, we don't need to show their tags and their preferences and their keywords. For
serialising contribution data, we want to focus on what data is required to properly attribute
contributors and their affiliations."

## Lists stay light

"I don't think we should be including the full [profile]. Certainly not in the list views."

## Privacy is a later feature, and nothing private gets out before it

"We can't let any private information get out there. But what is considered private and what is
not considered private probably depends on each user. So we're going to have to raise an issue for
another feature enhancement that allows people to specify what information they're willing to
share through the API." That enhancement is #246.
