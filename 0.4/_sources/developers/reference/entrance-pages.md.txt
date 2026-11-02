# Entrance pages

The entrance pages are the pages a visitor sees before signing in: sign in, create an account, reset a password, confirm an email address and the second step of a two-factor sign-in. This page describes the layout they share, where the pane's words come from and the templates a portal replaces to change them. It does not describe the forms, which django-mvp-accounts draws, or how to change the layout, which [How to change the entrance layout](../how-to/change-the-entrance-layout.md) covers.

## The layout

Every entrance page uses one template, `mvp_accounts/entrance/base.html`, which FairDM ships. It places the form in one half of the window with the portal's logo above it, and a pane in the other half. The pane's background is `c-background.aurora` over `c-background.grid`, drawn in the theme's colours. Below the `lg` breakpoint the pane is left out and the form has the page.

The layout is the `c-sign-in.split` component from daisy-cotton-ext, which FairDM installs. The pages themselves come from django-mvp-accounts. FairDM's template links two stylesheets, `css/daisy-cotton-ext.css` and `css/fairdm.css`, because the entrance pages do not extend FairDM's base template.

## The pane

The pane is the [`c-entrance.aside`](components.md#c-entranceaside) component. It shows these lines:

| Line | Where it comes from |
|---|---|
| Eyebrow | The fixed text "Research data portal". |
| Name | The name saved in the portal identity, else `PAGE_CONFIG["brand"]["text"]`, which is `SITE_NAME` unless a portal changes it. Drawn as a paragraph, not a heading. |
| Description | The description saved in the portal identity, else the `PORTAL_DESCRIPTION` setting. Left out when there is neither. |
| Run by | The name of the `Authority` saved in the portal identity (`fairdm.contrib.identity`), linked when it has an address. Left out when it has no name. |

The identity and the authority are edited in the administration interface. The settings are described in [Settings](settings.md).

Nothing in the pane is needed to sign in.

## Templates a portal replaces

| Template | Replaces | Receives |
|---|---|---|
| `cotton/entrance/aside.html` | The pane's words, the `c-entrance.aside` component. | `name`, `description`, `authority` and `authority_url`. |
| `mvp_accounts/entrance/base.html` | The whole layout. It extends `mvp_accounts/entrance/layout.html`, whose blocks are `logo`, `heading`, `providers`, `content` and `footer`, and wraps `{{ block.super }}` in a layout component. | The page's own context, with `identity`, `config` and `page_config` from FairDM's context processor. |

A portal's templates are found before FairDM's because a portal's apps are listed ahead of FairDM's ([ADR 0004](../../adr/0004-portal-apps-precede-framework-apps.md)).

The layouts daisy-cotton-ext ships, with the attributes and slots of each, are listed in its own documentation. django-mvp-accounts documents the pieces `{{ block.super }}` hands to the layout.

## Tasks

- [How to change the entrance pane](../how-to/change-the-entrance-pane.md)
- [How to change the entrance layout](../how-to/change-the-entrance-layout.md)
