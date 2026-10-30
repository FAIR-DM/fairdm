# Contributors

The Contributors tab lists the people and organizations credited on a record, and it is where the people who manage the record change who is credited and what each person may do. Projects, datasets, samples and measurements all have it, and the screens are the same on all four. Only the roles on offer and the access card differ.

## How to reach it

Open the record's page and choose its **Contributors** tab, or choose **See all** on the record's **People** card. The address is the record's own address followed by `contributors/`:

| Record | Address |
|---|---|
| Project | `/projects/<portal ID>/contributors/` |
| Dataset | `/datasets/<portal ID>/contributors/` |
| Sample | `/samples/<portal ID>/contributors/` |
| Measurement | `/measurement/<portal ID>/contributors/` |

The tab opens for exactly the people who may open the record's own page, and answers everyone else as if the record did not exist. Only people who manage the record are offered the controls for changing it. Everyone else who may open the record sees the two lists and nothing more. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

## The header and the search box

The heading is **Contributors**, with the record's name beneath it. When anyone is credited, a search box headed "Search by name" and a **Search** button sit beside the heading. They narrow both lists to the names that contain what you typed. The page then reads "Showing the people and organizations whose name contains" followed by your text, with a **Show everyone** link that clears the search.

## People

A section headed **People**, with a count, lists the people credited, in the order the record names them. Each row has:

- The row's place in the list.
- The person's avatar and name, linked to their page.
- The organization they are credited from on this record, if any.
- Their roles on this record, as badges.

People who manage the record also see, on each row:

- What the person may do, as a badge: **Can view**, **Can edit** or **Can manage**. A level held from a record above adds "from the" and the record's kind. A person with no level reads "No access". A person with no account yet adds "Takes effect when they have an account."
- Arrow buttons that move the person earlier or later, left out while a search is narrowing the list or when there is nobody to move past.
- **Edit** and **Remove**.

People who manage the record also see an **Add person** button, and below the list a note: "This order is the order the" followed by the record's kind, "names its people in, its citation included. Only people who can manage this" and the kind "see what each person may do."

### When no one is credited

The section reads "No people are credited yet." A manager also reads that the order they put people in is the order the record names them in, its citation included. While you are searching and no one matches, it reads "No person on this" followed by the record's kind and "matches" and your text.

## Organizations

A section headed **Organizations**, with a count, shows each organization as a small card with its logo and its name, linked to the organization's page. Roles are not shown on the card.

People who manage the record also see an **Add organization** button, and on each card a settings menu with:

- **Move earlier** and **Move later**.
- **Edit roles**.
- **Remove**. When people on the record are credited from the organization, this is replaced by "Cannot be removed while" followed by a count and "people here are credited from it", with a **See who** link.

Below the cards they read "Organizations are credited and hold no access. Their members gain none from it."

### When no organization is credited

The section reads "No organizations are credited yet." A manager also reads "A person's affiliation is listed here when they are added. An organization can also be credited on its own."

## Access from the record above

On a dataset, a sample and a measurement, people who manage the record also see a card headed "Access from the" followed by the kind of the record above, such as **project** or **dataset**. A project is at the top, so it has no such card.

The card lists the people who can open this record only because of what they hold on the record above it, each with a badge for their level and a link "from the" and the record's kind. They are not listed on this record, and their access can only be changed on the record above, which the **Manage there** button opens. When there are none, the card reads "Nobody else holds access to this" and the record's kind "through its" and the kind above.

## The levels

A person holds one level on a record. Each level includes the ones before it.

| Level | What the person may do |
|---|---|
| Can view | Open the record, even while it is private |
| Can edit | Also change the record and the data in it |
| Can manage | Also change its contributors and their levels, change its visibility, publish it and delete it |

