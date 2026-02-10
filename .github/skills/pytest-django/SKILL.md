---
name: pytest-django
description: >-
  Expert guide for testing Django applications with pytest-django. Use when writing or debugging
  Django tests, configuring test databases, working with Django fixtures, testing models/views/forms,
  managing database access in tests, handling transactions, using Django test client, testing with
  live servers, or configuring pytest for Django projects. Covers database fixtures (db, transactional_db,
  django_db_setup), Django-specific fixtures (client, admin_client, rf, settings, live_server,
  django_user_model, mailoutbox), markers (@pytest.mark.django_db), configuration (pytest.ini,
  pyproject.toml, conftest.py), test isolation, database reuse strategies, and Django assertion
  helpers. Use when setting up new Django test suites or troubleshooting Django-specific test issues.
---

# pytest-django

pytest-django is a pytest plugin that provides fixtures and markers for testing Django applications. It seamlessly integrates pytest's powerful testing capabilities with Django's ORM, test client, and other framework features.

## Quick Start

### Configuration

Choose one configuration method:

**pytest.ini**:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = yourproject.settings
python_files = tests.py test_*.py *_tests.py
```

**pyproject.toml**:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "yourproject.settings"
python_files = ["test_*.py", "*_test.py"]
```

**conftest.py** (programmatic):

```python
from django.conf import settings

def pytest_configure():
    settings.configure(
        DATABASES={...},
        INSTALLED_APPS=[...],
    )
```

### Basic Test

```python
import pytest
from myapp.models import User

@pytest.mark.django_db
def test_user_creation():
    user = User.objects.create(username='testuser')
    assert user.username == 'testuser'
```

## Core Concepts

### Database Access

**By default, tests have NO database access**. This is intentional to keep tests fast and isolated. Enable database access explicitly:

**Method 1: Mark individual tests**

```python
@pytest.mark.django_db
def test_my_model():
    MyModel.objects.create(name='test')
```

**Method 2: Use the `db` fixture**

```python
def test_with_db(db):
    MyModel.objects.create(name='test')
```

**Method 3: Enable for all tests** (use sparingly)

```python
# conftest.py
@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass
```

### Transactional vs Non-Transactional

**Standard database access** (`@pytest.mark.django_db`):

- Creates a transaction per test
- Rolls back at test end
- Fast, isolated
- Cannot test transaction-related code

**Transactional access** (`@pytest.mark.django_db(transaction=True)`):

- Flushes database between tests
- Slower but necessary for testing transactions, async code, or Celery tasks
- Required when code uses `transaction.atomic()`, `commit()`, `rollback()`

```python
@pytest.mark.django_db(transaction=True)
def test_transaction_behavior():
    # Test code that uses transactions
    pass
```

## Essential Fixtures

### Database Fixtures

**`db`** — Basic database access (transactional)

```python
def test_user(db):
    User.objects.create_user(username='test', password='pass')
```

**`transactional_db`** — Transactional database access

```python
def test_with_commit(transactional_db):
    # Can use transaction.atomic(), commit(), rollback()
    pass
```

**`django_db_setup`** — Customize test database setup

```python
@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        # Load fixtures
        call_command('loaddata', 'initial_data.json')
        # Create test data
        User.objects.create(username='admin')
```

**`django_db_blocker`** — Control database access in fixtures

```python
@pytest.fixture
def custom_setup(django_db_blocker):
    with django_db_blocker.unblock():
        # Database operations here
        Widget.objects.create(name='test')
```

### Django Test Client Fixtures

**`client`** — Unauthenticated Django test client

```python
def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
```

**`admin_client`** — Authenticated as superuser

```python
def test_admin_view(admin_client):
    response = admin_client.get('/admin/')
    assert response.status_code == 200
```

**`rf`** — RequestFactory for creating request objects

```python
def test_view_directly(rf):
    request = rf.get('/my-view/')
    response = my_view(request)
    assert response.status_code == 200
```

### Django Settings Fixture

**`settings`** — Temporarily modify Django settings

```python
def test_with_timezone(settings):
    settings.USE_TZ = True
    settings.TIME_ZONE = 'UTC'
    # Settings automatically revert after test
```

### User Model Fixture

**`django_user_model`** — Get configured User model

```python
def test_custom_user(django_user_model):
    user = django_user_model.objects.create_user(
        username='someone',
        password='something'
    )
    assert user.is_authenticated
```

### Live Server Fixture

**`live_server`** — Run Django development server for tests

```python
def test_with_selenium(live_server):
    from selenium import webdriver
    browser = webdriver.Firefox()
    browser.get(live_server.url)
    # Functional testing with real server
```

### Email Fixture

**`mailoutbox`** — Capture sent emails

```python
def test_email_sending(mailoutbox):
    from django.core.mail import send_mail
    send_mail('Subject', 'Body', 'from@example.com', ['to@example.com'])
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == 'Subject'
```

## Advanced Patterns

### Custom Database Setup

**Load fixtures at session start**:

```python
@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('loaddata', 'test_data.json')
```

**Use existing external database**:

```python
@pytest.fixture(scope='session')
def django_db_setup():
    from django.conf import settings
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'testdb.example.com',
        'NAME': 'external_test_db',
    }
```

**Create from template database** (PostgreSQL):

