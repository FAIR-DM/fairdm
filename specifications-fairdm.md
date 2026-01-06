# FairDM Framework Specifications

This document contains feature specifications that should be implemented in the FairDM framework packages. These specifications define reusable, generic capabilities for scientific data management portals that can be applied across different scientific domains.

**Note:** These specifications were originally developed for the Global Heat Flow Database Portal but represent patterns and capabilities that should be extracted into the FairDM framework for reuse across other scientific data management projects.

---

## Documentation Infrastructure & Conventions

Create a feature spec defining how documentation is authored, validated, and kept in sync with the constitution and features. The spec should define the Sphinx information architecture: where new docs live (user guides vs dev docs vs governance docs), where governance materials live (constitution + references) and how they are cross-linked, the "feature docs checklist" that lists what docs must be updated when a feature ships, how specs are referenced from docs so readers can trace behavior back to a spec, what "docs are valid" means including build steps and link checks and failure conditions and minimum expectations, and any migration or conformance work needed to bring existing docs into the conventions. The output should be specs/001-docs-infrastructure/ with spec.md, plan.md, and tasks.md. Reference the constitution at .specify/memory/constitution.md, the existing Sphinx structure at docs/, and the spec template at .specify/templates/spec-template.md. Acceptance criteria should be testable: a contributor can find where to add docs, can follow a checklist when shipping features, and documentation validation is explicit and repeatable.

## Testing Infrastructure & Conventions

Create a feature spec defining the testing strategy, test layers, and minimum fixtures required to make later specs enforceable. The spec should define test layers (unit/integration/contract) and where they live under tests/, naming conventions for test files and test functions, minimal fixture datasets for import, review submission, admin approval, and export workflows, and how to write tests for schema mapping and round-trip integrity. The output should be specs/002-testing-infrastructure/ with spec.md, plan.md, and tasks.md. Reference the constitution at .specify/memory/constitution.md, the existing test structure at tests/, and pyproject.toml for test tooling configuration. Acceptance criteria should ensure a new feature spec can reference a standard test layer and fixture location without ambiguity, a minimal happy path integration test plan exists for import to review to approval to export, and the spec defines conventions for test naming, location, and required assertions.

## CI/CD Pipeline & Automation

Create a feature spec defining continuous integration and deployment automation including what runs on PR, what runs on merge to main, and what runs nightly or on-demand. The spec should define test execution strategy in CI (which test suites run when), coverage collection and reporting expectations, build and deployment automation steps, environment-specific configurations, and failure notification and handling. The output should be specs/003-cicd-pipeline/ with spec.md, plan.md, and tasks.md. Reference the constitution at .specify/memory/constitution.md, existing CI configuration files (GitHub Actions, etc.), and pyproject.toml for tooling. Acceptance criteria should ensure a contributor knows what automated checks will run on their PR, CI failures provide actionable feedback, and deployment to staging/production follows documented and auditable steps.

## Curation Review Workflow

Create a feature spec defining the literature assessment review workflow where reviewers curate and assess datasets for scientific accuracy and completeness. The spec should define states (submitted, under review, needs revision, approved for publication review), transitions and allowed actors (reviewers, dataset submitters), what artifacts are produced at each stage (review comments, quality assessments, metadata corrections), and rejection and revision loops. The output should be specs/101-curation-review-workflow/ with spec.md, plan.md, and tasks.md. Reference the constitution at .specify/memory/constitution.md especially governance principles, docs/guides/reviewing.md if present, and any review-related models in the codebase. Acceptance criteria should ensure every transition has triggering action, required permissions, inputs, outputs, and audit events clearly defined, and the workflow enforces that curation review completion is required before publication approval can begin.

## Publication Approval Workflow

Create a feature spec defining the admin-only publication approval workflow that gates datasets from private to public visibility. The spec should define states (pending approval, changes requested, approved, published, rejected), transitions and allowed actors (admin-only role), what checks admins must perform (provenance completeness, metadata quality, export validation), and the final publication action that makes data publicly visible. The output should be specs/102-publication-approval-workflow/ with spec.md, plan.md, and tasks.md. Reference the constitution at .specify/memory/constitution.md especially governance and dual-review principles, and any admin approval UI or models in the codebase. Acceptance criteria should ensure publication approval is strictly separated from curation review permissions, every approval action is audited with timestamp and rationale, and rejected datasets can be sent back to curation with specific feedback.

## Provenance & Attribution Model (Authors vs Curators vs Editors)

Create a feature spec defining canonical storage and attribution for publication metadata (DOI, citation), scientific authors, portal contributors (reviewers and curators), and editorial approvers (admin actions plus timestamps). The spec should define entities and relationships, attribution rules for export and public display, and audit or event requirements for editorial actions. The output should be specs/103-provenance-attribution/ with spec.md, plan.md, and tasks.md. Reference the constitution at .specify/memory/constitution.md, any existing contributor or ORCID or ROR related data such as orcid_data.json, and existing models relating to datasets, publications, and contributors in the project/ folder. Acceptance criteria should ensure that given a dataset, the system can unambiguously list original authors, curators, and editors/approvers, and provenance fields required at publish-time are explicitly enumerated.

## Role Hierarchy & Permission Matrix

Create a feature spec defining roles and permissions so that review and curation permissions do not imply publish or approve permissions, publication approval is restricted to a designated admin role, and role assignment is tightly controlled. The spec should define the minimal role set and a permission matrix (role by capability), who can grant or revoke roles, and testable authorization rules and audit requirements. The output should be specs/104-role-permissions/ with spec.md, plan.md, and tasks.md. Reference the constitution at .specify/memory/constitution.md and the existing auth and permission approach in the codebase such as Django groups, permissions, and guardian. Acceptance criteria should ensure for each protected action the spec defines required permissions and denial behavior, and the spec includes at least five concrete auth scenarios covering reviewer vs admin boundaries.

