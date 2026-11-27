# Contributors

The Contributors tab lists the people and organizations credited on a record. It is also where the people who manage the record add people, change what each person did and may do, put people in order and remove them. Projects, datasets, samples and measurements all have it, and it works the same way on all four. Only the roles on offer differ.

## How to reach it

Open the record's page and choose its **Contributors** tab, or choose **See all** on the record's **People** card. The address is the record's own address followed by `contributors/`:

| Record | Address |
|---|---|
| Project | `/projects/<portal ID>/contributors/` |
| Dataset | `/datasets/<portal ID>/contributors/` |
| Sample | `/samples/<portal ID>/contributors/` |
| Measurement | `/measurements/<portal ID>/contributors/` |

The tab opens for exactly the people who may open the record's own page, and answers everyone else as if the record did not exist. Only people who manage the record are offered the controls for changing it. Everyone else who may open the record sees the two lists and nothing more. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

## People

A section headed **People**, with a count, lists the people credited in the order the record names them in. Each row shows the person's avatar and name, the organization they are credited from on this record and their roles. A person with no organization shows a dash.

People who manage the record also see an **Add** button beside the heading. Each row has a menu with **Edit**, **Reorder** and **Remove**. **Reorder** is offered when there is more than one person.

## Organizations

A section headed **Organizations**, with a count, lists every organization credited on the record, in the order the people they are credited from lead the record, then the organizations credited on their own. Each row shows the organization's name and its roles. An organization that only appears because someone is credited from it shows the role Project Member where the kind of record offers it.

People who manage the record see an **Add** button beside the heading. Each row has **Edit roles**, and **Remove** when nobody on the record is credited from that organization.

## Access from other records

On a dataset, a sample and a measurement, people who manage the record also see a section headed **Access from other records**. It lists the people who can open this record only because of what they hold on a record above it, with their level and the record it comes from. They are not credited here, and their access is changed on the record above.

## The levels

A person holds one level on a record. Each level includes the ones before it.

| Level | What the person may do |
|---|---|
| Can view | Open the record, even while it is private |
| Can edit | Also change the record and the data in it |
| Can manage | Also change its contributors and their levels, change its visibility, publish it and delete it |

A person added from the tab starts at **Can view**. An organization holds no level. A role says how a person took part and never changes a level. The reasoning, and how a level reaches the records beneath, is in [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

## The roles each kind offers

The roles depend on the record's kind. What each one means is in [Contributor roles](../../reference/contributor-roles.md).

| Record | Roles |
|---|---|
| Project | Creator, Project Leader, Project Member, Project Manager, Contact Person, Other |
| Dataset | Creator, Contact Person, Data Collector, Data Curator, Data Manager, Editor, Producer, Related Person, Researcher, Project Leader, Project Manager, Project Member, Supervisor, Work Package Leader, Rights Holder, Other |
| Sample | Collector, Preparer, Archivist, Destroyer, Restorer |
| Measurement | Preparation, Collection, Support |

Everyone added to a project or a dataset, person or organization, holds Project Member. The role is ticked and cannot be unticked, and someone who holds it keeps it when their roles are edited.

The person who creates a project or a dataset is credited on it at the **Can manage** level with the roles Creator, Project Member and Contact Person. A superuser who creates one is not credited, because a superuser cannot be a contributor. See [How contributor accounts and credits work](../../explanation/how-contributor-accounts-and-credits-work.md).

## Add a person

**Add** beside **People** opens a sheet. Its steps are:

1. **Search.** Type a name or an ORCID iD. The people in the portal who are not on the record yet narrow as you type. A name nobody in the portal has, and an ORCID iD nobody holds, appear as a **New** row at the bottom.
2. **Who they are.** A new name asks ORCID who it knows under that name. Pick the person you mean, or add them by name alone. A name added alone is split into given names and a family name for you to confirm.
3. **Their affiliation.** The organizations on their ORCID record come first, then those on their portal profile, then the rest of the portal. Search by name to find another, and use a **New** row for one the portal lacks. An organization picked from ORCID is matched in the portal by its ROR ID, which the portal also finds from a Funder Registry, Ringgold or GRID ID that the ORCID record gives. The portal makes one only when nothing matches.
4. **Their roles.** Tick the roles that apply, then **Add**.

**Back** returns to the step before. Tapping outside the sheet, dragging it down or its close button closes it without adding anyone.

ORCID and ROR searches are limited per person to a number a minute, and a registry that cannot be reached is said so in the step. The portal never adds someone from a registry it could not ask.

## Add an organization

**Add** beside **Organizations** opens a sheet with a search of the portal's organizations. A name the portal does not have becomes a **New** row, which asks ROR who it knows under that name. Pick the organization you mean or add it by name alone, then tick its roles and choose **Add**.

## Edit a contributor

**Edit** on a person opens their sheet:

- **Their affiliation on this record.** One of the person's own affiliations, any other organization in the portal, or none. The choice is kept with this record only.
- **Roles.** Tick every role that applies.
- **Their access.** The three levels, each with a hint. A level the person holds from a record above is the lowest on offer, and the levels below it are switched off.

**Edit roles** on an organization opens its roles. Everything on a sheet is saved together or not at all. A refusal is shown on the tab, and nothing is saved.

## Remove a contributor

**Remove** takes the person off the record at once and offers **Undo** for a few seconds. **Undo** puts them back with the same roles, level, organization and place in the order. A record always keeps a manager, so the only person who can manage it cannot be removed.

## Reorder

**Reorder** opens the people in a list you can drag by its handle. With the keyboard, focus the handle and use the arrow keys. **Save order** keeps it. The order is the order the record names its people in, its citation included. The eye beside each name decides whether that person is named in the citation: closed, they are credited and listed but left out of formal citations. See [How to put contributors in order](put-contributors-in-order.md).

## What you can do here

- Give someone access to a private record. See [How to let a colleague into a private record](let-a-colleague-into-a-private-record.md).
- Add a person or an organization. See [How to add a person or organization](add-a-person-or-organization.md).
- Set what someone did on the record. See [How to set a contributor's roles](set-a-contributors-roles.md).
- Change the order contributors are named in. See [How to put contributors in order](put-contributors-in-order.md).
- Take someone off the record. See [How to remove a contributor](remove-a-contributor.md).
- Change the organization a person is credited from. See [How to change the organization a person is credited from](change-the-organization-a-person-is-credited-from.md).
