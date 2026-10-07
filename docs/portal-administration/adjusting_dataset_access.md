# Adjusting Dataset Access

This guide walks through controlling who can view and edit specific datasets in your FairDM portal. You'll learn how to restrict access to sensitive data, let collaborators in, and make a dataset public for FAIR-compliant publication.

Access to a dataset has two parts. Its **visibility** says whether anyone may open it, and the **level** each listed contributor holds says what they may do. Both are set in the portal itself, by someone who manages the dataset. Nothing here is done in the administration interface: a permission stored there for a dataset grants nothing. See [Managing Users and Permissions](managing_users_and_permissions.md) for the levels and for how portal roles fit in.

## Prerequisites

- The manage level on the dataset, or a portal role that holds the right to change datasets, such as Data Curator
- A dataset that you want to manage access for

## Scenario 1: Restricting a dataset to specific people

Let's say you have a dataset called "Geological Survey 2024" that should only be open to members of a specific research team.

### Step 1: Make the dataset private

1. Open the dataset in the portal and choose **Update** from its **Manage** menu
2. Set **Visibility** to private and save

A private dataset now opens only to the people who hold a level on it, on its project or on the dataset itself, and to holders of a portal role whose rights cover it.

### Step 2: Review who is listed

Open the dataset's **Contributors** tab. Each person is shown with what they may do. A section beneath the lists shows anyone who holds access from the project above, with the level and where it comes from. Those people are changed on the project's own tab.

### Step 3: Let the authorized people in

1. Choose **Add person** and find your colleague
2. Choose **Edit** beside them and choose their level: **View** to read, **Edit** to change the dataset and its samples and measurements, **Manage** to also decide who else is let in
3. Save

Repeat for each team member who needs access. A level on the project reaches every dataset in it, so give the team a level on the project when it runs all of them.

### Step 4: Verify access

Ask one of the authorized people, or sign in as one, and confirm they can open the dataset from the portal's dataset list, and edit it if they hold the **Edit** level.

## Scenario 2: Making a dataset public

For FAIR compliance, you may want a finalized dataset to be open to everyone while keeping editing restricted to the research team.

1. Open the dataset's **Manage** menu, choose **Edit details** and set **Visibility** to public
2. Check the **Contributors** tab and confirm only trusted people hold the **Edit** and **Manage** levels

A public dataset opens to everyone, signed in or not. Levels still decide who may change and manage it.

To check the result, open a private browser window, find the dataset, and confirm that its details are visible and that no editing options are offered.

## Scenario 3: Revoking access

If a collaborator leaves the project or you need to restrict access during data quality review:

1. Open the dataset's **Contributors** tab
2. Choose **Remove** beside the person and confirm. To keep them as a contributor but without the ability to change the dataset, choose **Edit** and lower their level instead

They lose what they held through being listed on the dataset straight away. If they hold a level on the project above, they still hold it there, and it is changed on the project's tab.

## Best Practices

- **Document access policies**: Keep internal notes about who should have access to each dataset and why, especially for long-running projects.
- **Use the project for teams**: One entry on a project covers every dataset in it.
- **Audit regularly**: Periodically read the Contributors tab, especially after team changes or project milestones.
- **Communicate with users**: Let collaborators know when you've changed their level to avoid confusion.
- **Test access changes**: After changing a level, verify by signing in as a test user or asking a collaborator to confirm access.

## Troubleshooting

**I removed someone, but they can still open the dataset:**

- They may hold a level on the project above. The Contributors tab lists those people beneath the lists, with where it comes from.
- They may hold a portal role such as Data Curator, which reaches every dataset. Check their groups on their record in the administration interface.
- The dataset may be public, which opens it to everyone.

**A person added to a dataset cannot change it:**

- A person who is added holds the view level. Edit their entry and choose the **Edit** level.

**A person with the Edit level cannot change the visibility or delete the dataset:**

- Those need the manage level, which also lets a person change who is listed.

**A person with the Edit level cannot see the dataset's project:**

- A level on a dataset does not reach the project above it. Give them a level on the project too.

```{seealso}
For more details on user roles and group management, see [Managing Users and Permissions](managing_users_and_permissions.md).
```