## Audit Trail for Editorial Actions

Create a feature spec defining what events must be logged for admin and editorial actions: approve, reject, request revisions, permission or role changes, and dataset visibility state changes. The spec should define event schema (who, what, when, object, before/after where applicable), retention and access rules for audit data, and how audit data is presented to admins with minimal requirements. The output should be specs/105-audit-trail/ with spec.md, plan.md, and tasks.md. Reference the constitution at .specify/memory/constitution.md and existing logging or audit patterns in the codebase (search for audit, log entry, history, admin actions). Acceptance criteria should ensure every privileged action has a corresponding required audit event, and audit records are immutable and queryable by object and actor.

## Review Submission Package Requirements

Create a feature spec defining what must be present when a reviewer submits a dataset for publication approval consideration. The spec should define minimum provenance requirements (scientific authors, DOI, citation), required metadata fields (abstract, methods, quality scores), data completeness requirements (minimum measurements, coordinates, required fields), and validation rules that execute at submission time. The output should be specs/106-review-submission-requirements/ with spec.md, plan.md, and tasks.md. Reference the constitution at .specify/memory/constitution.md and any existing review submission docs and admin review UI. Acceptance criteria should ensure the spec enumerates required fields and artifacts with clear validation rules, incomplete submissions are blocked with actionable error messages, and test cases cover missing or invalid submission elements.

## Publication Pipeline & Release Process

Create a feature spec defining the steps and artifacts for publishing approved datasets to public visibility. The spec should define the publication trigger action, artifacts produced (public export files, metadata records), automated steps (export generation, file uploads, index updates), manual steps if any and who performs them, and rollback strategy if publication fails. The output should be specs/301-publication-pipeline/ with spec.md, plan.md, and tasks.md. Reference the constitution at .specify/memory/constitution.md and existing publishing or release docs if any under docs/publishing/. Acceptance criteria should ensure the pipeline is fully enumerated with clear responsibilities, publication is atomic (all steps succeed or all roll back), and every publication action is audited.

## Publish-Time Completeness Gates

Create a feature spec defining what must be present before publication approval. The spec should define provenance completeness requirements, minimum metadata requirements (abstract, license, contributors), and identifier requirements (DOI where available, ORCID or ROR where available). The output should be specs/302-publish-gates/ with spec.md, plan.md, and tasks.md. Reference the constitution at .specify/memory/constitution.md. Acceptance criteria should ensure the spec enumerates required fields and artifacts with validation rules, and validation failures are categorized into actionable error reasons.

## Post-Publication Immutability & Amendment Workflow

Create a feature spec defining what becomes read-only after publication and how corrections or new versions are handled. The spec should define immutability boundaries (which fields or objects lock), amendment or versioning model (new version vs patch, lineage), and how DOI or public artifacts are updated or superseded. The output should be specs/303-post-publication-amendments/ with spec.md, plan.md, and tasks.md. Reference the constitution at .specify/memory/constitution.md. Acceptance criteria should ensure the spec defines clear rules preventing silent post-publication mutation, and defines an auditable amendment workflow.

## Automated Checks vs Manual Overrides

Create a feature spec defining what is automated, what can be overridden, and how overrides are tracked. The spec should define which checks are hard gates vs soft warnings, override permissions and required audit trails, and how override rationale is captured. The output should be specs/305-checks-vs-overrides/ with spec.md, plan.md, and tasks.md. Reference the constitution at .specify/memory/constitution.md. Acceptance criteria should ensure every override is attributable, timestamped, and visible in audit logs.

## Public API Harvesting Contract

Create a feature spec defining minimum REST API endpoints and stable field guarantees needed for harvesting. The spec should define required endpoints, request and response shapes, and pagination, stability guarantees for fields, and error contracts. The output should be specs/401-public-api-contract/ with spec.md, plan.md, and tasks.md. Reference the constitution at .specify/memory/constitution.md and existing REST API implementation and any schema docs (e.g., DRF spectacular). Acceptance criteria should ensure a harvester client can be implemented solely from the spec.

## API Authorization Rules

Create a feature spec defining what is public vs authenticated vs reviewer-only vs admin-only. The spec should define authorization rules per endpoint or resource, token or session requirements if applicable, and expected error responses for unauthorized or forbidden. The output should be specs/402-api-authorization/ with spec.md, plan.md, and tasks.md. Reference the constitution at .specify/memory/constitution.md and existing auth patterns and permission model. Acceptance criteria should ensure for each endpoint the spec defines allowed roles and denial behavior.

## API Versioning & Deprecation Policy

Create a feature spec defining compatibility guarantees and deprecation windows for the public API. The spec should define versioning scheme (URL path, header, or media type; pick one), backward-compatibility rules, and deprecation communication requirements and timelines. The output should be specs/403-api-versioning/ with spec.md, plan.md, and tasks.md. Reference the constitution at .specify/memory/constitution.md. Acceptance criteria should ensure a consumer can know when a field or endpoint change is breaking vs non-breaking.

## Reference Document Ingestion & Indexing

Create a feature spec defining process and metadata for adding and maintaining governance references. The spec should define metadata schema for references (title, source, date, canonical link, summary) and indexing or discovery expectations in docs. The output should be specs/501-reference-ingestion/ with spec.md, plan.md, and tasks.md. Reference the constitution at .specify/memory/constitution.md and docs/constitution/references/ current structure. Acceptance criteria should ensure a contributor can add a new reference with consistent metadata and cross-links.
