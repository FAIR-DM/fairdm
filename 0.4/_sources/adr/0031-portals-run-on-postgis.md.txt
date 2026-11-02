# ADR 0031 — Portals run on PostgreSQL with PostGIS

**Status:** accepted

## Decision

Every FairDM portal runs on PostgreSQL with the PostGIS extension, and FairDM installs GeoDjango.
The database engine is `django.contrib.gis.db.backends.postgis` in every environment, development
and the test suite included. There is no setting to run on plain PostgreSQL or on SQLite, and no
way to install FairDM without GeoDjango.

This reverses the removal of GeoDjango in #196.

## Why

Two decimal columns hold a point and nothing more. A portal could not ask which records lie inside
an area, which lie near one another, or which country a sample came from, without loading every
location into Python. One portal types each site's country, region, continent and geological
domain by hand for this reason.

GeoDjango was left out because GDAL was hard to install on Windows and roughly doubled the size of
the image. Neither holds any more. Development runs in Docker, where PostGIS is one image and the
development image carries GDAL, so Windows needs no GDAL of its own. A portal runs on a single
server that pulls its image once per release, so the extra size costs disk space and a slower
first pull, and nothing while it runs.

Making PostGIS optional would mean two code paths for every spatial feature, and a portal would
find out which one it was on only when a query failed. One database is simpler to build on, to
test and to support.

## Consequences

- A portal's database needs the PostGIS extension, and its server or image needs GDAL, GEOS and
  PROJ. `fairdm.E101` refuses any other engine in production.
- Development needs a PostGIS server. `docker-compose.yml` provides one, and the development image
  provides the libraries.
- The test suite runs on PostGIS locally and in CI. The shared test workflow provides no database
  service, and the shared build workflow's type check cannot load GeoDjango without GDAL, so
  FairDM keeps its own test and build workflows.
- Spatial features, such as storing locations as geometries and querying them, can be built on the
  database directly.
