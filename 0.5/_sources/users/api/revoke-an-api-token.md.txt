# How to revoke an API token

Revoking a token stops it working at once. Do it when a laptop is lost, a script is retired, or you think a token has been seen by someone else.

```{warning}
Revoking cannot be undone. Anything that uses the token stops working, and you have to create a new token and give it to that script.
```

## Steps

1. Open the account menu and choose **API tokens**, or go to `/account/tokens/` on your portal.
2. Find the token in the **Your tokens** table. Each row shows the first characters of a token, so match them with the start of the token your script uses. If you are not sure which is which, check the **Created** and **Expires** dates.
3. Choose **Revoke** on that row. The **Revoke this token?** page shows the token, when it was created and when it expires.
4. Choose **Revoke token**. To change your mind, choose **Cancel**.

## The result

The portal returns you to the list with the message "Token … was revoked", and the token is gone from the table. Your other tokens keep working.

To confirm, run this with the revoked token in `FAIRDM_TOKEN`. Change `PORTAL` to your portal's address.

```python
import os

import requests

PORTAL = "https://portal.example.org"

session = requests.Session()
session.headers["Authorization"] = f"Token {os.environ['FAIRDM_TOKEN']}"

response = session.get(f"{PORTAL}/api/v1/", timeout=30)
print(response.status_code)
```

It prints `401`. A token that has reached its end date stops working on its own and is no longer listed.

## Next

- [How to get an API token](get-an-api-token.md) to replace the one you revoked
- [API tokens](../account/api-tokens.md) for the page itself
