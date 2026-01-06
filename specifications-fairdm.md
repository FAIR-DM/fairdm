# FairDM Framework Specifications

This document contains feature specifications that should be implemented in the FairDM framework packages. These specifications define reusable, generic capabilities for scientific data management portals that can be applied across different scientific domains.

**Note:** These specifications were originally developed for the Global Heat Flow Database Portal but represent patterns and capabilities that should be extracted into the FairDM framework for reuse across other scientific data management projects.

---

## Documentation Infrastructure & Conventions

Define how documentation is authored, validated, and kept synchronized with governance and feature implementations. Establish the documentation information architecture distinguishing user guides, developer documentation, and governance materials. Define cross-linking strategies between governance documents and technical documentation. Establish a feature documentation checklist specifying what documentation must be updated when features ship. Define how specifications are referenced from documentation to enable traceability. Establish validation criteria including build processes, link checking, failure conditions, and minimum quality expectations. Ensure contributors can locate appropriate documentation locations, follow consistent checklists when shipping features, and execute repeatable documentation validation.

## Testing Infrastructure & Conventions

Define the testing strategy, test organization layers, and foundational test fixtures supporting feature validation. Establish test layer taxonomy (unit, integration, contract) and their organizational structure. Define naming conventions for test files and test functions. Establish minimal fixture datasets covering common workflows including data import, review submission, administrative approval, and export operations. Define testing patterns for schema mapping validation and round-trip data integrity. Ensure feature specifications can reference standard test layers and fixture locations unambiguously, minimal happy-path integration tests exist covering end-to-end workflows, and testing conventions provide clear guidance on test naming, organization, and required assertions.

## CI/CD Pipeline & Automation

Define continuous integration and deployment automation including pull request checks, main branch integration, and scheduled or on-demand operations. Establish test execution strategies determining which test suites run in different contexts. Define coverage collection and reporting expectations. Establish build and deployment automation sequences. Define environment-specific configurations for different deployment targets. Establish failure notification and handling procedures. Ensure contributors understand what automated checks will run on their contributions, CI failures provide actionable diagnostic information, and deployment to staging and production environments follows documented, auditable procedures.

## Curation Review Workflow

Define the scientific review workflow where domain experts curate and assess datasets for accuracy and completeness. Establish workflow states including submission, active review, revision requests, and approval for publication consideration. Define state transitions and authorized actors including reviewers and dataset contributors. Specify artifacts produced at each stage including review comments, quality assessments, and metadata corrections. Establish rejection and revision iteration patterns. Ensure every workflow transition has clearly defined triggering actions, required permissions, inputs, outputs, and audit events, and the workflow enforces that curation review completion is prerequisite to publication approval.

## Publication Approval Workflow

Define the administrative publication approval workflow controlling dataset transition from private to public visibility. Establish workflow states including pending approval, change requests, approval, publication, and rejection. Define state transitions restricted to administrative roles. Specify required administrative checks including provenance verification, metadata quality assessment, and export validation. Define the final publication action making data publicly accessible. Ensure publication approval is strictly separated from curation review permissions, every approval action is audited with timestamp and rationale, and rejected datasets can be returned to curation with specific feedback.

## Provenance & Attribution Model (Authors vs Curators vs Editors)

Define canonical data structures and attribution rules for publication metadata, scientific authors, portal contributors, and editorial approvers. Establish entity relationships for DOI and citation metadata, original scientific authors, portal contributors (reviewers and curators), and editorial approvers with action timestamps. Define attribution rules for data exports and public display. Establish audit and event requirements for editorial actions. Ensure given a dataset, the system can unambiguously identify original authors, curators, and editorial approvers, and provenance fields required at publication time are explicitly enumerated.

## Role Hierarchy & Permission Matrix

Define roles and permissions ensuring review and curation capabilities do not confer publication or approval authority. Restrict publication approval to designated administrative roles with tightly controlled assignment. Define the minimal role set and permission matrix mapping roles to capabilities. Establish who can grant or revoke role assignments. Define testable authorization rules and audit requirements. Ensure for each protected action the specification defines required permissions and denial behavior, and includes concrete authorization scenarios covering reviewer and administrator boundaries.

