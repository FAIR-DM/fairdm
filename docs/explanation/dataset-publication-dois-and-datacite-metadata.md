# Dataset publication, DOIs and DataCite metadata

This page explains what "published" means for a dataset in a FairDM portal, what a portal does and does not do about DOIs, and how a portal describes a dataset in the DataCite metadata schema so that an external service can publish it. It covers the design and its limits. It does not walk through recording an identifier or exporting metadata, which are tasks for the dataset's team and for the portal's developers.

## Two meanings of "published"

The word is used in two senses, and a portal only does one of them.

- **Released inside the portal.** A dataset has a `published` flag, set in the administration interface. It decides whether the samples and measurements held in the dataset may be shown to people outside its team. This is what the portal means by "published" in its listings and in its API.
- **Formally published with a DOI.** A data repository, such as a service that registers DOIs with DataCite, accepts the dataset, assigns it a persistent identifier and commits to keeping it. A FairDM portal does not do this.

The flag is separate from the dataset's visibility, which decides whether its own page can be read. The two flags and the reasons for keeping them apart are explained in [How access to a record is decided](how-access-to-a-record-is-decided.md). The flag is set in the administration interface and nowhere a researcher can reach, so that releasing data is never a single click on the dataset page. Putting the control with administrators is deliberate: a control on the researcher's own page is where they would look for it, and that is the argument against placing it there. Every dataset starts unpublished. See [ADR 0014](../adr/0014-publication-is-a-separate-flag-from-visibility.md).

## What a portal does about DOIs

A FairDM portal does not register or assign DOIs. It does not contact DataCite or any other registration agency. A DOI is an identifier issued by a registry after a repository has accepted the dataset, so a portal can neither create one nor promise that a dataset will receive one.

What a portal does is hold and use a DOI that someone else has issued:

- **A dataset can carry a DOI as one of its identifiers.** The team records it on the dataset's identifiers page. Identifiers of type DOI link to the DOI resolver on the dataset's page.
- **A citation uses the DOI when there is one.** The citation on a dataset's page is written in DataCite's form: creators, year, title, publisher and identifier. The identifier is the DOI link if the dataset has one, and the dataset's own page address if it does not.
- **A dataset can point at its own data publication.** A dataset can name a literature item as its data reference. When it does, the page cites that publication instead of itself, because a published data paper or repository record is the thing to cite.
- **Changing a licence on a dataset that has a DOI triggers a warning in the administration interface.** The metadata held by the registry, such as DataCite or Crossref, may then need updating.

The reason a portal stops here is that formal publication is a commitment by a repository, and a portal is not one. A portal organises data for a research group or community. A repository takes responsibility for preserving a dataset and keeping its identifier resolving over the long term. Treating the two as one would let a portal imply a preservation promise that nobody has made.

## Helping a dataset reach a repository

Because the step to a repository happens elsewhere, the portal helps a team get ready for it, and gives the repository what it needs.

### The readiness checklist

On a dataset's page, people who manage the dataset see a checklist while the dataset is not yet public and published. It is headed "Ready to publish?" and lists what a data repository needs before it can accept the dataset. The list is drawn from DataCite's mandatory and recommended properties and from what a formal submission needs to go in unaided. It marks some items as required and some as recommended.

| Item | Required |
|---|---|
| An abstract describes the data | Yes |
| The methods are described | Yes |
| At least one creator is credited | Yes |
| Someone is named as the contact | Yes |
| A licence is chosen | Yes |
| The dataset holds samples or measurements | Yes |
| The collection period is recorded | Yes |
| Keywords make it findable | No |
| A related publication is linked | No |
| The dataset is public | No |

Items with a page that fixes them link to it.

### Credits in DataCite's shape

A credit on a record carries the properties DataCite defines for a creator or contributor: a name, whether it is a personal or organizational name, given and family names for a person, identifiers with their scheme, and the organization the person was credited from. The reasoning is in [Why FairDM records contributors](why-fairdm-records-contributors.md) and [ADR 0030](../adr/0030-a-credit-carries-what-datacite-asks-of-a-creator.md).

Which credits are creators and which are contributors is decided by the export, not by the credit. The portal's roles are finer than DataCite's contributor types, and a portal can add its own. In the exports a portal ships, a credit with the Creator role becomes a DataCite creator. Any other role becomes a contributor.

For a dataset's XML, the role's name is written as the contributor type. For a project's JSON, a small table maps the project roles to DataCite types, and any role not in the table becomes "Other". A portal with its own roles can find that DataCite has no type of the same meaning, so it should decide how those roles map when it exports.

## What the portal can export

There are two ways to get DataCite-shaped metadata out of a portal.

- **A dataset as DataCite XML.** `build_metadata` in `fairdm.contrib.import_export.utils` renders a dataset as XML against DataCite schema 4.4. It carries the creators, the contributors, subjects drawn from the dataset's keywords, dates, a related identifier pointing at the dataset's page, the licence as rights, the descriptions, and a geographic box. It leaves the publisher empty and takes the publication year from the day it is rendered, because the portal does not know who will publish the dataset or when. A team or repository fills those in. The shipped URL configuration registers no route to download it, so a portal that wants a download link adds a view that calls the function.
- **Projects as DataCite JSON.** The administration interface for projects has an action that exports the selected projects as DataCite JSON, and another that exports them as JSON. In the DataCite form, the resource type is "Project", a DOI becomes the primary identifier and every other identifier becomes an alternate identifier, and funding is carried as DataCite funding references.

Neither export submits anything. They produce a file for a person or a service to use.

### Where a dataset is on the map

The geographic section of the XML is a single box that holds the locations of the dataset's records. It is the box a visitor would see, whoever asks for the metadata, because published metadata is public. A location the public may not see does not count towards it, and a dataset with nothing a visitor may see located carries no geographic section. The reasoning is in [How locations are stored and protected](how-locations-are-stored-and-protected.md).

## Limits

- A portal does not mint DOIs, check that a DOI resolves, or keep a DOI's registry record up to date.
- The `published` flag is a release decision inside the portal. It does not mean a dataset has been accepted by a repository.
- The XML export is a starting point. It does not fill in every DataCite property, and a repository may ask for more.
- The readiness checklist reports what is present in the portal. It cannot tell you whether a particular repository will accept the dataset.

## Where to go next

- [Datasets](../users/datasets/datasets.md) and [Identifiers](../users/datasets/identifiers.md) describe the screens where a team records a DOI.
- [How to export projects as JSON or DataCite JSON](../administrators/how-to/export-projects.md) covers the project export.
- [REST API](../developers/reference/rest-api.md) lists how credits and identifiers appear in the API.
