# Before you start

This guide is mainly for experienced Django developers that may wish to contribute to the development of the core FairDM framework. If you are looking for information on how to develop a FairDM-powered web application for your research community, please see the [Developer Guide](#developer-guide).

## Design Philosophy

1. Python > HTML > CSS > JavaScript

2. Fat Models, Thin Views

3. Reusability

4. Testing

5. Mobile Second

6. Accessibility

7. Internationalisation

8. Documentation

10. Security

11. Tutorials

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