## Audit Trail for Editorial Actions

Define event logging requirements for administrative and editorial actions including approvals, rejections, revision requests, permission changes, role assignments, and dataset visibility state transitions. Establish event schema capturing actor, action, timestamp, affected object, and before/after state where applicable. Define retention policies and access rules for audit data. Establish how audit data is presented to administrators. Ensure every privileged action has a corresponding required audit event, and audit records are immutable and queryable by object and actor.

## Review Submission Package Requirements

Define submission completeness requirements when reviewers submit datasets for publication approval consideration. Establish minimum provenance requirements including scientific authors, DOI, and citation information. Define required metadata fields including abstract, methods, and quality assessments. Establish data completeness requirements including minimum measurements, coordinates, and mandatory fields. Define validation rules executed at submission time. Ensure required fields and artifacts are explicitly enumerated with validation rules, incomplete submissions are blocked with actionable error messages, and test coverage addresses missing or invalid submission elements.

## Publication Pipeline & Release Process

Define the publication process and artifacts for transitioning approved datasets to public visibility. Establish the publication trigger action and required preconditions. Define artifacts produced including public export files and metadata records. Establish automated process steps including export generation, file distribution, and index updates. Define any manual steps and responsible actors. Establish rollback strategies for publication failures. Ensure the publication pipeline is fully enumerated with clear responsibilities, publication operations are atomic (all steps succeed or all roll back), and every publication action is audited.

## Publish-Time Completeness Gates

Define completeness requirements that must be satisfied before publication approval. Establish provenance completeness requirements. Define minimum metadata requirements including abstract, license, and contributor information. Establish identifier requirements for DOI, ORCID, and ROR where available. Ensure required fields and artifacts are explicitly enumerated with validation rules, and validation failures are categorized into actionable error categories.

## Post-Publication Immutability & Amendment Workflow

Define what data becomes immutable after publication and how corrections or new versions are managed. Establish immutability boundaries specifying which fields or objects become locked. Define amendment and versioning models distinguishing new versions from patches and tracking lineage. Establish how DOI and public artifacts are updated or superseded. Ensure the specification defines clear rules preventing silent post-publication mutations, and defines an auditable amendment workflow.

## Automated Checks vs Manual Overrides

Define which validations are automated, which can be overridden, and how overrides are tracked. Establish which checks are hard gates versus soft warnings. Define override permissions and required audit trails. Establish how override rationale is captured and stored. Ensure every override is attributable to a specific actor, timestamped, and visible in audit logs.

## Public API Harvesting Contract

Define minimum REST API endpoints and field stability guarantees required for data harvesting. Establish required endpoints with request and response structures. Define pagination strategies. Establish field stability guarantees and versioning. Define error response contracts. Ensure a harvesting client can be implemented based solely on the specification.

## API Authorization Rules

Define authorization levels distinguishing public, authenticated, reviewer-restricted, and administrator-restricted access. Establish authorization rules for each endpoint or resource type. Define authentication token or session requirements where applicable. Establish expected error responses for unauthorized or forbidden requests. Ensure for each endpoint the specification defines allowed roles and denial behavior.

## API Versioning & Deprecation Policy

Define compatibility guarantees and deprecation procedures for the public API. Establish versioning scheme selecting from URL path versioning, header-based versioning, or media type versioning. Define backward-compatibility rules. Establish deprecation communication requirements and timelines. Ensure API consumers can determine when field or endpoint changes are breaking versus non-breaking.

## Reference Document Ingestion & Indexing

Define processes and metadata standards for adding and maintaining governance reference documents. Establish metadata schema for references including title, source, publication date, canonical link, and summary. Define indexing and discovery mechanisms within documentation systems. Ensure contributors can add new references with consistent metadata and appropriate cross-linking.
