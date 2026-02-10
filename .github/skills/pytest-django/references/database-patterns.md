# Database Patterns

Advanced database configuration and setup strategies for pytest-django.

## Table of Contents

- [Session-Scoped Database Setup](#session-scoped-database-setup)
- [External Database Testing](#external-database-testing)
- [Template Databases](#template-databases)
- [Database Reuse Strategies](#database-reuse-strategies)
- [Multi-Database Testing](#multi-database-testing)
- [Custom Database Backends](#custom-database-backends)

## Session-Scoped Database Setup

### Loading Fixtures Once

Load Django fixtures at the start of the test session:

```python
import pytest
from django.core.management import call_command

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Load test fixtures once per session."""
    with django_db_blocker.unblock():
        call_command('loaddata', 'users.json')
        call_command('loaddata', 'test_data.json')
```

### Creating Initial Data

Create test data programmatically:

```python
@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Create initial test data."""
    with django_db_blocker.unblock():
        from myapp.models import Organization, User

        # Create organizations
        org = Organization.objects.create(name='Test Org')

        # Create users
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
```

### Function-Scoped Access to Session Data

Access session-scoped data in function-scoped fixtures:

```python
@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        Organization.objects.create(name='Global Org', id=1)

@pytest.fixture
def test_organization(django_db_blocker):
    """Get the session-scoped organization."""
    with django_db_blocker.unblock():
        return Organization.objects.get(id=1)

def test_org_exists(test_organization):
    assert test_organization.name == 'Global Org'
```

## External Database Testing

### Using Pre-Populated Database

Skip test database creation and use an existing database:

```python
@pytest.fixture(scope='session')
def django_db_setup():
    """Configure Django to use existing database."""
    from django.conf import settings

    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'testdb.example.com',
        'NAME': 'existing_test_db',
        'USER': 'testuser',
        'PASSWORD': 'testpass',
        'PORT': '5432',
    }
```

### Read-Only External Database

Test against a read-only external database:

```python
@pytest.fixture(scope='session')
def django_db_setup():
    """Configure read-only database connection."""
    from django.conf import settings

    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'readonly-replica.example.com',
        'NAME': 'production_replica',
        'USER': 'readonly_user',
        'PASSWORD': 'readonly_pass',
        'OPTIONS': {
            'options': '-c default_transaction_read_only=on'
        }
    }
```

## Template Databases

### PostgreSQL Template Database

Create test database from a pre-populated template:

```python
import pytest
from django.db import connections
import psycopg

def run_sql(sql):
    """Execute SQL on postgres default database."""
    with psycopg.connect(database='postgres') as conn:
        conn.autocommit = True
        conn.execute(sql)

@pytest.fixture(scope='session')
def django_db_setup():
    """Create test database from template."""
    from django.conf import settings

    test_db_name = 'test_db_from_template'
    template_name = 'source_template_db'

    settings.DATABASES['default']['NAME'] = test_db_name

    # Drop existing test database if it exists
    run_sql(f'DROP DATABASE IF EXISTS {test_db_name}')

    # Create test database from template
    run_sql(f'CREATE DATABASE {test_db_name} TEMPLATE {template_name}')

    yield

    # Cleanup: close all connections and drop test database
    for connection in connections.all():
        connection.close()

    run_sql(f'DROP DATABASE {test_db_name}')
```

### Creating Template Database

Script to create a reusable template database:

```python
# scripts/create_template_db.py
import psycopg
from django.core.management import call_command
from django.conf import settings

def create_template_database():
    """Create a template database with migrations and fixtures."""
    template_name = 'source_template_db'

    conn = psycopg.connect(database='postgres')
    conn.autocommit = True

    # Drop and recreate template
    conn.execute(f'DROP DATABASE IF EXISTS {template_name}')
    conn.execute(f'CREATE DATABASE {template_name}')
    conn.close()

    # Point Django to template database
    settings.DATABASES['default']['NAME'] = template_name

    # Run migrations
    call_command('migrate', '--noinput')

    # Load fixtures
    call_command('loaddata', 'initial_data.json')

    print(f"Template database '{template_name}' created successfully")

if __name__ == '__main__':
    create_template_database()
```

## Database Reuse Strategies

### Always Reuse Database

Configure pytest to reuse database by default:

```ini
# pytest.ini
[pytest]
addopts = --reuse-db
```

### Conditional Database Creation

Create database only when schema changes:

```python
# conftest.py
import os
import pytest

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup):
    """Track schema version and recreate only when changed."""
    schema_version_file = '.test_db_version'
    current_version = get_migration_version()  # Your implementation

    if os.path.exists(schema_version_file):
        with open(schema_version_file, 'r') as f:
            saved_version = f.read()

        if saved_version != current_version:
            # Schema changed, recreate database
            pytest.main(['--create-db'])

    # Save current version
    with open(schema_version_file, 'w') as f:
        f.write(current_version)
```

### Parallel Testing with xdist

**Default behavior** (separate databases):

```bash
pytest -n 4  # Creates test_db_gw0, test_db_gw1, test_db_gw2, test_db_gw3
```

**Shared database** (when safe):

```python
@pytest.fixture(scope='session')
def django_db_modify_db_settings():
    """Disable database separation for xdist workers."""
    pass  # Empty fixture
```

⚠️ **Warning**: Only use shared database when:

- Tests don't modify data (read-only)
- Using `transaction=True` for full isolation
- You understand the risks of test interference

**Custom database naming**:

```python
@pytest.fixture(scope='session')
def django_db_modify_db_settings(django_db_modify_db_settings):
    """Custom database naming for xdist workers."""
    from django.conf import settings
    from xdist import get_xdist_worker_id

    worker_id = get_xdist_worker_id()
    if worker_id != 'master':
        db_name = f'custom_test_db_{worker_id}'
        settings.DATABASES['default']['NAME'] = db_name
```

## Multi-Database Testing

### Testing with Multiple Databases

```python
@pytest.fixture(scope='session')
def django_db_setup():
    """Configure multiple test databases."""
    from django.conf import settings

    settings.DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'test_main_db',
        },
        'analytics': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'test_analytics_db',
        },
        'cache': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'test_cache_db',
        }
    }

@pytest.mark.django_db(databases=['default', 'analytics'])
def test_cross_database_query():
    """Test queries across multiple databases."""
    from myapp.models import User
    from analytics.models import UserActivity

    user = User.objects.create(username='test')
    UserActivity.objects.using('analytics').create(user_id=user.id)

    assert UserActivity.objects.using('analytics').filter(user_id=user.id).exists()
```

### Database Routing in Tests

```python
# Test with custom database router
@pytest.mark.django_db(databases='__all__')
def test_database_routing():
    """Test automatic database routing."""
    from myapp.models import User
    from analytics.models import Event

    # Router automatically sends to correct database
    user = User.objects.create(username='test')  # → default
    event = Event.objects.create(type='login')   # → analytics

    assert User.objects.using('default').filter(username='test').exists()
    assert Event.objects.using('analytics').filter(type='login').exists()
```

## Custom Database Backends

### SQLite In-Memory for Speed

```python
@pytest.fixture(scope='session')
def django_db_setup():
    """Use SQLite in-memory for faster tests."""
    from django.conf import settings

    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
```

### PostgreSQL with Custom Options

```python
@pytest.fixture(scope='session')
def django_db_setup():
    """Configure PostgreSQL with performance options."""
    from django.conf import settings

    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_db',
        'OPTIONS': {
            'options': '-c synchronous_commit=off',  # Faster commits
            'connect_timeout': 10,
        },
        'TEST': {
            'TEMPLATE': 'template0',  # Use clean template
            'CHARSET': 'UTF8',
        }
    }
```

### MySQL with Transaction Isolation

```python
@pytest.fixture(scope='session')
def django_db_setup():
    """Configure MySQL with specific isolation level."""
    from django.conf import settings

    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'test_db',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'isolation_level': 'read committed',
        },
        'TEST': {
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_unicode_ci',
        }
    }
```

## Database Fixtures Best Practices

1. **Session scope for expensive setup**: Use `scope='session'` for one-time database configuration
2. **Function scope for test data**: Create test-specific data in function-scoped fixtures
3. **Use django_db_blocker**: Always wrap database operations in fixtures with `django_db_blocker.unblock()`
4. **Cleanup after session**: Close connections and drop temporary databases in teardown
5. **Document assumptions**: Clearly document what each fixture provides and its scope
6. **Avoid fixture interdependencies**: Keep fixtures independent when possible
7. **Test fixture setup**: Verify that fixtures create expected state

Example of well-structured fixtures:

```python
@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """One-time database setup with global test data."""
    with django_db_blocker.unblock():
        # Create data that all tests can read
        Category.objects.create(name='Global Category', id=999)

@pytest.fixture
def test_user(db):
    """Create a test user for individual test."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def authenticated_client(client, test_user):
    """Provide authenticated test client."""
    client.force_login(test_user)
    return client

def test_profile_page(authenticated_client):
    """Test requires authenticated client."""
    response = authenticated_client.get('/profile/')
    assert response.status_code == 200
```
