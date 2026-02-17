# Contract: Permission Checking

## `Plugin.has_permission(request, obj=None)`

### Signature
```python
def has_permission(self, request: HttpRequest, obj: Model | None = None) -> bool
```

### Preconditions
- `request.user` must be available (Django auth middleware active)
- `obj` may be `None` if only model-level checking is needed

### Algorithm

```
IF plugin.permission is None:
    RETURN True  (no permission required)

# Step 1: Model-level check (Django auth)
IF NOT request.user.has_perm(plugin.permission):
    RETURN False

# Step 2: Object-level check (django-guardian)
IF obj is not None:
    IF NOT request.user.has_perm(plugin.permission, obj):
        RETURN False

RETURN True
```

### Postconditions
- Returns `True` if the user may access this plugin for the given object
- Returns `False` if either model-level OR object-level check fails
- When `permission` is `None`, always returns `True` (public plugin)

---

## `Plugin.dispatch()` — Permission Gate

### Signature
```python
def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse
```

### Algorithm

```
1. Fetch object via self.get_object()
2. IF NOT self.has_permission(request, object):
     RAISE PermissionDenied  (returns 403)
3. ELSE:
     RETURN super().dispatch(request, *args, **kwargs)
```

### Error Response
- **403 Forbidden**: User authenticated but lacks permission
- Uses Django's standard `PermissionDenied` exception handling (can be customized via `handler403`)

---

## PluginGroup Permission Layering

### Two-Tier Check

```
Group-Level Check (PluginGroup.permission)
  │
  ├── FAIL → All wrapped plugins inaccessible, tab hidden
  │
  └── PASS → Individual Plugin Permission Check
               │
               ├── FAIL → This specific plugin returns 403
               │
               └── PASS → Plugin view executes normally
```

### Tab Visibility
- Group's `has_permission()` controls tab visibility
- Individual plugin permissions only gate direct URL access
- This means: if a user can see the tab (group permission passes), they click through to the default plugin. If that specific plugin has additional permission requirements, those are checked at dispatch time.

### Implementation

```python
class PluginGroup:
    permission = None
    
    @classmethod
    def has_permission(cls, request, obj=None):
        if cls.permission is None:
            return True
        if not request.user.has_perm(cls.permission):
            return False
        if obj is not None and not request.user.has_perm(cls.permission, obj):
            return False
        return True
```

---

## Permission String Format

### Convention
```
"{app_label}.{action}_{model_name}"
```

### Examples
| Permission String | Meaning |
|-------------------|---------|
| `"myapp.view_sample"` | Can view sample instances |
| `"myapp.change_sample"` | Can edit sample instances |
| `"myapp.delete_sample"` | Can delete sample instances |
| `"myapp.manage_sample"` | Custom permission for admin operations |

### Object-Level Permissions (django-guardian)
The same permission strings are used for both model-level and object-level checks. django-guardian stores object-level grants in its `UserObjectPermission` and `GroupObjectPermission` tables.

---

## Superuser Behavior

- Django superusers (`user.is_superuser = True`) bypass all permission checks automatically
- `has_perm()` returns `True` for superusers regardless of assigned permissions
- This is standard Django behavior and not overridden by the plugin system

---

## Anonymous User Behavior

- Anonymous users fail all permission checks (unless the specific permission is assigned to the anonymous user via django-guardian)
- Plugins with `permission = None` are accessible to anonymous users
- Tab rendering for anonymous users only shows public (permission-free) plugins
