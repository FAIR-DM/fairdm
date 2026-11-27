# ADR 0005 — A measurement type nominates its value; the base reports and formats it

**Status:** accepted

## Decision

A measurement type declares a `value` field, and optionally an `uncertainty` field beside it. It
does not override the reporting method. `Measurement.get_value()` returns whatever the type
nominated, pairs it with the uncertainty where one is recorded, and falls back to the record's name
for a type that nominates nothing. `Measurement.print_value()` renders that for a person, delegating
to the framework's quantity formatter rather than assembling a string.

`value` may be a quantity carrying units, or a plain number. Uncertainty arithmetic is attempted
only where the value supports it.

The formatter is installed on the shared unit registry by the framework's application-startup hook.

## Why

The alternative — every type overriding the reporting method to return its own formatted string —
was what the documentation taught, and it puts presentation in the model layer once per type. Every
portal then writes the same formatting by hand and gets it subtly differently, and the framework has
no way to render a measurement it did not define.

Declaring a field is also the smaller thing to ask of a portal developer, and the framework already
knows how to render a quantity with an uncertainty. There was no reason to make each type re-answer
a question the framework had already answered.

The startup hook matters more than it looks. The formatter previously installed itself as a side
effect of importing a template tag module, and Django imports those lazily — only when a template
loads them. A value rendered outside a template, in a management command, an API response or a
test, silently got the unit library's default format instead of the framework's. Installing at
startup makes the format a property of the application rather than of whether a page happened to
render first.

## Revisit if

A measurement type needs more than one reportable quantity. The convention is deliberately
single-valued, and the honest answer then is a named set rather than a second special attribute —
`value` should not grow a `value2` beside it.
