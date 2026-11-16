# Edit organization

The Edit organization screen is where the people who keep an organization's record change what its public page says: its name, logo, type, place, description and web addresses.

You reach it in any of these ways:

- Open the **Manage** menu in the header of the [organization's page](organization.md) and choose **Edit details**.
- Select the **Edit details** button in the header, if you are a Community Manager who does not keep the organization.
- Select **Fix** beside the logo, type, city and country, description or website item of the **Organization record** checklist. You arrive at the field the item asks for.
- Select **Write a description** in the **About** card, when the organization has none.

The address is the organization's address followed by `update/`. You must be signed in, with an active account. The organization's owner and its administrators can open the screen while their affiliation has not ended. A Community Manager can open it for any organization. An ordinary member, a person with no affiliation and a person who holds only the Data Curator role are refused, and a visitor who has not signed in is sent to the [Sign in](sign-in.md) screen.

The screen is headed **Edit organization**.

## The form

The first group of fields has no heading:

| Field | What it holds |
|---|---|
| **Logo** | A JPEG, PNG or WebP image. The help text names the size limit. Ticking the clear box removes the logo, and the organization's initials show instead. |
| **Name** | The name the organization is publicly known by. It is required, and it appears wherever the organization is credited. |
| **Alternative names** | Other names the organization is known by, one per line. |
| **Type** | The kind of institution: **Education**, **Funder**, **Healthcare**, **Company**, **Archive**, **Nonprofit**, **Government**, **Facility** or **Other**. |
| **Part of** | The organization this one belongs to. Search for it by name, or clear the box to make this organization part of nothing. |

**Type** and **Part of** sit side by side. A group headed **Location** follows:

| Field | What it holds |
|---|---|
| **City** and **Country** | Where the organization is based, side by side. |
| **Coordinates** | A latitude and a longitude. Organizations added from ROR get the coordinates ROR publishes. |

A group headed **About** has one field:

| Field | What it holds |
|---|---|
| **Description** | A few lines about what the organization does. Markdown is supported. |

A group headed **Online** has two:

| Field | What it holds |
|---|---|
| **Website** | The organization's own web address. |
| **Other links** | Web addresses of other pages about the organization, one per line. |

Every web address must begin with `http://` or `https://`. Blank lines are dropped, and an entry typed twice is kept once. The website and the other links are stored as one list with the website first. When you clear the website and save, the first of the other links becomes the website the next time you open the screen.

An organization cannot be part of itself or of any organization beneath it, at any depth. If you choose one, nothing is saved and **Part of** says why.

The form does not change the organization's ROR identifier, its members or its owner.

A portal can add fields to the form or take some away. See [How to customise the profile form](../../developers/how-to/customise-the-profile-form.md).

## The buttons

- **Save** saves the changes and returns you to the organization's page, with the message **Your changes were saved.**
- **Cancel** returns you to the organization's page and changes nothing.

When a field cannot be saved, nothing is saved. The field says what is wrong, and everything else you typed stays in the form.

## What you can do here

- Change the organization's details. See [How to edit an organization's profile](edit-an-organizations-profile.md).
- See how the page reads to others. See [Organization](organization.md).
