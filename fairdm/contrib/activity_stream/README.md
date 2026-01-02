# Activity Stream App

This Django app provides activity tracking functionality for FairDM using `django-activity-stream`.

## Features

- **Activity Tracking**: Automatically tracks create/update/delete actions on FairDM objects
- **Activity Plugin**: Displays recent activity for Projects, Datasets, Samples, and Measurements
- **Follow/Unfollow**: Allows users to follow objects and receive notifications
- **Activity Feeds**: Provides activity feed views for users and objects

## Installation

The app is automatically included in the FairDM framework. It's configured in `INSTALLED_APPS` as:

```python
INSTALLED_APPS = [
    # ...
    "fairdm.contrib.activity_stream",
    "actstream",  # django-activity-stream dependency
    # ...
]
```

## Usage

### Creating Activities

Use the `create_activity` helper function to track actions:

```python
from fairdm.contrib.activity_stream.utils import create_activity

# Track a creation
create_activity(
    actor=request.user,
    verb="created",
    target=my_project,
    description=f"Created a new project: {my_project.title}"
)

# Track an update with related object
create_activity(
    actor=request.user,
    verb="updated",
    target=my_dataset,
    action_object=my_sample,
    description="Added sample to dataset"
)
```

### Follow/Unfollow

Allow users to follow objects:

```python
from fairdm.contrib.activity_stream.utils import follow, unfollow, is_following

# Follow an object
follow(user, project)

# Check if following
if is_following(user, project):
    # User is following the project
    pass

# Unfollow
unfollow(user, project)
```

### Get Object Activities

Retrieve activities for an object:

```python
from fairdm.contrib.activity_stream.utils import get_object_activities

# Get all activities for an object
activities = get_object_activities(my_project)

# Get limited activities
recent_activities = get_object_activities(my_project, limit=5)
```

### Activity Plugin

The `ActivityPlugin` can be used in any model's plugin configuration:

```python
from fairdm.contrib.activity_stream.plugins import ActivityPlugin

class Activity(ActivityPlugin):
    """Display recent activity for this object."""
    pass
```

This is already configured for all core FairDM models (Project, Dataset, Sample, Measurement).

## Templates

### Main Activity Template

Located at `activity_stream/activity_stream.html`, this template displays a list of activities.

### Activity Item Component

The Cotton component `c-activity.item` renders individual activity items with:
- Color-coded borders (green for created, blue for updated, red for deleted)
- Actor avatar
- Activity description
- Timestamp
- Action type icon

Usage in templates:
```django
{% load cotton %}
<c-activity.item :activity="activity" />
```

## Configuration

Settings are defined in `fairdm/contrib/activity_stream/conf.py`:

```python
ACTSTREAM_SETTINGS = {
    "USE_JSONFIELD": True,
}
```

## URL Configuration

The app includes django-activity-stream's built-in URLs at `/activity/`:

- `/activity/` - Activity feed views
- `/activity/follow/` - Follow/unfollow endpoints
- `/activity/user/<username>/` - User activity feed
- etc.

## Registered Models

The following models are automatically registered with actstream on app ready:

- `Project`
- `Dataset`
- `Sample`
- `Measurement`
- `Person` (from contributors app)
- `Organization` (from contributors app)
- `Point` (from location app)

Additional models can be registered in their respective app's `ready()` method.

## Plugin Registration

The app automatically registers the `ActivityPlugin` for all core FairDM models when it loads. This happens in the `ActivityStreamConfig.ready()` method, so the core models don't need to know about this app.

The registered plugins provide an "Activity" tab in the detail view of:
- Projects
- Datasets
- Samples
- Measurements

No action is required from developers using FairDM - the activity tracking is automatically available once the app is in `INSTALLED_APPS`.

## API

Import functions and classes using their full module paths:

```python
from fairdm.contrib.activity_stream.plugins import ActivityPlugin
from fairdm.contrib.activity_stream.utils import (
    create_activity,
    follow,
    unfollow,
    is_following,
    get_object_activities,
)
```

## Integration with FairDM Views

The FairDM create views automatically log creation activities:

```python
class FairDMCreateView(CreateView):
    def form_valid(self, form):
        response = super().form_valid(form)
        create_activity(
            self.request.user,
            verb="created",
            target=self.object,
            description=f"Created a new {self.object._meta.verbose_name}: {self.object}"
        )
        return response
```

## Migration Notes

This app consolidates all activity-stream related code that was previously scattered across:
- `fairdm.core.plugins` (ActivityPlugin)
- `fairdm.views` (create_activity calls)
- `fairdm.utils.views` (follow/unfollow functions)
- Various app `ready()` methods (actstream registration)
- Settings files (ACTSTREAM_SETTINGS)
