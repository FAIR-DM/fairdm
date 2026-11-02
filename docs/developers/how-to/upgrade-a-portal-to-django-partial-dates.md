# How to upgrade a portal to django-partial-dates

FairDM now stores partial dates through [django-partial-dates](https://django-partial-dates.fairdm.org/) in place of django-partial-date. A date is stored as the text `1990`, `1990-06` or `1990-06-14` instead of as a timestamp whose seconds hold the precision. FairDM's own migrations convert the columns of its own tables. You convert the columns of your portal's own models, and you change any code that reads a partial date.

## Before you start

- Back up the database, and read [How to back up a portal](back-up-a-portal.md) if the scheduled backups are not running.
- Run the whole procedure against a copy of the database first, and time it. Each conversion locks its table until the migration ends.
- Plan to stop everything that writes to the database, Celery workers included, from the start of the migration until it finishes.

## Steps

1. Install the new FairDM release. It depends on django-partial-dates 0.1, and no longer on django-partial-date. If the portal imports `partial_date` itself, it needs that package installed until step 3 is done.

2. Point the portal's existing migrations at the stand-in field. Do this for every migration that creates or alters a field declared with `fairdm.db.models.PartialDateField` or with django-partial-date's own field:

   ```python
   import partial_dates.conversion

   field = partial_dates.conversion.OldPartialDateField(blank=True, null=True)
   ```

   Replace `fairdm.db.fields.PartialDateField` and `partial_date.fields.PartialDateField` in those migrations and keep every option. Keeping the old name is the mistake to avoid here: a model field declared with `fairdm.db.models.PartialDateField` keeps that path, so `makemigrations` finds no change and the column stays a timestamp, which the field can no longer read.

3. If a model declares django-partial-date's field directly, change it to `fairdm.db.models.PartialDateField`.

4. Make the migration, and change each `AlterField` that Django wrote for a date to `ConvertPartialDateField`:

   ```bash
   python manage.py makemigrations
   ```

   ```python
   from partial_dates.conversion import ConvertPartialDateField

   operations = [
       ConvertPartialDateField(
           model_name="sedimentsample",
           name="collected_on",
           field=fairdm.db.fields.PartialDateField(blank=True, null=True),
       ),
   ]
   ```

   Change nothing else in the operation. Django's own `AlterField` fails on a table that holds rows.

5. Change the code that reads a partial date. The value is a different class:

   | Before | Now |
   |---|---|
   | `from partial_date import PartialDate` | `from partial_dates import PartialDate, Precision` |
   | `PartialDate("1990-06")` | `PartialDate.fromisoformat("1990-06")`, or `PartialDate(1990, 6)`. `"1990-6"` now raises a `ValueError`. |
   | `value.date` | `value.start`, the first day of the period, or `value.end`, the last. `value.year`, `value.month` and `value.day` hold the recorded parts. |
   | `value.precision == 2`, `PartialDate.DAY` | `value.precision is Precision.DAY`. In a template, compare with the text `"day"`. |
   | `fairdm.core.dates.precedes(a, b)` | `a.relation_to(b) is Relation.BEFORE`, with `Relation` from `partial_dates`. |

   `str(value)` is unchanged. The [django-partial-dates guide](https://django-partial-dates.fairdm.org/developer/moving-from-django-partial-date.html) lists every other change, including what filters on a date now match.

6. Stop everything that writes to the database, then apply the migrations:

   ```bash
   python manage.py migrate
   ```

   Migrate with `migrate`, never with the output of `sqlmigrate`, which holds no check of the values.

7. If the migration stops with `RefusedValuesError`, a column holds a value django-partial-date never wrote, and nothing in that table has changed. The error names the model, the field and the rows. Correct each row as the [table in the django-partial-dates guide](https://django-partial-dates.fairdm.org/developer/moving-from-django-partial-date.html#correct-a-refused-value) says, then run `migrate` again.

8. Check that nothing is left to do:

   ```bash
   python manage.py makemigrations --check --dry-run
   ```

Keep django-partial-dates in the portal's requirements if it names the package itself. Its migrations import it, and every new database is built from them.

## Going back

Each conversion can be reversed, and reversing restores the timestamp each row held. Run `migrate` for the app with the number of the migration before the conversion.
