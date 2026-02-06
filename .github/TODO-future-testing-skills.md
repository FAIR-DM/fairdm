# Future Testing Skills — TODO

These testing capabilities are intentionally deferred and should be implemented as
separate, dedicated skills when the prerequisites are met.

## 1. Contract Testing Skill

**Prerequisite:** The REST API layer (DRF-based) must be stable and consumed by at
least one external portal or client.

**Scope:**

- API schema validation (response structure, field types, required fields)
- Backward compatibility checks for API responses
- Data format contract tests (JSON-LD, DataCite metadata exports)
- Interoperability tests (stable identifier resolution, content negotiation)

**Location:** Tests should live alongside the API app once it exists (e.g.
`tests/test_api/`), not in a separate `contract/` tree.

## 2. End-to-End (E2E) Testing Skill

**Prerequisite:** The framework has a stable, deployed portal (or the demo app is
running in a realistic server environment) and pytest-playwright is properly configured.

**Scope:**

- User journey tests (create project → add dataset → upload samples → publish)
- Browser-rendered output validation (HTMX interactions, Alpine.js state, accessibility)
- Form submission flows that involve JavaScript-enhanced widgets
- Responsive layout verification across Bootstrap 5 breakpoints

**Tooling:** pytest-playwright

**Note:** Component-level HTML testing (verifying Cotton component output) does NOT
require E2E tests. Use `django_cotton_bs5`'s `render_component` /
`render_component_soup` fixtures for that.
