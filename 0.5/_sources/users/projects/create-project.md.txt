# Create a project

The Create a project screen starts a new project with the three facts every project needs: its name, its status and who may see it. Everything else is filled in afterwards on the project's own screens. You reach it from the **Create new** menu in the header, where you choose **Project**, or from the **Add** button on [Projects](projects.md). The screen is at `/projects/create/`. A visitor who is not signed in is sent to sign in first.

## The form

The form has three fields, and all three are required.

- **Project name.** The help text reads "A clear, descriptive name for your project." The name can be up to 255 characters.
- **Status.** The stage the project is at, with the help text "Current phase of the project lifecycle." The choices are Concept, Planning, In progress, Complete and Searching for collaborators. The list opens on Concept.
- **Visibility.** Two options, **Private** and **Public**, with the help text "Who can view this project?" Public is selected when the form opens.

The form preselects Public, but the project itself defaults to Private, so a project that is created without this form starts private. The form and the project decide their defaults separately. See [ADR 0009](../../adr/0009-a-form-default-and-a-model-default-may-differ.md).

## The buttons

The form ends with two buttons, **Save & continue** and **Save & continue editing**. Both create the project and open its page, where a message says "Project successfully created." If a field is wrong, the form stays open with the error beside the field and nothing is created.

## What is recorded for you

The project lists you as a contributor with the **Can manage** level and the roles Creator, Project Member and Contact Person. The exception is a superuser, who cannot be credited on a record. See [Contributors](../contributors/contributors-tab.md) for what the level allows.

The project has no owner organization yet. That, the cover image and the other details are set afterwards.

## What is not on this screen

The form leaves out the cover image and the owner organization, which are on [Edit details](edit-details.md). The project's descriptions, keywords, dates and identifiers have screens of their own, all in the **Manage** menu of [the project page](project.md).

## What you can do here

- Create the project: [How to create a project](create-a-project.md).
- Fill in the rest: [Edit details](edit-details.md), [Descriptions](../editing-a-record/descriptions.md), [Key dates](../editing-a-record/key-dates.md).
