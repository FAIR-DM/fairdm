# How to restrict API tokens to some people

By default every signed-in person may create API tokens. You give tokens to some people only by naming a function that decides. Do this when scripts should run only for staff, or for a group your portal manages.

## Before you start

You need to edit the portal's settings module. The setting used here, `MVP_ACCOUNTS_API_TOKEN_ACCESS`, is described in [Settings](../reference/settings.md).

## Steps

1. Write a function that takes the person and returns whether they may hold tokens.

   ```python
   # myportal/access.py
   def may_hold_tokens(user):
       return user.groups.filter(name="API users").exists()
   ```

2. Name the function in the portal's settings by its dotted path.

   ```python
   # settings.py
   MVP_ACCOUNTS_API_TOKEN_ACCESS = "myportal.access.may_hold_tokens"
   ```

3. Restart the portal.

## The result

A person the function says no to sees no link to the token pages, and gets `403` if they open one of the three token pages (list, create and revoke) by address. They can still read public records through the API without a token.

A visitor who is not signed in is never passed to the function. They have no access to the token pages either way.

- The function decides who may reach the token pages. It does not revoke tokens a person already holds, and it is not asked when a token is used. Delete the tokens of someone you remove from the group.
- A path that cannot be imported raises `ImportError` when a page that calls the function is opened. Check the path.
- To remove the restriction, delete the setting.

How a token is sent and what it is allowed to do is in the [REST API reference](../reference/rest-api.md). The record of the decision to create tokens on the account pages is [ADR 0028](../../adr/0028-api-tokens-are-created-on-the-account-pages.md).
