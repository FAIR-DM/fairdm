# Edit profile

The Edit profile screen is where you change what your public profile says about you: your name, photo, biography, links and languages.

You reach it in any of these ways:

- Select **Edit profile** in the header of [your profile](your-profile.md).
- Select **Fix** beside the photo, biography or links item of the **Your profile** checklist on your profile. You arrive at the field the item asks for.
- Select **Write your biography** in the **About** card of your profile, when you have not written one.

The address is your profile's address followed by `update/`. You must be signed in. Only you can open it for your own profile. A Community Manager can also open it for a profile nobody can sign in to, such as one nobody has claimed or one that is deactivated. Anyone else is refused, and a visitor who has not signed in is sent to the [Sign in](sign-in.md) screen.

The screen is headed **Edit profile**.

## The notice

On your own profile, a notice above the form reads **Your email address, password and connected sign-ins are managed in your account centre.** The words *account centre* link to the [Account Center](account-centre.md). The notice is not shown to a Community Manager editing someone else's profile.

## The form

The first group of fields has no heading:

| Field | What it holds |
|---|---|
| **Given name** and **Family name** | The two parts of your name, side by side. The help text says they are used with each other in citations. |
| **Display name** | The name you are publicly known by, as it appears on your credits. It is required. |
| **Alternative names** | Other names you publish under, one per line. |

A second group is headed **About you**:

| Field | What it holds |
|---|---|
| **Photo** | A JPEG, PNG or WebP image. The help text names the size limit. Ticking the clear box removes the photo, and your initials show instead. |
| **Biography** | A few lines about your research. Markdown is supported. |
| **Languages** | The languages you work in. Choose as many as you need. |
| **Links** | Web addresses of your other profiles, one per line. Each must begin with `http://` or `https://`. |

Blank lines are dropped, and an entry typed twice is kept once. A line that is not a web address is refused with the line quoted: `“…” is not a web address. Start it with http:// or https://.`

The form changes nothing else about you. Your email address, password and connected sign-ins are in the [Account Center](account-centre.md). Your ORCID iD is added by signing in with ORCID. Your affiliations and portal roles are set by the people who run the portal.

A portal can add fields to the form or take some away. See [How to customise the profile form](../../developers/how-to/customise-the-profile-form.md).

## The buttons

- **Save** saves the changes and returns you to the profile, with the message **Your changes were saved.**
- **Cancel** returns you to the profile and changes nothing.

When a field cannot be saved, nothing is saved. The field says what is wrong, and everything else you typed stays in the form.

## What you can do here

- Change your profile. See [How to edit your profile](edit-your-profile.md).
- See how the profile reads to others. See [Your profile](your-profile.md).
