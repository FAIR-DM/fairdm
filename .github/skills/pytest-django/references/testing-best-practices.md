# Testing Best Practices

Django testing guidelines and best practices for writing effective tests with pytest-django.

## Table of Contents

- [Test Organization](#test-organization)
- [Test Naming Conventions](#test-naming-conventions)
- [Test Structure](#test-structure)
- [Database Testing](#database-testing)
- [Performance Optimization](#performance-optimization)
- [Common Pitfalls](#common-pitfalls)
- [Testing Different Components](#testing-different-components)

## Test Organization

### Directory Structure

Mirror your source code structure in tests:

```
myproject/
├── myapp/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── admin.py
└── tests/
    └── myapp/
        ├── __init__.py
        ├── test_models.py
        ├── test_views.py
        ├── test_forms.py
        └── test_admin.py
```

### Grouping Tests

Group related tests using classes (but avoid unittest.TestCase):

```python
# Good: Logical grouping without inheritance
class TestUserModel:
    """Tests for User model."""

    @pytest.mark.django_db
    def test_create_user(self):
        user = User.objects.create_user(username='test', password='pass')
        assert user.username == 'test'

    @pytest.mark.django_db
    def test_user_str(self):
        user = User.objects.create_user(username='test')
        assert str(user) == 'test'

class TestUserProfile:
    """Tests for User profile functionality."""

    @pytest.mark.django_db
    def test_profile_created(self):
        user = User.objects.create_user(username='test')
        assert hasattr(user, 'profile')
```

### Shared Fixtures via conftest.py

```python
# tests/conftest.py
import pytest

@pytest.fixture
def user(db):
    """Standard user fixture available to all tests."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

# tests/myapp/conftest.py
import pytest

@pytest.fixture
def article(db, user):
    """Article fixture for myapp tests."""
    from myapp.models import Article
    return Article.objects.create(
        title='Test Article',
        content='Content',
        author=user
    )
```

## Test Naming Conventions

### Function Names

Use descriptive names that explain what is being tested:

```python
# Good: Clear intent
def test_user_can_create_post_when_authenticated()
def test_invalid_email_raises_validation_error()
def test_deleted_article_returns_404()

# Bad: Vague
def test_post()
def test_email()
def test_article()
```

### Test Class Names

```python
# Good: Describes what's being tested
class TestUserAuthentication:
    ...

class TestArticlePermissions:
    ...

class TestCommentModeration:
    ...

# Bad: Too generic
class TestUser:
    ...

class TestViews:
    ...
```

## Test Structure

### AAA Pattern (Arrange, Act, Assert)

```python
@pytest.mark.django_db
def test_article_publication(user):
    # Arrange: Set up test data
    article = Article.objects.create(
        title='Test Article',
        content='Content',
        author=user,
        status='draft'
    )

    # Act: Perform the action being tested
    article.publish()

    # Assert: Verify the expected outcome
    assert article.status == 'published'
    assert article.published_date is not None
```

### Single Assertion Principle

Prefer one logical assertion per test:

```python
# Good: Single logical concept
@pytest.mark.django_db
def test_user_creation_sets_username():
    user = User.objects.create_user(username='test')
    assert user.username == 'test'

@pytest.mark.django_db
def test_user_creation_sets_date_joined():
    user = User.objects.create_user(username='test')
    assert user.date_joined is not None

# Acceptable: Multiple assertions for same concept
@pytest.mark.django_db
def test_user_full_name_property():
    user = User.objects.create_user(
        username='test',
        first_name='John',
        last_name='Doe'
    )
    assert user.get_full_name() == 'John Doe'
    assert 'John' in user.get_full_name()
    assert 'Doe' in user.get_full_name()
```

### Parametrized Tests

Use parametrization for testing multiple inputs:

```python
@pytest.mark.django_db
@pytest.mark.parametrize('username,email,is_valid', [
    ('validuser', 'valid@example.com', True),
    ('', 'valid@example.com', False),
    ('validuser', 'invalid-email', False),
    ('ab', 'valid@example.com', False),  # Too short
])
def test_user_validation(username, email, is_valid):
    user = User(username=username, email=email)

    if is_valid:
        user.full_clean()  # Should not raise
    else:
        with pytest.raises(ValidationError):
            user.full_clean()
```

## Database Testing

### Minimize Database Access

Only use database when necessary:

```python
# Good: No database needed for pure logic
def test_format_phone_number():
    assert format_phone_number('1234567890') == '(123) 456-7890'

# Good: Database needed for ORM operations
@pytest.mark.django_db
def test_user_creation():
    user = User.objects.create_user(username='test')
    assert user.pk is not None
```

### Use Transactions Appropriately

```python
# Standard test: Fast, transactional rollback
@pytest.mark.django_db
def test_create_article():
    article = Article.objects.create(title='Test')
    assert Article.objects.count() == 1

# Transaction test: For testing transaction behavior
@pytest.mark.django_db(transaction=True)
def test_transaction_rollback():
    from django.db import transaction

    try:
        with transaction.atomic():
            Article.objects.create(title='Test')
            raise Exception('Rollback')
    except Exception:
        pass

    assert Article.objects.count() == 0
```

### Test Isolation

Ensure tests don't interfere with each other:

```python
# Good: Each test creates its own data
@pytest.mark.django_db
def test_article_count():
    Article.objects.create(title='Article 1')
    assert Article.objects.count() == 1

@pytest.mark.django_db
def test_article_deletion():
    article = Article.objects.create(title='Article 2')
    article.delete()
    assert Article.objects.count() == 0

# Bad: Tests depend on execution order
@pytest.mark.django_db
def test_create_first_article():
    Article.objects.create(title='Article 1')
    assert Article.objects.count() == 1

@pytest.mark.django_db
def test_create_second_article():
    Article.objects.create(title='Article 2')
    assert Article.objects.count() == 2  # Fails if run alone!
```

## Performance Optimization

### Query Count Assertions

Guard against N+1 query problems:

```python
@pytest.mark.django_db
def test_article_list_queries(client, django_assert_num_queries):
    # Create test data
    user = User.objects.create_user(username='author')
    for i in range(10):
        Article.objects.create(
            title=f'Article {i}',
            author=user
        )

    # Should not increase with number of articles
    with django_assert_num_queries(3):  # 1 session, 1 user, 1 articles query
        response = client.get('/articles/')

@pytest.mark.django_db
def test_optimized_query():
    """Test that prefetch_related is used correctly."""
    user = User.objects.create_user(username='test')

    # Create articles with comments
    for i in range(5):
        article = Article.objects.create(title=f'Article {i}', author=user)
        for j in range(3):
            Comment.objects.create(article=article, text=f'Comment {j}')

    # Without optimization: 1 + 5 queries (N+1 problem)
    # With prefetch_related: 2 queries total
    with django_assert_num_queries(2):
        articles = Article.objects.prefetch_related('comments').all()
        for article in articles:
            list(article.comments.all())
```

### Use select_related and prefetch_related

```python
@pytest.mark.django_db
def test_query_optimization():
    """Verify ORM optimization techniques."""
    user = User.objects.create_user(username='test')
    Article.objects.create(title='Test', author=user)

    # Bad: N+1 queries
    with django_assert_num_queries(2):  # 1 for articles, 1 for each author
        articles = Article.objects.all()
        authors = [article.author.username for article in articles]

    # Good: Single join query
    with django_assert_num_queries(1):
        articles = Article.objects.select_related('author').all()
        authors = [article.author.username for article in articles]
```

### Database Reuse

```bash
# First run: Creates database
pytest

# Subsequent runs: Reuse database (faster)
pytest --reuse-db

# Force recreation
pytest --create-db
```

### Parallel Execution

```bash
# Run tests in parallel
pytest -n auto

# Specific number of workers
pytest -n 4
```

## Common Pitfalls

### Pitfall 1: Missing @pytest.mark.django_db

```python
# Wrong: Will fail with "Database access not allowed"
def test_user_count():
    assert User.objects.count() == 0

# Correct
@pytest.mark.django_db
def test_user_count():
    assert User.objects.count() == 0
```

### Pitfall 2: Forgetting to Save Model Changes

```python
# Wrong: Changes not persisted
@pytest.mark.django_db
def test_user_update():
    user = User.objects.create_user(username='test')
    user.email = 'new@example.com'  # Not saved!

    fresh_user = User.objects.get(pk=user.pk)
    assert fresh_user.email == 'new@example.com'  # Fails!

# Correct
@pytest.mark.django_db
def test_user_update():
    user = User.objects.create_user(username='test')
    user.email = 'new@example.com'
    user.save()  # Persist changes

    fresh_user = User.objects.get(pk=user.pk)
    assert fresh_user.email == 'new@example.com'
```

### Pitfall 3: Testing Implementation Instead of Behavior

```python
# Bad: Tests implementation detail (view function name)
def test_home_view_function_name():
    from myapp.views import home
    assert home.__name__ == 'home'

# Good: Tests behavior (what the view does)
def test_home_view_returns_200(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'Welcome' in response.content.decode()
```

### Pitfall 4: Over-Mocking

```python
# Bad: Over-mocking loses confidence
def test_user_service(mocker):
    mocker.patch('myapp.models.User.objects.create_user')
    mocker.patch('myapp.models.User.save')
    mocker.patch('myapp.services.send_welcome_email')
    # Test becomes meaningless

# Good: Test real integration
@pytest.mark.django_db
def test_user_service(mailoutbox):
    from myapp.services import create_user_account
    user = create_user_account('test', 'test@example.com')

    assert User.objects.filter(username='test').exists()
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ['test@example.com']
```

## Testing Different Components

### Models

```python
@pytest.mark.django_db
def test_article_str_representation():
    article = Article.objects.create(title='Test Article')
    assert str(article) == 'Test Article'

@pytest.mark.django_db
def test_article_get_absolute_url():
    article = Article.objects.create(
        title='Test Article',
        slug='test-article'
    )
    assert article.get_absolute_url() == '/articles/test-article/'

@pytest.mark.django_db
def test_article_published_manager():
    Article.objects.create(title='Draft', status='draft')
    Article.objects.create(title='Published', status='published')

    assert Article.published.count() == 1
    assert Article.objects.count() == 2
```

### Views

```python
def test_article_list_view(client):
    response = client.get('/articles/')
    assert response.status_code == 200
    assert 'articles' in response.context

def test_article_detail_view(client, article):
    response = client.get(f'/articles/{article.slug}/')
    assert response.status_code == 200
    assert response.context['article'] == article

def test_article_create_requires_login(client):
    response = client.get('/articles/new/')
    assert response.status_code == 302  # Redirect to login

def test_article_create_authenticated(authenticated_client):
    response = authenticated_client.post('/articles/new/', {
        'title': 'New Article',
        'content': 'Content',
    })
    assert response.status_code == 302  # Redirect after success
    assert Article.objects.filter(title='New Article').exists()
```

### Forms

```python
def test_article_form_valid_data():
    form = ArticleForm(data={
        'title': 'Test Article',
        'content': 'Test content',
    })
    assert form.is_valid()

def test_article_form_missing_title():
    form = ArticleForm(data={
        'content': 'Test content',
    })
    assert not form.is_valid()
    assert 'title' in form.errors

@pytest.mark.django_db
def test_article_form_save():
    form = ArticleForm(data={
        'title': 'Test Article',
        'content': 'Test content',
    })
    assert form.is_valid()
    article = form.save()
    assert article.pk is not None
    assert article.title == 'Test Article'
```

### Admin

```python
def test_article_admin_list(admin_client):
    response = admin_client.get('/admin/myapp/article/')
    assert response.status_code == 200

@pytest.mark.django_db
def test_article_admin_search(admin_client):
    Article.objects.create(title='Searchable Article')
    response = admin_client.get('/admin/myapp/article/?q=Searchable')
    assert response.status_code == 200
    assert 'Searchable Article' in response.content.decode()

@pytest.mark.django_db
def test_article_admin_create(admin_client, user):
    response = admin_client.post('/admin/myapp/article/add/', {
        'title': 'Admin Article',
        'content': 'Content',
        'author': user.pk,
        'status': 'published',
    })
    assert Article.objects.filter(title='Admin Article').exists()
```

### Signals

```python
@pytest.mark.django_db
def test_profile_created_signal():
    """Test that profile is created automatically for new users."""
    user = User.objects.create_user(username='test')
    assert hasattr(user, 'profile')
    assert user.profile.user == user

@pytest.mark.django_db
def test_post_save_signal(mailoutbox):
    """Test that email is sent on article publication."""
    article = Article.objects.create(
        title='Test',
        status='draft'
    )

    # No email for draft
    assert len(mailoutbox) == 0

    # Email sent on publish
    article.status = 'published'
    article.save()

    assert len(mailoutbox) == 1
```

### Management Commands

```python
from django.core.management import call_command
from io import StringIO

@pytest.mark.django_db
def test_cleanup_command():
    """Test custom management command."""
    # Create old data
    old_article = Article.objects.create(
        title='Old',
        created=timezone.now() - timezone.timedelta(days=400)
    )
    new_article = Article.objects.create(
        title='New',
        created=timezone.now()
    )

    # Run command
    out = StringIO()
    call_command('cleanup_old_articles', days=365, stdout=out)

    # Verify results
    assert not Article.objects.filter(pk=old_article.pk).exists()
    assert Article.objects.filter(pk=new_article.pk).exists()
    assert 'Deleted 1 article' in out.getvalue()
```

### Middleware

```python
def test_custom_middleware(rf):
    """Test custom middleware."""
    from myapp.middleware import CustomMiddleware

    request = rf.get('/')

    # Create middleware
    middleware = CustomMiddleware(lambda req: HttpResponse('OK'))

    # Process request
    response = middleware(request)

    # Verify middleware behavior
    assert hasattr(request, 'custom_attribute')
    assert response.status_code == 200
```

## Summary

**Key Principles:**

1. **Test behavior, not implementation**
2. **Keep tests independent and isolated**
3. **Use descriptive test names**
4. **Follow AAA pattern (Arrange, Act, Assert)**
5. **Minimize database access**
6. **Guard against query performance issues**
7. **Use appropriate fixtures and scopes**
8. **Parametrize similar tests**
9. **Avoid over-mocking**
10. **Write tests that document expected behavior**
