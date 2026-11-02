# How to change the entrance pane

The pane beside the sign-in form names the portal. You change it when the portal's name, description and authority are not what you want a visitor to read before signing in.

## Before you start

You need a templates directory in one of your portal's apps. The pane and the values it shows are described in [Entrance pages](../reference/entrance-pages.md).

If you only want a different name, description or authority, save them in the portal identity in the administration interface, or set `PORTAL_DESCRIPTION`. You do not need a template for that.

## Steps

1. Create `templates/cotton/entrance/aside.html` in your portal. FairDM's template of the same name is replaced by yours.

2. Declare the four attributes the component receives, then write the pane. Write the portal's name as a paragraph and not as a heading, because each entrance page already has one top-level heading, on its form.

   ```django
   {# templates/cotton/entrance/aside.html #}
   <c-vars name description authority authority_url />
   <div class="dce:flex dce:max-w-xl dce:flex-col dce:gap-4">
     <p class="dce:text-4xl dce:font-bold dce:tracking-tight">{{ name }}</p>
     <p class="dce:text-lg">Heat flow measurements from five continents, open to everyone.</p>
   </div>
   ```

3. Open the sign-in page in a window wider than 1024 pixels.

## The result

The pane shows your words in place of FairDM's. On a narrower window the pane is not drawn, as before. The pane is [`c-entrance.aside`](../reference/components.md#c-entranceaside). To change where the pane sits, see [How to change the entrance layout](change-the-entrance-layout.md).
