# Data Model: FairDM Documentation Baseline

This feature does not introduce new runtime database models. Instead, it formalises conceptual entities used to reason about documentation content and structure.

## Conceptual Entities

### Documentation Section
- **Description**: A logical grouping of documentation pages aimed at a specific audience or theme.
- **Examples**: Admin Guide, Contributor Guide, Developer Guide, Contributing.
- **Key attributes**:
  - Name and purpose.
  - Target audience (role).
  - Entry page (landing page).
  - Navigation structure (toctree / child topics).

### User Role
- **Description**: A type of user consuming the documentation, with specific goals and tasks.
- **Examples**: Developer, Portal Administrator, Contributor, Framework Contributor.
- **Key attributes**:
  - Primary goals.
  - Typical tasks.
  - Expected level of technical knowledge.

### Getting Started Journey
- **Description**: A curated, linear path through multiple documentation pages that enables a user to accomplish a meaningful outcome.
- **For this feature**: A developer-focused journey that covers running a demo portal, defining a simple Sample/Measurement model, registering it, and verifying it in the UI and via programmatic access.
- **Key attributes**:
  - Starting page.
  - Ordered list of steps/pages.
  - Expected outcome and validation criteria.

## Relationships

- A **Documentation Section** targets one or more **User Roles**.
- A **User Role** may rely on content from multiple **Documentation Sections** (e.g., developers may consult both the developer guide and contributing guide).
- A **Getting Started Journey** is implemented as a path through one or more **Documentation Sections**, tailored primarily to the Developer role.

## Validation Rules

- Each Documentation Section MUST have a clearly stated purpose and target audience.
- Each major User Role identified in the specification MUST have at least one obvious entry point in the documentation.
- The primary Getting Started Journey MUST be traversable using only links in the documentation (no external instructions required).
