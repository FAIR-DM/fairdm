# How to create a user account

Creating an account in the administration interface gives a person a sign-in without their having to sign up themselves. Do it when self-service signup is closed, or when you want to set someone up before they arrive.

## Before you start

You need the right to add people. None of the four [portal roles](../reference/portal-roles.md) holds it, so only a superuser, or a member of a group your portal made with that permission, sees **Add user**.

## Steps

1. Open the administration interface. See [Reaching the administration interface](../reference/portal-roles.md#reaching-the-administration-interface).
2. Under **Community**, choose **Users**.
3. Choose **Add user**.
4. Enter the person's **First name**, **Last name** and **Email**. They sign in with the email address, so it is the one field the account cannot do without.
5. Enter a **Password** and repeat it under **Password confirmation**. The password has to pass the portal's password checks.
6. Choose **Save**. The person's own page opens.

## The result

The person appears in the **Users** list with the account state **Invited**.

With the portal's default settings a person has to confirm their email address before they can sign in, and confirming it changes the state to **Claimed**. To skip that for someone you have already verified, tick **Verified** on a row of the **Email addresses** section of their page, with the address and **Primary** set, and save. The setting behind the default is `ACCOUNT_EMAIL_VERIFICATION`, described on the [settings reference](../../developers/reference/settings.md).

The new account holds no portal role and is not credited on any record. It sees what any signed-in person sees. To give it a role, follow [How to assign a portal role](assign-a-portal-role.md). To let it into a private record, follow [How to let a colleague into a private record](../../users/contributors/let-a-colleague-into-a-private-record.md).

To stop visitors creating accounts for themselves, follow [How to close self-service signup](close-self-service-signup.md).
