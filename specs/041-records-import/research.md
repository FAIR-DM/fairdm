# Research: import a spreadsheet of samples or measurements into a dataset

## Assumptions checked

Each assumption the specification makes about what already works, checked against `main` at
`eed6473e` with its locked dependencies installed.

- **The modal component exists.** django-mvp 0.36.1 is installed and ships
  `mvp/templates/cotton/mvp/modal.html`, so `c-mvp.modal` is available for the dialog of types.
- **The card choice widget exists.** django-mvp-forms 0.11.0 is installed and
  `mvp_forms/widgets.py` defines `CardSelect` (a `RadioSelect` drawn as cards with an icon, a
  description and a mark), for the import options.
- **The import permission exists at the edit level.** `fairdm/contrib/contributors/access.py`
  maps `import_data` to `ContributionLevel.EDIT`, so a person with the edit level on a dataset
  holds `dataset.import_data`.
- **Both types carry a Local ID.** `Sample.local_id` (`fairdm/core/sample/models.py`) and
  `Measurement.local_id` (migration `measurement/0008_measurement_local_id`) both exist.
- **The reading libraries are installed.** django-import-export, tablib with its `ods` and `xlsx`
  extras (odfpy and openpyxl), Celery and django-celery-beat are dependencies on `main`.
- **The old import module is unreachable.** `fairdm/contrib/import_export/urls.py` registers no
  routes. Its views include `DataImportView`, `DataExportView` and `DatasetPublishConfirm`, and
  `BaseFairDMResource` lives in its `resources.py`. The registry's `ResourceFactory` is in
  `fairdm/registry/factories.py` and is the default for `resource_class` in
  `fairdm/registry/config.py`.
- **The location defect is real.** `LocatedResourceMixin.import_instance`
  (`fairdm/utils/location/resources.py`) catches the field errors into `errors`, then returns
  when no location column is in the row, before `raise ValidationError(errors)`. A row with
  invalid fields and no location columns is therefore reported valid. The fix is a requirement
  of this feature (FR-017).
