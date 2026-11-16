# API tokens

The API tokens screen lists the tokens you have made. A token lets a script or another tool use the portal's API as you, without your password. See [REST API](../../developers/reference/rest-api.md) for what a token can reach.

You reach it by selecting **Manage API tokens** on the [Account Center](account-centre.md), or by choosing **API tokens** in the **Account** group of the sidebar. The address is `account/tokens/`. You must be signed in, and the portal must let you hold tokens. When it does not, the screen answers with a refusal, and the **API tokens** card and sidebar entry do not appear. Opening the address while signed out sends you to the [Sign in](sign-in.md) screen.

The screen is headed **API tokens**, with the line **A token lets a script or another tool use the API as you, without your password.** under it. The breadcrumb leads back to the Account Center.

## The Create token button

Beside the heading is a **Create token** button. It opens the create screen, described below. The button is left out when you already hold as many tokens as the portal allows. A notice then reads, with the portal's limit in place of `10`, **You hold 10 tokens, the most this site allows. Revoke one before you create another.** The limit is a portal setting. See [Settings](../../developers/reference/settings.md).

## The new token

Right after you create a token, a card headed **Your new token** appears above the list. It holds:

- a warning, **Copy this token now and keep it somewhere safe. It will not be shown again.**
- the whole token in a read-only box labelled **Token**, with a **Copy** button
- a line showing how to send it, in the `Authorization` header
- an **I have copied it** button

The card appears once. Reloading the screen or coming back later shows the list without it, and the whole token can never be shown again.

## Your tokens

A card headed **Your tokens**. Once you hold a token and the portal sets a limit, a badge beside the title counts them, such as `2 of 10`. The card holds a table with these columns:

| Column | What it shows |
|---|---|
| **Token** | The first characters of the token, followed by an ellipsis. A token made a moment ago also carries a **New** badge. |
| **Created** | The date you made it. |
| **Expires** | The date it stops working, or **Never**. |
| (no heading) | A **Revoke** button. |

Tokens that have expired are not listed. Under the table: **Only the first characters of each token are kept. Lost the rest of one? Revoke it and create another.**

### When it is empty

With no token, the card shows a key icon, the heading **You have no API tokens** and the line **Create one when a script or another tool needs to use the API as you.**

## The create screen

Selecting **Create token** opens a screen headed **Create a token**, with a form that holds:

- **Expires after**, a menu with **7 days**, **30 days**, **90 days**, **1 year** and **Never expires**. **30 days** is chosen to begin with. Its help text reads **A token that expires limits the harm if it leaks. You can revoke any token sooner.**
- the line **The token is shown once, on the next page. Have somewhere ready to keep it.**
- the **Create token** and **Cancel** buttons

Selecting **Create token** returns you to the list, with the new token shown once.

## The revoke screen

Selecting **Revoke** on a row opens a screen headed **Revoke this token?**. It shows the token's first characters, its **Created** date and its **Expires** date, and the warning **Anything that uses this token will stop working as soon as you revoke it. A revoked token cannot be brought back.** The **Revoke token** button revokes it and returns you to the list with a message such as `Token ab12cd34… was revoked.` **Cancel** returns you to the list and revokes nothing.

If the token has gone already, because it expired or you revoked it elsewhere, the list shows **That token no longer exists.**

## What you can do here

- Make a token. See [How to get an API token](../api/get-an-api-token.md).
- Revoke a token. See [How to revoke an API token](../api/revoke-an-api-token.md).
- Read the data with a token. See [How to read a dataset's samples with a script](../api/read-a-datasets-samples-with-a-script.md).
- Find out what the API offers. See [API documentation](../api/api-docs.md).
