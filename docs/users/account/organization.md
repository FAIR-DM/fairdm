# Organization

An organization page is the public page of one institution, funder, facility or company. It is what opens when someone selects an organization's name on a record, in a list or on a person's profile. Everyone sees the same page, apart from the controls and the checklist described below, which are for the people who keep the organization's record.

You reach it by selecting the organization's name on the [Organizations](../community/organizations.md) screen, or wherever it is named on a record or a profile. The address is `contributor/` followed by the organization's portal ID. Anyone can open it, signed in or not. The heading is the organization's name.

A strip of page links near the top has **Overview**, **Projects** and **Datasets**. This page describes **Overview**. **Projects** and **Datasets** list the public projects and datasets the organization owns or is credited on.

## The header

The header shows:

- the organization's logo, or its initials
- a badge for its type, such as **Education**, when it has one
- its name, followed by a ROR icon linking to its ROR record when it has a ROR identifier
- the organization it is part of, its place and the languages it works in, each shown only when set
- a **Share** menu and a **REST API** button, which opens the page as JSON
- the controls for the people who keep the record, described next

The controls depend on who you are:

- The organization's owner and administrators see a **Manage** menu with **Edit details**. The menu also lists **Manage members** and **Update from ROR**, which are disabled.
- A Community Manager who does not keep the organization sees an **Edit details** button instead of the menu.
- Any other signed-in person sees a disabled **Request to join** button, unless they are already a member.
- A visitor who has not signed in sees no control.

## The figures

Three counts: **Projects** and **Datasets**, which link to the two tabs, and **Members**. They cover public records only.

## About

A card headed **About**, with the organization's description. When there is none, it says **No description has been added yet.** The people who keep the record see **Nobody has described this organization yet.** and a **Write a description** button, which opens the description field on the [Edit organization](edit-organization.md) screen.

## Members

A card headed **Members**, with a count. It lists the people with a current affiliation, ten at most. Each row shows the person's photo and name, `Since` and the year they joined, and an **Owner** or **Administrator** badge where it applies. When there are more, the last row reads `+` a number **other members**. When nobody is affiliated, the card says **Nobody has listed this organization as an affiliation yet.**

## Projects and Datasets

Two cards, **Projects** and **Datasets**, each listing up to five public records, with a count beside the title and a **View all** button. A project row shows its status and an **Owner** badge when the organization owns the project. Projects in progress come first, then the most recently changed.

When there are none, the project card says **This organization doesn't own and isn't credited on any public project yet.** and the dataset card says **No public dataset is credited to this organization or belongs to a project it owns yet.**

## Cards without content

A **Map** card is in the main column and **Recent activity** sits in the column on the right. Each holds a placeholder that describes what the card is meant to show, and no data.

## The column on the right

- **Organization record**, a checklist only the people who keep the record see, marked **Only admin can see this**. It counts how many items are in place, such as `4 of 6 in place`. Items still missing come first, each with a **Fix** link where the portal can take you to the field. The items are **A ROR identifier**, **A logo** (recommended), **The type of organization**, **City and country**, **A description** and **A website** (recommended).
- **Identifiers**, a table of the organization's identifiers, such as its ROR identifier, and its **Portal ID** with a copy button.
- **Links**, the organization's web pages, each named by its site. Without any, it says **No links have been added.**
- A map of where the organization is based, when it has coordinates.
- **Organization hierarchy**, which shows the organization it is part of, its siblings and its own sub-organizations. Without any, it says **No parent organization and no institutes, departments or groups are recorded for this organization.**

## What you can do here

- Change the organization's details. See [How to edit an organization's profile](edit-an-organizations-profile.md).
- Credit the organization on a record you manage. See [How to add a person or organization](../contributors/add-a-person-or-organization.md).
- Find other organizations. See [Organizations](../community/organizations.md).
