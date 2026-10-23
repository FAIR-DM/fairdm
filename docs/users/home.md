# Home

The home screen is the first page of the portal. What it shows depends on whether you are signed in. A visitor who has not signed in sees a landing page that introduces the portal. A signed-in user sees a dashboard.

You reach it by opening the portal's address, or by selecting **Home** in the navigation menu. After you sign in, the portal sends you here.

## The landing page

The landing page is for visitors who have not signed in. It has no navigation bar, so the first thing on screen is the welcome section. Each section below the welcome section appears only when the portal has something to put in it, except where stated.

### Welcome

The welcome section fills the first screen. It shows:

- a short line above the heading, `Research data portal` unless the portal has changed it
- the heading, `Welcome to` followed by the portal's name unless the portal has changed it
- a sentence under the heading saying what the portal is for
- the **Browse datasets** and **Explore projects** buttons
- a line under the buttons with the **Create account** link and the **Sign in** link. The **Create account** link appears only when the portal's registration setting is on. The link can still lead to a notice that sign up is closed, because an administrator can close sign up in other ways. See [Sign up](account/sign-up.md).

How a portal changes the wording and the picture is set out in [Home page](../developers/reference/home-page.md). The registration setting is described in [Settings](../developers/reference/settings.md).

### Figures

A band of counts, one for each kind of record the portal holds: **Datasets**, **Samples**, **Measurements**, **People** and **Organizations**. A kind with a count of zero is left out. When every count is zero the band does not appear. The dataset, sample and measurement counts cover public records only.

### About

A section headed **Built by researchers, for researchers**, under the label `About` and the portal's name. It shows:

- the portal's description, when it has one
- the portal's keywords, as badges
- a line `Run by` and the name of the organization that runs the portal, linked to its website when it has one
- four short points headed **Findable.**, **Accessible.**, **Interoperable.** and **Reusable.**

### Latest datasets

Under the label `Recently updated`, a section headed **Latest datasets**. It shows up to three public datasets, the most recently changed first, as cards, with a **Browse datasets** button below them. When the portal has no public dataset the section does not appear.

### Samples and measurements

A section headed **Samples and measurements**. It has a **Samples** list and a **Measurements** list. Each row names a kind of sample or measurement the portal holds, gives a short description of it, links to its [Collections](collections.md) listing and shows how many public records of that kind exist. A dash stands in for none. The five kinds with the most records are listed, and a last row reads `and` a number `more kinds` when there are others. When the portal has registered no kind of sample or measurement, the section does not appear.

### Community

A section headed `Developed and maintained by your research community`. It shows:

- a **Meet the people** button, which opens [People](community/people.md)
- an **Organizations** button, which opens [Organizations](community/organizations.md)
- a row of up to eight faces of the people credited on the most records, followed by a count and a link to the full list
- up to six organizations credited on the most records, each linked to its page

When nobody has been credited yet, the section does not appear.

### New projects

Under the label `Recently added`, a section headed **New projects**. It shows up to three public projects, the most recently added first, as cards, with an **Explore projects** button below them. When the portal has no public project the section does not appear.

### API

A section headed **Browse public data via the API**. It shows an example request and an **API docs** button, which opens [API documentation](api/api-docs.md). This section always appears.

### Join

A closing section. When the portal allows people to register, it is headed `Add your data to` and the portal's name, with the **Create account** and **Sign in** buttons. When it does not, it is headed **Sign in to contribute** and has a **Sign in** button, with a line saying that administrators create the accounts. This section always appears.

### Footer

Three groups of links:

- **Explore**: **Projects**, **Datasets**, **People** and **Organizations**
- **Resources**: **API docs**, **User guide** and **Contact**
- **Account**: **Sign in**, and **Create account** when the portal allows people to register

The footer also shows the copyright line with the name of the organization that runs the portal, and a **Powered by FairDM** link.

## The dashboard

The dashboard is for signed-in users. It is headed **My Dashboard**. Under the heading is a greeting made of `Welcome,` and your first name, or your username when you have no first name, followed by an exclamation mark.

The body of the dashboard has no content of its own. It shows one placeholder line.

The bar at the top of the dashboard carries the **Create new** button, which lets you start a project or a dataset from any screen that shows the bar.

## What you can do here

- Sign in or create an account with [Sign in](account/sign-in.md) and [How to create an account](account/create-an-account.md).
- Create a project with [How to create a project](projects/create-a-project.md).
- Create a dataset with [How to create a dataset](datasets/create-a-dataset.md).
- Follow the [tutorial](tutorial.md) from the dashboard to your first dataset.
