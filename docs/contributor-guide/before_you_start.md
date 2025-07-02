# Before you start

This guide is mainly for experienced Django developers that may wish to contribute to the development of the core FairDM framework. If you are looking for information on how to develop a FairDM-powered web application for your research community, please see the [Developer Guide](#developer-guide).

## Philosophy

**Simplicity** - FairDM strives to be simple, straight-forward and easy-to-use for both portal users and portal developers.

**Consistency** - FairDM promotes "convention over configuration" and emphasizes consistency over flexibility. Portal developers should not have to worry about implementation details, but rather focus on build a data schema that reflects the needs of their research community.

**Batteries Included** - FairDM provides a robust set of built-in functionalities that are common to all research data portals. All mission-critical external services are predefined and provided to portal developers ready-to-go.

**Isolation** - FairDM portals are designed to be self-hosted and self-contained, allowing researchers to maintain full control over their data and portal infrastructure.

**Integration** - FairDM should not try to reinvent the wheel. It should, where possible, integrate with existing, well-defined and widely accepted tools and services from the research data management ecosystem. Integrations should never compromise the [FairDM vision](#vision).

**Interoperability** - FairDM portals should be completely interoperable with other FairDM portals. FairDM should, through use of common export formats, strive to be interoperable with external systems.


<!-- ## Design Philosophy

1. Python > HTML > CSS > JavaScript

2. Fat Models, Thin Views

3. Reusability

4. Testing

5. Mobile Second

6. Accessibility

7. Internationalisation

8. Documentation

10. Security

11. Tutorials -->

## Repository Structure

    fairdm/                    # Project directory
    │
    ├── api/                       # Management script for running commands
    ├── conf/                      # Project package directory
    │   ├── backends/            # Django settings for the project
    │   ├── settings/            # Django settings for the project
    │   ├── local.py                # URL declarations for the project
    │   └── production.py                # WSGI config for deployment
    ├── contrib/                  # Application directory
    │   ├── admin/               # Admin configurations
    │   ├── contributors/                # Application configurations
    │   ├── core/              # Database models
    │   ├── datasets/               # Test cases
    │   ├── organizations/                # URL declarations for the app
    │   └── projects/               # View functions
    │   └── reviews/               # View functions
    │   └── samples/               # View functions
    │   └── users/               # View functions
    │
    └── templates/                  # Directory for HTML templates
        └── app_name/              # Directory for app-specific templates
            └── base.html          # Base template file