An organization holds no level. A role says how a person took part and never changes a level. The reasoning, and how a level reaches the records beneath, is in [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

## The roles each kind offers

The roles on the Edit a contributor screen depend on the record's kind.

| Record | Roles |
|---|---|
| Project | Creator, Project Leader, Project Member, Project Manager, Contact Person, Other |
| Dataset | Creator, Contact Person, Data Collector, Data Curator, Data Manager, Editor, Producer, Related Person, Researcher, Project Leader, Project Manager, Project Member, Supervisor, Work Package Leader, Rights Holder, Other |
| Sample | Collector, Preparer, Archivist, Destroyer, Restorer |
| Measurement | Preparation, Collection, Support |

The person who creates a project or a dataset is credited on it at the **Can manage** level with the roles Creator, Project Member and Contact Person. A superuser who creates one is not credited, because a superuser cannot be a contributor. See [How contributor accounts and credits work](../../explanation/how-contributor-accounts-and-credits-work.md).

## Add a person

Choose **Add person** to open a screen headed **Add a person**. It opens with "A person is added with the organization they were at for this" and the record's kind. It offers three tabs, and switching between them does not reload the page. Each tab keeps its own search.

### Already in the portal

Headed "Search the people in this portal", with the hint "By name, or part of it." and a **Search** button. Each match has a **Choose** button, or reads **Already a contributor** when the person is on the record. When there are more matches than the screen lists, it says "There are more matches than are shown, so add more of the name to narrow the search." Up to 20 matches are listed. With none it reads "Nobody in this portal matches" followed by your text.

Choosing a match shows the person and the affiliation choice, then **Add to this** and the record's kind, with **Choose someone else** beside it.

### Find by ORCID

Headed "Search ORCID", with the hint "By name, or by ORCID iD such as 0000-0002-1825-0097." Each match shows the person's name, the institution ORCID lists and their ORCID iD, with a **Choose** button. Up to 10 matches are listed, and people with no public name are not. While the search runs the screen reads "Searching ORCID…". With none it reads "ORCID has nobody matching" followed by your text. When ORCID cannot be reached it reads "Searching ORCID is unavailable right now, but the other two tabs still work."

Choosing a match shows it with the line "A profile is made for them from their ORCID record. They can claim it later by signing in with ORCID." The first current employer ORCID lists is offered as the organization. A profile that already holds that ORCID iD is used and no second one is made.

### New person

For someone who is not in the portal and has no ORCID iD. The tab reads "For someone who is not in the portal and has no ORCID iD. They get a profile with no account, and can be invited to claim it later." Its fields are **Given name** and **Family name**, then the affiliation choice. The button reads **Add to this** and the record's kind.

When a profile with the same name exists, the tab warns "Someone with this name is already in the portal.", lists those profiles with a **Choose** button each, and the button changes to **Make a new profile anyway and add**. A refused submission lists the problems under "Nothing was added."

### The affiliation choice

Every way of adding a person ends with a fieldset headed "Their affiliation for this" and the record's kind. It offers the person's own affiliations, the primary one first and selected, each marked "Their primary affiliation today", "Also current" or "Earlier, until" and a date. Beneath them are **Another organization**, with a text box that suggests organizations in the portal, and **No affiliation**. A name the portal does not have yet makes a new organization. The choice is kept with this record only.

### Footer

The screen ends with "A person you add can open this" and the record's kind "straight away, and nothing more until you say so. They join the end of the people." and a **Back to contributors** button.

## Add an organization

Choose **Add organization** to open a screen headed **Add an organization**. It opens with "Use this for an organization credited on this" and the record's kind "in its own right, such as a funder or a host institution." It offers three tabs.

- **Already in the portal**, headed "Search the organizations in this portal". Each match has an **Add** button, or reads **Already listed**.
- **Find in ROR**, headed "Search the ROR registry", with the hint "By name, or by ROR ID such as https://ror.org/04z8jg394." Each match shows the name, its kind and place, and its ROR ID, with a **Choose** button. Choosing one shows "A profile is made for it from its ROR record and it is added to this" and the record's kind, with **Add to this** and the kind, and **Choose another**. Organizations that are not active in ROR are not listed. When ROR cannot be reached the tab reads "Searching ROR is unavailable right now, but the other two tabs still work."
- **New organization**, for "an organization that is not in the portal and not in ROR". Its fields are **Name**, **City (optional)**, **Country (optional)** and **Website (optional)**. A country is given by name or by its two-letter code. A name that an organization in the portal already has is never made twice. The tab offers the existing organization with an **Add** button instead.

The screen ends with "An organization is credited and holds no access. It joins the end of the organizations."

After you add anyone, you arrive on the Edit a contributor screen with a message such as "Name was added. Say what they did, and what they may do here." For an organization the message reads "Say what they did here." If the person is a superuser, nobody is added and the message reads that a superuser cannot be a contributor.

## Edit a contributor

**Edit** beside a person, or **Edit roles** on an organization's menu, opens a screen headed **Edit a contributor**. It shows the contributor, then:

- A group headed "What they did on" the record's kind, with a checkbox for each role in the table above. The hint reads "Choose every role that applies, or none. Roles are credit: they do not change what anyone may do."
- For a person, the affiliation choice described above, with their current choice selected.
- For a person, a group headed "What they may do on" the record's kind, with three radio buttons, **Can view**, **Can edit** and **Can manage**, each with a hint. A level the person already holds from a record above is the lowest on offer, and the choices below it are switched off. A person with no account reads "This person has no account yet. What you choose takes effect when they have one."
- For an organization, the line "Nothing. An organization is credited and holds no access, and its members gain none from it. Add a person to give them access."

The buttons are **Save**, **Cancel**, and **Remove from this record**. Everything is saved together or not at all. A refusal lists its reasons under "Nothing was saved." Three refusals are possible:

- A role the kind does not offer: "Choose from the roles offered for this kind of record."
- A level below what the person holds from a record above: "They hold “Can edit” from the dataset above, and it cannot be lowered here." The level and record in the message vary.
- A change that would leave the record with nobody to manage it: "Name is the only person who can manage this dataset. Give someone else “Can manage” first."

Saving returns you to the Contributors tab with "Name was saved."

## Remove a contributor

**Remove** opens a screen headed **Remove a contributor**. It shows the contributor and one of three states:

- The question "Remove" followed by the name and "from this" and the kind, with a list of what happens: the contributor is no longer credited or named in the citation, a person loses the access they held through being listed here and keeps what they hold from a record above, and an organization they are credited from stays under Organizations. Choose **Remove** to go ahead, or **Cancel**.
- For an organization that people are credited from, the name and "cannot be removed yet." with the explanation that it is listed as the affiliation of the people below, and the list of those people. There is no way to go ahead.
- For the only person who can manage the record, the name and "cannot be removed yet." with "They are the only person who can manage this" and the kind, then "Give someone else “Can manage” first, so it is never left with nobody to look after it." There is no way to go ahead.

Both refused states offer **Back to contributors**. After a removal you arrive on the Contributors tab with "Name was removed from this" and the kind.

## What you can do here

- Give someone access to a private record. See [How to let a colleague into a private record](let-a-colleague-into-a-private-record.md).
- Add a person or an organization. See [How to add a person or organization](add-a-person-or-organization.md).
- Set what someone did on the record. See [How to set a contributor's roles](set-a-contributors-roles.md).
- Change the order contributors are named in. See [How to put contributors in order](put-contributors-in-order.md).
- Take someone off the record. See [How to remove a contributor](remove-a-contributor.md).
- Change the organization a person is credited from. See [How to change the organization a person is credited from](change-the-organization-a-person-is-credited-from.md).
