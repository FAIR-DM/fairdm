# Adjusting Dataset Access

This guide provides a step-by-step walkthrough for controlling who can view and edit specific datasets in your FairDM portal. You'll learn how to restrict access to sensitive data, grant access to collaborators, and enable public read access for FAIR-compliant publication.

## Prerequisites

- Administrative access to the FairDM portal
- A dataset that you want to manage access for
- Basic familiarity with the Django admin interface

## Scenario 1: Restricting a Dataset to Specific Users

Let's say you have a dataset called "Geological Survey 2024" that should only be accessible to members of a specific research team.

### Step 1: Log in to the Admin Interface

Navigate to your portal's admin interface (typically `/admin/`) and log in with your administrator credentials.

### Step 2: Find the Dataset

1. In the admin sidebar, locate the **Datasets** section
2. Click on **Datasets** to view the list
3. Find "Geological Survey 2024" and click on it to open the dataset details

### Step 3: Review Current Permissions

Scroll down to the **Object permissions** section. You may see:

- **All users**: Has "Can view dataset" permission (default public read access)
- Or individual users/groups with specific permissions

### Step 4: Remove Broad Access

If "All users" or a broad group has access and you want to restrict it:

1. Click the **red X** next to any permissions you want to remove
2. Click **Save** at the bottom of the page

### Step 5: Grant Access to Authorized Users

1. In the **Object permissions** section, click **Add user permissions**
2. Search for and select the user (e.g., "alice_researcher")
3. Check the permissions you want to grant:
   - ☑️ **Can view dataset** (allows viewing the dataset and its metadata)
   - ☑️ **Can change dataset** (allows editing the dataset)
   - ☐ **Can delete dataset** (use carefully—allows permanent removal)
4. Click **Save**

Repeat for each team member who needs access.

```{tip}
**Using groups for team access**: Instead of adding permissions for individual users, create a Django group called "Geological Survey Team", assign users to that group, and grant permissions to the group. This makes managing access much easier as team membership changes.
```

### Step 6: Verify Access

Log in as one of the authorized users (or ask them to test) and confirm they can:

- Navigate to the dataset from the portal's dataset list
- View the dataset details
- Edit the dataset if "Can change dataset" was granted

## Scenario 2: Enabling Public Read Access for a Published Dataset

For FAIR compliance, you may want to make a finalized dataset publicly readable while keeping editing restricted to the research team.

### Step 1: Grant View Permission to All Users

1. Open the dataset in the admin interface
2. Scroll to **Object permissions**
3. Click **Add user permissions**
4. In the user search field, select **AnonymousUser** (this represents unauthenticated visitors)
5. Check ☑️ **Can view dataset** only (do not grant change or delete permissions)
6. Click **Save**

Now anyone visiting your portal can view the dataset, even without logging in.

### Step 2: Restrict Editing to Authorized Users

Ensure that only your research team has "Can change dataset" or "Can delete dataset" permissions:

1. Review the permissions list in the **Object permissions** section
2. Confirm that only trusted users or groups have edit/delete access
3. Remove any unnecessary permissions

### Step 3: Verify Public Access

1. Open an incognito/private browser window (to simulate an unauthenticated user)
2. Navigate to your portal and find the dataset
3. Confirm you can view the dataset details without logging in
4. Verify that editing options (e.g., "Edit" button) are not visible

## Scenario 3: Temporarily Revoking Access

If a collaborator leaves the project or you need to temporarily restrict access during data quality review:

### Step 1: Identify the User's Permissions

1. Open the dataset in the admin interface
2. Scroll to **Object permissions**
3. Locate the user whose access you want to revoke

### Step 2: Remove Permissions

1. Click the **red X** next to the user's permissions
2. Click **Save**

The user will immediately lose access to the dataset.

### Step 3: Re-Grant Access if Needed

When you're ready to restore access:

1. Follow the steps from **Scenario 1, Step 5** to add the user back
2. Grant the appropriate permissions
3. Click **Save**

## Best Practices

- **Document access policies**: Keep internal notes about who should have access to each dataset and why, especially for long-running projects.
- **Use groups for scalability**: Manage permissions at the group level rather than assigning permissions to individuals one by one.
- **Audit permissions regularly**: Periodically review dataset access, especially after team changes or project milestones.
- **Communicate with users**: Let collaborators know when you've granted or revoked access to avoid confusion.
- **Test access changes**: After adjusting permissions, verify by logging in as a test user or asking a collaborator to confirm access.

## Troubleshooting

**I removed permissions, but the user can still access the dataset:**

- The user may be in a group with broader permissions (e.g., "Database Admin"). Check group memberships in the user's profile in the admin interface.
- Clear the browser cache or use an incognito window to test access.

**Anonymous users can edit the dataset even though I only granted view permission:**

- Verify that only "Can view dataset" is checked for AnonymousUser and that no other permissions are granted.
- Check your portal's global permission settings in the Django admin.

**The Object permissions section is missing:**

- Ensure django-guardian is installed and configured in your FairDM portal. Contact your system administrator if needed.

```{seealso}
For more details on user roles and group management, see [Managing Users and Permissions](managing_users_and_permissions.md).
```
