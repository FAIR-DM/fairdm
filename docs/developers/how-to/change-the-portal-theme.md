# How to change the portal theme

A portal is styled with daisyUI themes, applied through django-mvp and daisy-cotton. You change the theme to match a community's or organisation's colours, or to let visitors pick their own.

## Before you start

You need the portal's settings module, the one that calls `fairdm.setup()`. The theme settings belong to django-mvp, which FairDM installs, and sit under `MVP_CONFIG["theme"]`. FairDM sets no theme of its own, so a portal starts on django-mvp's defaults: `light` for the default theme and `dark` for the dark one.

## Steps

1. Pick a daisyUI theme by name. The stylesheet django-mvp ships includes these: `abyss`, `acid`, `aqua`, `autumn`, `black`, `bumblebee`, `business`, `caramellatte`, `cmyk`, `coffee`, `corporate`, `cupcake`, `cyberpunk`, `dark`, `dim`, `dracula`, `emerald`, `fantasy`, `forest`, `garden`, `halloween`, `lemonade`, `light`, `lofi`, `luxury`, `night`, `nord`, `pastel`, `retro`, `silk`, `sunset`, `synthwave`, `valentine`, `winter` and `wireframe`.

2. In the settings module, after the `fairdm.setup()` call, set the default theme and the theme the toggle switches to. Assign the `theme` key and not the whole `MVP_CONFIG`, which also holds FairDM's own entries.

   ```python
   import fairdm

   fairdm.setup()

   MVP_CONFIG["theme"] = {
       "default": "corporate",
       "dark": "business",
   }
   ```

   `default` applies when a visitor has expressed no preference. `dark` is the theme the toggle in the navigation switches to and back from.

3. To let visitors choose from several themes, list them in `choices`. The toggle becomes a menu of those themes.

   ```python
   MVP_CONFIG["theme"] = {
       "default": "corporate",
       "dark": "business",
       "choices": ["corporate", "business", "nord", "dracula"],
   }
   ```

4. Restart the portal and open any page. A theme name that matches nothing falls through to the default theme without an error.

## The result

Every page uses the theme. A visitor's choice is remembered in their browser. If you remove a theme from `choices`, a visitor who had chosen it is moved to the default.

`MVP_CONFIG` is described in [Settings](../reference/settings.md), and the theme keys in django-mvp's documentation. To override a FairDM setting in general, see [How to override a FairDM setting](override-a-fairdm-setting.md). Why a portal is configured this way is explained in [How FairDM configures a portal](../../explanation/how-fairdm-configures-a-portal.md), and the styling stack in [The technology stack](../../explanation/the-technology-stack.md).
