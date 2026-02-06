# Audience Guide for FairDM Documentation

Detailed profiling and content strategy for each FairDM documentation audience. Read this when creating substantial new documentation or when unsure how to frame content for a specific audience.

## Audience Profiles

### Portal Users (user-guide/)

**Who**: Researchers, lab technicians, graduate students, data contributors — people who interact with a live FairDM portal to submit, browse, or download research data.

**Technical level**: Non-technical. Comfortable with web browsers and forms. May not know what Python, Django, or a database is.

**Goals**:

- Submit research data and metadata correctly
- Find and download existing datasets
- Manage their account and collaborate with team members
- Understand what FAIR means for their work (at a practical level)

**Writing approach**:

- Step-by-step instructions with screenshots where helpful
- Avoid technical jargon; explain domain terms in plain language
- Use "you" and active voice ("Click the Submit button" not "The Submit button should be clicked")
- Focus on *what* to do, not *why* it works
- Include "What you'll need" prerequisites
- End guides with "What you've accomplished" checklists

**Content types**: How-to guides, UI walkthroughs, FAQ, getting started tutorials

**Citations**: Rarely needed. Only when explaining FAIR concepts at a high level.

**Cross-references**: Link to other UG pages and occasionally PA pages (for permission issues). Never link to specs or constitution.

### Portal Administrators (portal-administration/)

**Who**: IT staff, lab managers, data stewards, principal investigators with admin access — people responsible for configuring and maintaining a portal instance.

**Technical level**: Intermediate. Comfortable with Django admin interface. May know basic Python but are not developers.

**Goals**:

- Manage users, roles, and permissions
- Configure portal settings
- Ensure data quality and metadata compliance
- Handle backups, monitoring, and troubleshooting
- Set up authentication (SSO, OAuth)

**Writing approach**:

- Task-oriented with clear outcomes
- Reference Django admin interface elements by name
- Provide configuration examples (settings, admin screens)
- Include security and permission implications
- Warn about destructive operations

**Content types**: Configuration guides, admin procedures, permission matrices, troubleshooting

**Citations**: Occasionally, when discussing data governance standards or compliance requirements.

**Cross-references**: Link to UG pages for user-facing impact, PD pages for deployment context. Rarely link to specs.

### Portal Developers (portal-development/)

**Who**: Research software engineers, lab developers, domain scientists with Python skills — people building a portal for their research community using FairDM.

**Technical level**: Technical. Know Python and basic Django. May not be professional developers.

**Goals**:

- Set up a development environment
- Define domain-specific Sample and Measurement models
- Register models with the FairDM registry
- Customise templates, themes, and plugins
- Deploy to production
- Integrate with external systems (APIs, imports)

**Writing approach**:

- Complete, runnable code examples (not fragments)
- Explain the "what" and "why" of configuration choices
- Show both minimal and advanced patterns
- Provide copy-pasteable code blocks
- Link to API reference and specs for deeper context

**Content types**: Tutorials, configuration reference, API guides, deployment guides, model examples

**Citations**: When discussing FAIR implementation details, data standards, or design rationale.

**Cross-references**: Must link to relevant specs. Link to constitution when explaining design decisions. Link to UG/PA for user-facing documentation of features.

### Framework Contributors (contributing/)

**Who**: Open-source developers, advanced research engineers — people contributing code, tests, or documentation to the FairDM framework itself.

**Technical level**: Advanced. Strong Python, Django, testing, and software architecture skills.

**Goals**:

- Set up the FairDM development environment
- Understand framework architecture and design decisions
- Write tests that meet coverage requirements
- Follow coding standards and review processes
- Propose and document new features

**Writing approach**:

- Peer-to-peer technical tone
- Reference internal architecture and code paths
- Explain *why* architectural decisions were made (link to constitution)
- Provide pattern examples rather than exhaustive tutorials
- Include testing requirements for all contributions

**Content types**: Architecture docs, coding standards, testing guides, contribution workflows, documentation guidelines

**Citations**: When establishing technical rationale or referencing academic work that informed design.

**Cross-references**: Must link to constitution principles. Link to specs for feature context. Link to PD docs for user-facing API documentation.

## Content Strategy by Type

### Tutorials (learning-oriented)

**Primary audiences**: UG, PD

- Titled "Getting Started with X" or descriptive action
- Sequential steps (Step 1, Step 2...)
- End with accomplishment summary
- Include prerequisites
- One concept per tutorial

### How-to Guides (task-oriented)

**Primary audiences**: UG, PA, PD

- Titled "How to X" or imperative form
- Assume reader knows what they want
- Focus on a single task
- Include edge cases and gotchas

### Reference (information-oriented)

**Primary audiences**: PD, FC

- Complete and accurate above all else
- Structured consistently (tables, definition lists)
- Use `{contents}` directive with `:local:` for navigation
- Minimal narrative; maximum precision

### Explanation (understanding-oriented)

**Primary audiences**: PD, FC, overview

- Discuss "why" not just "how"
- Connect to principles and rationale
- Use citations for claims about standards
- May cross-reference multiple sections

## FAIR Data Claims — Citation Requirements

When documentation makes claims about FAIR principles, research data management, or scientific standards, citations are **mandatory**. Common citation contexts:

| Claim type | Citation required? | Example |
|------------|-------------------|---------|
| FAIR principles definition | Yes | {cite}`Wilkinson2016` |
| Research data management standards | Yes | Cite relevant standard |
| Scientific methodology | Yes | Cite relevant paper |
| FairDM feature description | No | Self-documented |
| Django/Python functionality | No | Link to official docs |
| UI instructions | No | Screenshots sufficient |

Use the `citation-management` skill to search for and validate citations when making claims about scientific standards, FAIR principles, or research data management practices.
