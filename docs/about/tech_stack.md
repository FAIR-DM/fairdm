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

## Traefik Reverse Proxy and Load Balancer

For incoming traffic management, FairDM uses Traefik, a modern reverse proxy and load balancer. Traefik automatically routes HTTP and HTTPS requests to the appropriate service containers. Its seamless integration with Docker Compose allows configuration through simple labels, which lowers the barrier for administrators unfamiliar with complex network setups. Traefik also handles SSL certificate provisioning and renewal through Let’s Encrypt, ensuring secure communication by default.

## Automated Backup and Persistence

Data durability is crucial for research portals. FairDM includes automated database backup capabilities to regularly save PostgreSQL data snapshots. However, these backups require configuration with an external storage service, allowing flexibility depending on institutional policies and infrastructure.

## Monitoring and Logging

While FairDM does not yet provide built-in comprehensive monitoring, it supports integration with popular third-party tools such as Sentry for error tracking and alerting. For task monitoring, it includes Flower, a web interface that tracks Celery workers and job status, enabling administrators to supervise background task health.

## Deployment Environment and Management

FairDM is optimized for single-server deployment, striking a balance between capability and simplicity. Docker Compose orchestrates all the core services, encapsulating the entire stack into manageable containers. To facilitate easy server management, detailed documentation is provided for using tools like Portainer CE, which offers a graphical interface for container and volume management, ideal for users with limited command-line experience.

## Configuration via Environment Variables

All deployment-specific settings, including database credentials, domain names, and feature toggles, are managed through environment variables. This approach promotes clean separation between code and configuration, simplifies customization across different deployments, and supports secure handling of sensitive information.