# Fixture Recipes

Common pytest-django fixture patterns and practical examples.

## Table of Contents

- [User Fixtures](#user-fixtures)
- [Client Fixtures](#client-fixtures)
- [Model Factory Fixtures](#model-factory-fixtures)
- [Settings Fixtures](#settings-fixtures)
- [Email Testing Fixtures](#email-testing-fixtures)
- [File Upload Fixtures](#file-upload-fixtures)
- [Cache Fixtures](#cache-fixtures)
- [Request Fixtures](#request-fixtures)

## User Fixtures

### Basic User Creation

```python
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def user(db):
    """Create a standard test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )

@pytest.fixture
def admin_user(db):
    """Create an admin/superuser."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )

@pytest.fixture
def staff_user(db):
    """Create a staff user."""
    return User.objects.create_user(
        username='staff',
        email='staff@example.com',
        password='staff123',
        is_staff=True
    )
```

### Users with Permissions

```python
@pytest.fixture
def user_with_permissions(db):
    """Create user with specific permissions."""
    from django.contrib.auth.models import Permission

    user = User.objects.create_user(
        username='permitted',
        password='pass123'
    )

    # Add specific permissions
    perms = Permission.objects.filter(
        codename__in=['add_article', 'change_article', 'view_article']
    )
    user.user_permissions.set(perms)

    return user

@pytest.fixture
def editor_user(db):
    """Create user with editor group."""
    from django.contrib.auth.models import Group

    user = User.objects.create_user(username='editor', password='pass123')
    editor_group, _ = Group.objects.get_or_create(name='Editors')
    user.groups.add(editor_group)

    return user
```

### User Fixtures with Relationships

```python
@pytest.fixture
def user_with_profile(db):
    """Create user with related profile."""
    user = User.objects.create_user(
        username='profileuser',
        password='pass123'
    )
    Profile.objects.create(
        user=user,
        bio='Test bio',
        location='Test City',
        birth_date='1990-01-01'
    )
    return user

@pytest.fixture
def user_with_posts(db):
    """Create user with blog posts."""
    user = User.objects.create_user(username='blogger', password='pass123')

    for i in range(3):
        Post.objects.create(
            author=user,
            title=f'Test Post {i}',
            content=f'Content for post {i}'
        )

    return user
```

## Client Fixtures

### Custom Authenticated Clients

```python
@pytest.fixture
def authenticated_client(client, user):
    """Client authenticated as standard user."""
    client.force_login(user)
    return client

@pytest.fixture
def api_client(client):
    """Client configured for API testing."""
    client.defaults['HTTP_ACCEPT'] = 'application/json'
    client.defaults['CONTENT_TYPE'] = 'application/json'
    return client

@pytest.fixture
def token_client(client, user):
    """Client with JWT authentication token."""
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(user)
    client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {refresh.access_token}'
    return client
```

### Clients with Custom Headers

```python
@pytest.fixture
def ajax_client(client):
    """Client configured for AJAX requests."""
    client.defaults['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
    return client

@pytest.fixture
def mobile_client(client):
    """Client simulating mobile browser."""
    client.defaults['HTTP_USER_AGENT'] = (
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) '
        'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
    )
    return client

@pytest.fixture
def cors_client(client):
    """Client with CORS headers."""
    client.defaults['HTTP_ORIGIN'] = 'http://example.com'
    return client
```

### Session Management Fixtures

```python
@pytest.fixture
def client_with_session(client):
    """Client with pre-configured session data."""
    session = client.session
    session['cart_items'] = ['item1', 'item2']
    session['user_preferences'] = {'theme': 'dark'}
    session.save()
    return client

@pytest.fixture
def client_with_cookies(client):
    """Client with predefined cookies."""
    client.cookies['tracking_id'] = 'test_tracking_123'
    client.cookies['consent'] = 'accepted'
    return client
```

## Model Factory Fixtures

### Basic Model Factories

```python
@pytest.fixture
def article_factory(db):
    """Factory for creating articles."""
    def create_article(**kwargs):
        defaults = {
            'title': 'Test Article',
            'content': 'Test content',
            'status': 'published'
        }
        defaults.update(kwargs)
        return Article.objects.create(**defaults)
    return create_article

@pytest.fixture
def category_factory(db):
    """Factory for creating categories."""
    counter = 0
    def create_category(**kwargs):
        nonlocal counter
        counter += 1
        defaults = {
            'name': f'Category {counter}',
            'slug': f'category-{counter}'
        }
        defaults.update(kwargs)
        return Category.objects.create(**defaults)
    return create_category
```

### Factories with Relationships

```python
@pytest.fixture
def comment_factory(db, user):
    """Factory for creating comments."""
    def create_comment(article=None, **kwargs):
        if article is None:
            article = Article.objects.create(title='Test', content='Content')

        defaults = {
            'article': article,
            'author': user,
            'text': 'Test comment'
        }
        defaults.update(kwargs)
        return Comment.objects.create(**defaults)
    return create_comment

@pytest.fixture
def blog_post_with_comments(db, user):
    """Create blog post with comments."""
    post = Post.objects.create(
        title='Test Post',
        content='Content',
        author=user
    )

    # Create comments
    for i in range(3):
        Comment.objects.create(
            post=post,
            author=user,
            text=f'Comment {i}'
        )

    return post
```

### Batch Creation Fixtures

```python
@pytest.fixture
def multiple_users(db):
    """Create multiple test users."""
    users = []
    for i in range(5):
        user = User.objects.create_user(
            username=f'user{i}',
            email=f'user{i}@example.com',
            password='pass123'
        )
        users.append(user)
    return users

@pytest.fixture
def articles_dataset(db, user):
    """Create dataset of articles for testing pagination/filtering."""
    articles = []
    categories = ['Tech', 'Science', 'Sports']

    for i in range(20):
        article = Article.objects.create(
            title=f'Article {i}',
            content=f'Content {i}',
            author=user,
            category=categories[i % 3],
            published_date=timezone.now() - timezone.timedelta(days=i)
        )
        articles.append(article)

    return articles
```

## Settings Fixtures

### Temporary Settings Changes

```python
@pytest.fixture
def debug_mode(settings):
    """Enable DEBUG mode for test."""
    settings.DEBUG = True
    return settings

@pytest.fixture
def test_email_backend(settings):
    """Use test email backend."""
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    return settings

@pytest.fixture
def test_storage(settings, tmp_path):
    """Use temporary file storage."""
    settings.MEDIA_ROOT = tmp_path / 'media'
    settings.MEDIA_URL = '/media/'
    return settings
```

### Multi-Setting Fixtures

```python
@pytest.fixture
def production_like_settings(settings):
    """Configure settings to mimic production."""
    settings.DEBUG = False
    settings.ALLOWED_HOSTS = ['testserver', 'localhost']
    settings.SECURE_SSL_REDIRECT = True
    settings.SESSION_COOKIE_SECURE = True
    settings.CSRF_COOKIE_SECURE = True
    return settings

@pytest.fixture
def caching_enabled(settings):
    """Enable caching with dummy cache."""
    settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'test-cache',
        }
    }
    return settings
```

## Email Testing Fixtures

### Email Verification Fixtures

```python
@pytest.fixture
def sent_email(mailoutbox, user):
    """Send a test email and return mailoutbox."""
    from django.core.mail import send_mail

    send_mail(
        'Test Subject',
        'Test message body',
        'from@example.com',
        [user.email],
        fail_silently=False,
    )

    return mailoutbox

@pytest.fixture
def email_verifier():
    """Helper for verifying email contents."""
    def verify(mail, subject=None, body_contains=None, to=None):
        if subject:
            assert mail.subject == subject
        if body_contains:
            assert body_contains in mail.body
        if to:
            assert to in mail.to
        return True
    return verify
```

### Email Templates

```python
@pytest.fixture
def templated_email(mailoutbox, user):
    """Send HTML email from template."""
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string

    context = {'user': user, 'action_url': 'http://example.com/verify'}

    subject = 'Verify Your Email'
    text_content = render_to_string('email/verify.txt', context)
    html_content = render_to_string('email/verify.html', context)

    msg = EmailMultiAlternatives(subject, text_content, 'from@example.com', [user.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    return mailoutbox[0]
```

## File Upload Fixtures

### File Upload Helpers

```python
import io
from django.core.files.uploadedfile import SimpleUploadedFile, InMemoryUploadedFile
from PIL import Image

@pytest.fixture
def text_file():
    """Create simple text file for upload."""
    return SimpleUploadedFile(
        "test.txt",
        b"Test file content",
        content_type="text/plain"
    )

@pytest.fixture
def csv_file():
    """Create CSV file for upload."""
    csv_content = b"name,email\nJohn,john@example.com\nJane,jane@example.com"
    return SimpleUploadedFile(
        "data.csv",
        csv_content,
        content_type="text/csv"
    )

@pytest.fixture
def image_file():
    """Create test image file."""
    # Create a simple image
    image = Image.new('RGB', (100, 100), color='red')
    img_io = io.BytesIO()
    image.save(img_io, format='PNG')
    img_io.seek(0)

    return InMemoryUploadedFile(
        img_io,
        field_name='image',
        name='test.png',
        content_type='image/png',
        size=len(img_io.getvalue()),
        charset=None
    )

@pytest.fixture
def pdf_file():
    """Create mock PDF file."""
    return SimpleUploadedFile(
        "document.pdf",
        b"%PDF-1.4 mock pdf content",
        content_type="application/pdf"
    )
```

### Complex File Fixtures

```python
@pytest.fixture
def uploaded_document(db, user, pdf_file):
    """Create document with uploaded file."""
    return Document.objects.create(
        title='Test Document',
        file=pdf_file,
        uploaded_by=user
    )

@pytest.fixture
def user_avatar(db, user, image_file):
    """Create user with avatar."""
    profile = user.profile
    profile.avatar = image_file
    profile.save()
    return profile
```

## Cache Fixtures

### Cache Management

```python
@pytest.fixture
def cache(settings):
    """Provide cache instance and clear after test."""
    from django.core.cache import cache

    # Clear cache before test
    cache.clear()

    yield cache

    # Clear cache after test
    cache.clear()

@pytest.fixture
def cached_data(cache):
    """Populate cache with test data."""
    cache.set('test_key', 'test_value', 300)
    cache.set('user:1', {'name': 'Test User'}, 300)
    return cache

@pytest.fixture
def redis_cache(settings):
    """Configure Redis cache for testing."""
    settings.CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/15',  # Test database
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
    from django.core.cache import cache
    cache.clear()
    yield cache
    cache.clear()
```

## Request Fixtures

### RequestFactory Patterns

```python
@pytest.fixture
def rf():
    """RequestFactory instance."""
    from django.test import RequestFactory
    return RequestFactory()

@pytest.fixture
def get_request(rf):
    """Simple GET request."""
    return rf.get('/')

@pytest.fixture
def post_request(rf):
    """POST request with data."""
    return rf.post('/', {'key': 'value'})

@pytest.fixture
def authenticated_request(rf, user):
    """Request with authenticated user."""
    request = rf.get('/')
    request.user = user
    return request

@pytest.fixture
def request_with_session(rf):
    """Request with session middleware."""
    from django.contrib.sessions.middleware import SessionMiddleware

    request = rf.get('/')

    # Add session
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()

    return request

@pytest.fixture
def ajax_request(rf):
    """AJAX request."""
    return rf.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
```

### Request with Middleware

```python
@pytest.fixture
def request_with_messages(rf, user):
    """Request with messages framework."""
    from django.contrib.messages.middleware import MessageMiddleware
    from django.contrib.sessions.middleware import SessionMiddleware
    from django.contrib.messages import get_messages

    request = rf.get('/')
    request.user = user

    # Add session
    session_middleware = SessionMiddleware(lambda req: None)
    session_middleware.process_request(request)
    request.session.save()

    # Add messages
    messages_middleware = MessageMiddleware(lambda req: None)
    messages_middleware.process_request(request)

    return request
```

## Composite Fixtures

### Complete Test Environment

```python
@pytest.fixture
def full_test_environment(
    db,
    user,
    authenticated_client,
    settings,
    mailoutbox,
    tmp_path
):
    """Complete testing environment with all essentials."""
    # Configure settings
    settings.DEBUG = True
    settings.MEDIA_ROOT = tmp_path / 'media'

    # Create sample data
    Category.objects.create(name='Test Category')

    return {
        'user': user,
        'client': authenticated_client,
        'settings': settings,
        'mailoutbox': mailoutbox,
        'media_root': settings.MEDIA_ROOT,
    }

def test_with_full_environment(full_test_environment):
    """Use comprehensive test fixture."""
    env = full_test_environment

    response = env['client'].get('/dashboard/')
    assert response.status_code == 200
    assert env['user'].is_authenticated
```

## Fixture Best Practices

1. **Name fixtures clearly**: Use descriptive names that indicate what they provide
2. **Document fixtures**: Add docstrings explaining purpose and what's returned
3. **Use appropriate scopes**: Function scope is default; use session/module when appropriate
4. **Compose fixtures**: Build complex fixtures from simpler ones
5. **Clean up resources**: Use yield for teardown logic when needed
6. **Avoid fixture pollution**: Each test should get fresh fixtures
7. **Parametrize when appropriate**: Use `@pytest.fixture(params=[...])` for variations
8. **Return useful objects**: Return the most useful object (not just None after creation)

```python
# Good: Clear, composable, well-documented
@pytest.fixture
def published_article(db, user):
    """Create a published article with author.

    Returns:
        Article: Published article instance
    """
    return Article.objects.create(
        title='Test Article',
        content='Content',
        author=user,
        status='published'
    )

# Bad: Unclear, side-effects only
@pytest.fixture
def setup_article(db, user):
    Article.objects.create(title='Test', content='Content', author=user)
    # Returns None - less useful
```
