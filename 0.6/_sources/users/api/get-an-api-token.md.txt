# How to get an API token

A token lets a script use the API as you, without your password. You need one to create, change or delete records, and to read records that are not public.

## Before you start

- Sign in to your portal.
- Install `requests` for Python with `python -m pip install requests`.

## Steps

1. Open the account menu and choose **API tokens**, or go to `/account/tokens/` on your portal. The page is described in [API tokens](../account/api-tokens.md).

   If **API tokens** is not in the menu, your portal does not give tokens to your account. Ask your portal's administrator. Public records can still be read without a token.

2. Choose **Create token**.
3. Under **Expires after**, choose how long the token should work: **7 days**, **30 days**, **90 days**, **1 year** or **Never expires**. A token that expires limits the harm if it leaks, so choose the shortest time your script needs.
4. Choose **Create token** again. You return to the **API tokens** page, where **Your new token** shows the complete token.
5. Choose **Copy**, and keep the token somewhere private, as you would a password. The portal shows it once. It keeps only the first characters, so it cannot show you the rest later.
6. Choose **I have copied it**.
7. Put the token in an environment variable, so it stays out of your script. In a Linux or macOS terminal:

   ```bash
   export FAIRDM_TOKEN="paste-your-token-here"
   ```

   In Windows PowerShell:

   ```powershell
   $env:FAIRDM_TOKEN = "paste-your-token-here"
   ```

   Change `paste-your-token-here` to the token you copied.

8. Check that the portal accepts it. Save this as `check_token.py`, and change `PORTAL` to your portal's address. The other how-to guides in this section start from the same lines.

   ```python
   import os

   import requests

   PORTAL = "https://portal.example.org"

   session = requests.Session()
   session.headers["Authorization"] = f"Token {os.environ['FAIRDM_TOKEN']}"

   response = session.get(f"{PORTAL}/api/v1/", timeout=30)
   print(response.status_code)
   ```

   Run it with `python check_token.py`.

## The result

The script prints `200`. Your token is on the **API tokens** page, listed by its first characters with the dates it was created and expires. A script that sends it is treated as you, with the access you have.

If the script prints `401`, the portal does not accept the token. It was copied incompletely, has expired or was revoked. Create another.

You can hold up to ten tokens at a time unless your portal sets another limit, so a laptop and a server can each have their own. Once you reach the limit, the page says so and **Create token** is hidden until you [revoke one](revoke-an-api-token.md).

## Next

- [How to read a dataset's samples with a script](read-a-datasets-samples-with-a-script.md)
- [How to revoke an API token](revoke-an-api-token.md)
- The [REST API reference](../../developers/reference/rest-api.md) for what the API accepts and returns
