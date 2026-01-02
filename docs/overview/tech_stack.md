# Technology Stack

FairDM is built on a reliable and widely adopted open-source infrastructure designed for ease of deployment and management, particularly suited to research groups with limited IT resources.

## Django

At the heart of FairDM is Django, a mature Python web framework renowned for its scalability, security, and clean design. Django powers the entire application, managing both backend logic and rendering user-facing pages. Its general popularity ensures that developers and researchers find it approachable and well-documented.

## PostgreSQL Database with Optional PostGIS Extension

FairDM uses PostgreSQL as its primary relational database system. PostgreSQL is an industry-leading open-source database known for its robustness, advanced querying capabilities, and strong community support. To support research projects involving geospatial data, FairDM optionally includes the PostGIS extension, which adds powerful geographic object support. This enables efficient storage and querying of sample location data or other spatial metadata.

## Redis In-Memory Data Store

To improve application performance and manage asynchronous tasks, FairDM leverages Redis, an in-memory data structure store. Redis serves two critical functions: caching frequently accessed data to reduce load times and acting as a message broker that queues background jobs, ensuring smooth and responsive user interactions.

## Celery Task Queue

FairDM relies on Celery, a distributed task queue system, to manage background processing. Celery handles tasks such as sending notification emails, processing uploaded datasets, and other long-running operations asynchronously, keeping the main application responsive and efficient. Paired with Redis as a broker, Celery allows the system to scale background tasks independently of user requests.

## Reverse proxy and TLS termination (deployment choice)

In production deployments, FairDM is typically placed behind a reverse proxy / ingress layer that handles routing and (optionally) TLS termination. Many setups use tools like Traefik or Nginx, but the exact choice depends on your hosting environment and operational preferences.

## Backup and persistence (recommended)

Data durability is crucial for research portals. FairDM expects deployments to include a backup strategy for databases and uploaded files (frequency, retention, and off-site storage are deployment concerns). The exact mechanism depends on institutional policies and infrastructure.

## Monitoring and logging

FairDM can be integrated with third-party tools such as Sentry for error tracking and alerting. If you use Celery, tools like Flower can be used to monitor workers and task health.

## Deployment environment and management

FairDM is optimized for single-server deployment, striking a balance between capability and simplicity. Docker Compose can orchestrate core services and encapsulate the stack into manageable containers. Many teams also use tools like Portainer CE for graphical container and volume management.

## Configuration via Environment Variables

All deployment-specific settings, including database credentials, domain names, and feature toggles, are managed through environment variables. This approach promotes clean separation between code and configuration, simplifies customization across different deployments, and supports secure handling of sensitive information.