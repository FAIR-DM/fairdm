# Planning notes: autocomplete fields for records, people and organizations

Suggestions from the maintainer for research and planning. The plan answers each one by name.

## Build on django-tomselect and django-mvp-forms

"We will use django-tomselect by default for view-backed implementations. Any other autocomplete
libraries we have installed can be removed. django-mvp-forms already provides reasonable stylistic
support for django-tomselect."

## Single and multiple, ready to use

"Most views will require single and multi select fields/widgets to go with them. We don't want end
users wiring things up themselves."

## Checkboxes for multiple selection, chips for tags only

"For multi select, prefer the checkbox style over chips. Chips are only advisable for tag-type
fields."

## The search box sits in the dropdown

"Prefer dropdown style where the search is in the dropdown rather than the input itself."

## Fields can be customised

"Fields need some customisation to control various things like if they show private objects or
not. E.g a public list filter doesn't require private objects in the dropdown."

## Vocabulary concepts wait for their own field

"Vocabulary concepts are out of scope. A dedicated field will eventually be created inside the dcv
package." Until then the keyword filters and the contribution roles field move to django-mvp-forms'
tom-select widget that needs no view, so django-autocomplete-light can be removed now.
