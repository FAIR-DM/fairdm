# Roles and Permissions

A set of defined roles within the community is essential to maintaing the integrity and
upkeep of the database. Django itself has a [permissions system](https://docs.djangoproject.com/en/4.1/topics/auth/default/#permissions-and-authorization) built in whereby permission to modify the database can be granted to specific individuals or groups of trusted users.

Normally, the developer must define particular roles suitable for a given application; however, as FairDM powered applications share a common motive (administering a research database), we provide some pre-packaged roles that will help you get started.

## Groups

The built-in roles are defined as Groups within the admin section of your site. Groups are modifiable by database Custodian(s) who can add or remove users from groups as they wish. The available Groups by default are:

Portal Admin
: Controls configuration and overall administration of the site. This includes the ability to add or remove users from groups, and to modify the permissions of groups. 

Database Admin
: Users that are part of this group have permission to view, edit, create or delete any objects associated with the database (by database here we mean the part that was designed to fulfil the needs of the research community).

Site Content
: Has permission to modify  content on the site

Literature Manager
: Has permission to add, edit, or delete literature entries

Reviewer
: Has permission to review pre-existing datasets for quality control

    