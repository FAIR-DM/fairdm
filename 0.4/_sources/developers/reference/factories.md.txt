# Test factories

FairDM ships [factory_boy](https://factoryboy.readthedocs.io/) factories for its models, so a portal's tests do not have to build projects, datasets, people and credits by hand. This page lists each factory, what it fills in for you, and the arguments it takes. It does not show how to use them in a test, which [How to test a portal with FairDM factories](../how-to/test-a-portal-with-fairdm-factories.md) does, and it does not explain why metadata is opt-in, which [Why factories create metadata only when asked](../explanation/why-factories-create-metadata-only-when-asked.md) does.

Import every factory from `fairdm.factories`:

```python
from fairdm.factories import DatasetFactory, PersonFactory, ProjectFactory
```

Each factory is a `DjangoModelFactory`. It takes any field of its model as a keyword argument, and it has the usual factory_boy methods: `create()`, `build()`, `create_batch(n)` and `build_batch(n)`. Calling the class creates a record and saves it.

## Arguments every record factory takes

`ProjectFactory`, `DatasetFactory`, `SampleFactory` and `MeasurementFactory` take these opt-in arguments. Nothing is created unless you pass one.

| Argument | Type | Creates |
|---|---|---|
| `descriptions` | `int` | That many descriptions on the record |
| `descriptions__types` | `list[str]` | The addresses of the types the descriptions take, in order |
| `dates` | `int` | That many key dates on the record |
| `dates__types` | `list[str]` | The addresses of the types the dates take, in order |

- Without `descriptions__types` or `dates__types`, the types are taken in order from the record kind's collection, so `descriptions=2` on a project creates an abstract and an introduction. The vocabularies must be loaded, as the test suite does once per session with `sync_vocabularies`.
- A value that is not an `int` raises `TypeError`.
- A type that is not in the record kind's collection raises `ValueError` listing the valid types.
- More descriptions or dates than there are types raises `ValueError`. Pass `descriptions__types` or `dates__types` with at least that many.
- A record holds one description and one date of each type, which is why the types differ.
- The factories do not create identifiers, keywords or credits. Use the metadata factories below, or `ContributionFactory`.

The valid types for each record kind, by identifier, are:

| Record | `descriptions__types` | `dates__types` |
|---|---|---|
| Project | `abstract`, `introduction`, `background`, `objectives`, `expected-output`, `conclusions`, `other` | `start`, `end` |
| Dataset | `abstract`, `methods`, `series-information`, `technical-info`, `other` | `available`, `collection-start`, `collection-end`, `submitted`, `published`, `withdrawn` |
| Sample | `sample-collection`, `sample-preparation`, `sample-storage`, `sample-destruction`, `other` | `created`, `destroyed`, `collected`, `returned`, `prepared`, `archival`, `restored` |
| Measurement | `measurement-conditions`, `measurement-setup`, `measurement-tear-down`, `other` | `setup`, `tear-down` |

A type's address is its vocabulary's address, a slash and the identifier, as in `f"{DESCRIPTION_TYPES}/introduction"` with `DESCRIPTION_TYPES` from `fairdm.core.vocabularies`. `ProjectDescription.get_type_concepts()` and the same method on the other description and date models give the concepts in code. Every factory that makes a row with a `type`, and `SampleFactory` for `status`, takes the concept's address as well as the concept.

## Images

`ProjectFactory`, `DatasetFactory`, `ContributorFactory`, `PersonFactory` and `OrganizationFactory` write no image unless you ask.

| Argument | Effect |
|---|---|
| `with_image=True` | Generates a placeholder image. 800 by 600 pixels for a project or dataset, 400 by 400 for a contributor |
| `image=<file>` | Uses that file |

## Core records

| Factory | Model | Fills in |
|---|---|---|
| `ProjectFactory` | `Project` | `name` (a short sentence), `status` (a random project status), `funding` (one DataCite funding reference), `owner` (a new organization). `visibility` is the model's default, which is private |
| `DatasetFactory` | `Dataset` | `name` (a short sentence), `project` (a new project), `license` (the licence named by `FAIRDM_DEFAULT_LICENSE`, created if it does not exist). `visibility` is private |
| `SampleFactory` | `Sample` | `name`, `local_id` (`SAMPLE-` and four digits), `status` (`unknown`), `dataset` (a new dataset), `location` (`None`) |
| `MeasurementFactory` | `Measurement` | `name`, `dataset` (a new dataset) |

`SampleFactory` and `MeasurementFactory` are abstract. `Sample` and `Measurement` cannot be created directly, so you subclass the factory for each concrete type your portal defines. The framework ships no concrete sample or measurement factory. See [How to add a factory for a portal model](../how-to/add-a-factory-for-a-portal-model.md).

`MeasurementFactory` gives `sample` no default. Pass a concrete sample, or declare a `sample` in your subclass.

`FAIRDM_DEFAULT_LICENSE` is described in [Settings](settings.md).

## Contributors and credits

| Factory | Model | Fills in | Needs from you |
|---|---|---|---|
| `UserFactory` | The portal's user model, `Person` | `email` (`user0@example.com`, then `user1@example.com`), `first_name` (`Test`), `last_name` (`User`), `is_active` (`True`), `is_staff` and `is_superuser` (`False`), password `password123` | Nothing. Pass `password="..."` to set another |
| `ContributorFactory` | `Contributor` | `name` (`Contributor 0`, `Contributor 1`, and so on), `profile` (a paragraph of text) | Nothing |
| `PersonFactory` | `Person` | `email` (`person0@fakeuser.org`, and so on), `first_name`, `last_name` (random names), `is_active` (`True`), an unusable password | Nothing. Pass `password="..."` for a person who can sign in |
| `OrganizationFactory` | `Organization` | The fields of `ContributorFactory` | Nothing |
| `ContributorIdentifierFactory` | `ContributorIdentifier` | `type` (`ORCID`), `value` (a unique sequence) | `related`, the contributor that holds it |
| `AffiliationFactory` | `Affiliation` | `person` (a new person), `organization` (a new organization), `type` (the plain member level), `start_date` (`2020`), no end date | Nothing |
| `ContributionFactory` | `Contribution` | `contributor` (a new person), the credited object (a new project) | Nothing. Pass `content_object=<record>` to credit another record, and `level=` to give the person a level on it |

- `Person` has no username. A person signs in by email.
- `PersonFactory` builds a new person on each call because the email is a sequence. Passing an `email` that already exists returns that person instead of creating a second one.
- The unusable password of a `PersonFactory` person suits a contributor added for attribution. Use `force_login` or `force_authenticate` in a test, or pass a password.
- `ContributorIdentifierFactory` generates a unique `value` because an identifier's value is unique across every record that carries one, not only across contributors.
- `ContributionFactory` sets no `level`. Pass one when a test depends on what the person may do. The levels are `ContributionLevel.VIEW`, `EDIT` and `MANAGE`, from `fairdm.contrib.contributors.choices`.

## Metadata and relations

These factories each create one row of a record's metadata. None picks the record for you, so pass `related`, or the fields named below.

| Factory | Model | Default `type` | Other defaults | Needs from you |
|---|---|---|---|---|
| `ProjectDescriptionFactory` | `ProjectDescription` | `Abstract` | `value` (text) | `related` |
| `ProjectDateFactory` | `ProjectDate` | `Start` | `value` (a year, a month or a day) | `related` |
| `ProjectIdentifierFactory` | `ProjectIdentifier` | `DOI` | `value` (a random DOI) | `related` |
| `DatasetDescriptionFactory` | `DatasetDescription` | `Abstract` | `value` (text) | `related` |
| `DatasetDateFactory` | `DatasetDate` | `Available` | `value` (a year, a month or a day) | `related` |
| `DatasetIdentifierFactory` | `DatasetIdentifier` | `DOI` | `value` (a unique sequence) | `related` |
| `SampleDescriptionFactory` | `SampleDescription` | `SampleCollection` | `value` (text) | `related` |
| `SampleDateFactory` | `SampleDate` | `Created` | `value` (a year, a month or a day) | `related` |
| `SampleIdentifierFactory` | `SampleIdentifier` | `DOI` | `value` (a unique sequence) | `related` |
| `SampleRelationFactory` | `SampleRelation` | `child_of` | | `source` and `target`, both concrete samples |
| `MeasurementDescriptionFactory` | `MeasurementDescription` | `MeasurementConditions` | `value` (text) | `related` |
| `MeasurementDateFactory` | `MeasurementDate` | `Setup` | `value` (a year, a month or a day) | `related` |
| `MeasurementIdentifierFactory` | `MeasurementIdentifier` | `DOI` | `value` (a unique sequence) | `related` |
| `LiteratureItemFactory` | `literature.Item` | `article-journal` | `citation_key` (a unique sequence), `title`. Also takes `doi`, `year` (the issued year) and `authors` (`(family, given)` pairs), and no other field | Nothing |
| `DatasetLiteratureRelationFactory` | `DatasetLiteratureRelation` | | `dataset` (a new dataset), `literature_item` (a new item), `relationship_type` (`IsCitedBy`) | Nothing |

## Faker provider

Importing `fairdm.factories` registers `FairDMProvider` with factory_boy's `Faker`, so a factory can ask for these generators by name.

| Generator | Returns |
|---|---|
| `geo_point` | A random point as a WKT string, `POINT(<latitude> <longitude>)`. Keyword arguments go to Faker's `latlng` |
| `html_paragraphs` | Paragraphs wrapped in `<p>` tags. `nb` is the number, or a function returning it |
| `multiline_text` | Paragraphs of plain text separated by blank lines. `nb` works as above |
| `partial_date` | A date written as a year, a year and month, or a full date, chosen at random |
| `random_instance` | A random existing record. Pass `model=` or `queryset=`, and it returns `None` if there are none |

```python
import factory

date_collected = factory.Faker("partial_date")
```

`fairdm.factories.utils.randint(min_value, max_value)` returns a function that gives a random integer in the range, for use with `factory.LazyFunction`.
