# Account Center

The Account Center is where you manage the things that belong to your account and not to a record: your email addresses, your password, the accounts you sign in with and your API tokens. It is not where you edit your public profile. That is the [Edit profile](edit-profile.md) screen.

You reach it by opening the menu at the foot of the sidebar, where your photo and name are, and choosing **Account Center**. The address is `account-center/`. You must be signed in. Opening the address while signed out sends you to the [Sign in](sign-in.md) screen.

The screen is headed **Account Center**, with the line **Manage your account and see what's available to you here.** under it.

## The sidebar

On the screens of the Account Center, the sidebar shows an **Account Center** entry and an **Account** group. The group has one entry for each card below. Choosing an entry opens the screen that the card's button opens.

## The cards

The cards are laid out two across on a wide screen. Each has a title, a sentence and a button. The portal shows the cards below, in this order:

| Card | What it says | Button |
|---|---|---|
| **Email** | Add, remove and verify the addresses on your account, and choose the one we write to. | **Manage email** |
| **Password** | Change the password you sign in with, or set one if you do not have one yet. | **Change password** |
| **Connected accounts** | See the accounts you can sign in with, connect another one, or remove one. | **Manage connected accounts** |
| **Two-factor authentication** | Add a second step to signing in, so a stolen password is not enough on its own. | **Manage two-factor authentication** |
| **Sessions** | See the browsers and devices signed in to your account, and sign out the others. | **Manage sessions** |
| **API tokens** | Create tokens for scripts and tools that use the API as you, and revoke any you no longer need. | **Manage API tokens** |

The **API tokens** card appears only when the portal lets you hold tokens. See [API tokens](api-tokens.md).

A portal can add cards of its own.

## When it is empty

The screen has no empty state. A card appears only when the screen it opens exists, so a portal that has left a feature out also leaves out that feature's card.

## What you can do here

- Create or revoke an API token. See [API tokens](api-tokens.md), [How to get an API token](../api/get-an-api-token.md) and [How to revoke an API token](../api/revoke-an-api-token.md).
- Change your public profile. See [How to edit your profile](edit-your-profile.md).
