# Theme

Customization of your portals theme is done using SCSS variables located in your project's `assets/scss/_bs5_variables.scss` file. This file contains a list of SCSS variables that are used to define the colors, fonts, and other visual elements of your portal. By changing these variables, you can easily customize the look and feel of your portal to match your community or organisation's branding.

```{warning}
We recommend only customizing variables that affect visual elements of the portal (e.g. colors, fonts, etc.). Modifying other variables that control structure or layout, such as the Boostrap 5 grid variables, will likely cause unexpected and unwanted behavior.
```

## Changing the primary color

In most cases, changing the primary color of your theme is the only modification that is required to match your portal's branding. To change the primary color, simply modify the `$primary` variable in the `assets/scss/_bs5_variables.scss` file.

```scss
$primary:       #5400d2; # Purple
```


## Further customisation

You can further customize your portal's theme by adding any relevant Bootstrap 5 SCSS variables to the `assets/scss/_bs5_variables.scss` file. For more information, please refer to the [Bootstrap 5 documentation](https://getbootstrap.com/docs/5.3/).