```python
@pytest.fixture(scope='session')
def django_db_setup():
    from django.conf import settings
    from django.db import connections
    import psycopg

    settings.DATABASES['default']['NAME'] = 'test_db_copy'

    with psycopg.connect(database='postgres') as conn:
        conn.execute('DROP DATABASE IF EXISTS test_db_copy')
        conn.execute('CREATE DATABASE test_db_copy TEMPLATE source_db')

    yield

    for connection in connections.all():
        connection.close()

    with psycopg.connect(database='postgres') as conn:
        conn.execute('DROP DATABASE test_db_copy')
```

### Database Reuse

Speed up test runs by reusing the test database:

**Command line**:

```bash
pytest --reuse-db  # Keep database between runs
pytest --create-db # Force recreation
```

**Configuration** (pytest.ini):

```ini
[pytest]
addopts = --reuse-db
```

### xdist (Parallel Testing)

**Default behavior**: Each worker gets its own database (`test_db_gw0`, `test_db_gw1`, etc.)

**Share database across workers** (when safe):

```python
@pytest.fixture(scope='session')
def django_db_modify_db_settings():
    pass  # Empty fixture = disable database separation
```

⚠️ Only use when tests don't rely on transactional isolation.

### Template Variable Validation

**Enable strict template variable checking**:

```ini
# pytest.ini
[pytest]
FAIL_INVALID_TEMPLATE_VARS = True
```

**Disable for specific tests**:

```python
@pytest.mark.ignore_template_errors
def test_with_invalid_vars(client):
    client.get('/page-with-undefined-vars/')
```

## Django Assertion Helpers

Import Django's test assertions for use in pytest:

```python
from pytest_django.asserts import (
    assertTemplateUsed,
    assertTemplateNotUsed,
    assertContains,
    assertNotContains,
    assertFormError,
    assertFormsetError,
    assertRedirects,
    assertQuerysetEqual,
    assertNumQueries,
    assertJSONEqual,
    assertJSONNotEqual,
    assertXMLEqual,
    assertXMLNotEqual,
    assertInHTML,
)

def test_template_used(client):
    response = client.get('/page/')
    assertTemplateUsed(response, 'base.html')

def test_query_count(django_assert_num_queries):
    with django_assert_num_queries(3):
        list(MyModel.objects.all())
        # Fails if query count != 3
```

## Common Patterns

### Testing Models

```python
@pytest.mark.django_db
def test_model_creation():
    obj = MyModel.objects.create(name='test')
    assert obj.pk is not None
    assert str(obj) == 'test'

@pytest.mark.django_db
def test_model_validation():
    obj = MyModel(name='')
    with pytest.raises(ValidationError):
        obj.full_clean()
```

### Testing Views

```python
def test_view_get(client):
    response = client.get('/my-view/')
    assert response.status_code == 200
    assert 'expected_text' in response.content.decode()

def test_view_post(client):
    response = client.post('/my-view/', {'field': 'value'})
    assert response.status_code == 302  # Redirect
    assert MyModel.objects.filter(field='value').exists()
```

### Testing Forms

```python
def test_form_valid():
    form = MyForm(data={'name': 'test', 'email': 'test@example.com'})
    assert form.is_valid()

def test_form_invalid():
    form = MyForm(data={'name': ''})
    assert not form.is_valid()
    assert 'name' in form.errors
```

### Testing Admin

```python
def test_admin_list_view(admin_client):
    response = admin_client.get('/admin/myapp/mymodel/')
    assert response.status_code == 200

@pytest.mark.django_db
def test_admin_create(admin_client):
    response = admin_client.post('/admin/myapp/mymodel/add/', {
        'name': 'test',
        'description': 'test description',
    })
    assert MyModel.objects.filter(name='test').exists()
```

### Testing Management Commands

```python
from django.core.management import call_command
from io import StringIO

@pytest.mark.django_db
def test_command():
    out = StringIO()
    call_command('mycommand', stdout=out)
    assert 'Expected output' in out.getvalue()
```

### Parametrized Tests

```python
@pytest.mark.django_db
@pytest.mark.parametrize('username,expected', [
    ('valid_user', True),
    ('', False),
    ('user@example', False),
])
def test_username_validation(username, expected):
    user = User(username=username)
    is_valid = user.full_clean() is None
    assert is_valid == expected
```

## Performance Tips

1. **Minimize database access**: Use `@pytest.mark.django_db` only when necessary
2. **Use session-scoped fixtures**: For expensive setup shared across tests
3. **Reuse test database**: Add `--reuse-db` to speed up repeated runs
4. **Parallel execution**: Use `pytest-xdist` for parallel test execution
5. **Prefer factory functions over fixtures**: For test data that varies per test
6. **Avoid transactional tests**: Unless testing transaction-specific behavior
7. **Query count assertions**: Guard against N+1 queries early

```python
# Good: Query count assertion
@pytest.mark.django_db
def test_list_view_queries(client, django_assert_max_num_queries):
    with django_assert_max_num_queries(10):
        response = client.get('/items/')
```

## Troubleshooting

**"Database access not allowed"**: Add `@pytest.mark.django_db` or use `db` fixture

**Tests interfere with each other**: Ensure proper test isolation or use `transaction=True`

**Fixtures not found**: Check `DJANGO_SETTINGS_MODULE` configuration

**Slow tests**: Profile with `pytest --durations=10` and optimize database-heavy tests

**Import errors**: Ensure Django is properly configured before imports

## Further Reading

For detailed database configuration, advanced fixture patterns, and integration with testing tools, see:

- [references/database-patterns.md](references/database-patterns.md) — Advanced database setup strategies
- [references/fixture-recipes.md](references/fixture-recipes.md) — Common fixture patterns and examples
- [references/testing-best-practices.md](references/testing-best-practices.md) — Django testing guidelines
