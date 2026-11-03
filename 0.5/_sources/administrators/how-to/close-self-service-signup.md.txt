# How to close self-service signup

Closing signup stops visitors creating accounts for themselves, so that only the accounts you create exist. Do it for a portal that serves a known group of people.

A portal has two controls for this. Use the setting when you can change the portal's configuration. Use the switch when you can only use the administration interface.

## Close signup with the setting

You need to be able to edit the portal's settings module, or to ask whoever deploys the portal.

1. In the portal's settings, set `FAIRDM_INVITATION_ONLY_SIGNUP` to `True`:

    ```python
    FAIRDM_INVITATION_ONLY_SIGNUP = True
    ```

2. Restart the portal so it reads the setting.

The default is `False`. The setting is described on the [settings reference](../../developers/reference/settings.md).

With the setting on, the signup page does not create an account. A signup that reaches the portal with an email address already verified in the same session is still accepted.

## Close signup with the switch

You need to be able to change switches. A superuser can.

1. Open the administration interface. See [Reaching the administration interface](../reference/portal-roles.md#reaching-the-administration-interface).
2. Under **django-waffle**, choose **Switches**, then the switch named `allow_signup`.
3. Untick **Active**.
4. Choose **Save**.

With the switch off, the portal accepts no signup at all. That includes a signup that arrives with a verified email address, and a signup through ORCID. To open signup again, tick **Active** and save.

## The result

Visitors cannot create an account. Accounts that exist keep working, and you create further ones with [How to create a user account](create-a-user-account.md).
