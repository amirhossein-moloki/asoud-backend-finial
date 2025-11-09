# ASOUD Web Services

A comprehensive Django-based e-commerce platform with advanced features including affiliate marketing, multi-vendor support, chat system, and SMS integration.

## Table of Contents

- [Features](#features)
- [Directory Structure](#directory-structure)
- [Configuration](#configuration)
- [Installation](#installation)
- [Development](#development)
- [Testing](#testing)
- [API Documentation](#api-documentation)
- [Production Deployment](#production-deployment)
- [Contributing](#contributing)

## Features

- **Multi-vendor marketplace** with separate owner and marketer interfaces
- **Product management** with categories, keywords, and themes
- **Advanced pricing** with colleague and marketer pricing tiers
- **Affiliate system** with referral tracking
- **Shopping cart and order management**
- **Real-time chat system** between users
- **SMS integration** with bulk and template messaging
- **Discount and promotion system**
- **Payment gateway integration**
- **Notification system**
- **User wallet and credit system**
- **Geographic region support**
- **Product reservation system**

## Project Directory Structure
```bash
.
├── .env                          # Environment variables
├── .gitignore                   # Git ignore rules
├── Dockerfile                   # Docker container configuration
├── README.md                    # Project documentation
├── requirements.txt             # Python dependencies
├── manage.py                    # Django management script
├── entrypoint.sh               # Docker entrypoint script
├── config/                     # Django project configuration
│   ├── __init__.py
│   ├── asgi.py                 # ASGI configuration
│   ├── settings/               # Environment-specific settings
│   │   ├── __init__.py
│   │   ├── base.py            # Base settings
│   │   ├── development.py     # Development settings
│   │   └── production.py      # Production settings
│   └── urls.py                # Main URL configuration
├── apps/                      # Django applications
│   ├── base/                  # Base models and utilities
│   ├── users/                 # User management
│   ├── product/               # Product catalog
│   ├── cart/                  # Shopping cart and orders
│   ├── chat/                  # Real-time messaging
│   ├── sms/                   # SMS integration
│   ├── payment/               # Payment processing
│   ├── affiliate/             # Affiliate marketing
│   ├── discount/              # Discount system
│   ├── notification/          # Notification system
│   ├── wallet/                # User wallet system
│   └── ...                    # Other feature modules
├── templates/                 # HTML templates
├── static/                    # Static files (CSS, JS, images)
├── media/                     # User uploaded files
├── locale/                    # Internationalization files
├── logs/                      # Application logs
├── data/                      # Configuration files
│   └── nginx/                 # Nginx configurations
├── docker-compose.dev.yaml    # Development Docker Compose
├── docker-compose.prod.yaml   # Production Docker Compose
└── utils/                     # Utility functions
```

## Configuration
Before running the project, make sure to set these environment variables either in a `.env` file (for local development) or through your server's environment configuration.

### Django Project Configuration
- **DJANGO_SECRET_KEY**: The Django project's secret key used for cryptographic signing
- **DJANGO_DEBUG**: Set to False in production
- **DJANGO_ALLOWED_HOSTS**: Comma-separated list of allowed hosts

### Database Configuration
- **DATABASE_NAME**: The name of the PostgreSQL database
- **DATABASE_USERNAME**: The username to access the database
- **DATABASE_PASSWORD**: The password for the database user
- **DATABASE_HOST**: The host address of the database server (default: db)
- **DATABASE_PORT**: The port number for the database server (default: 5432)

### Redis Configuration
- **REDIS_HOST**: Redis server host (default: redis)
- **REDIS_PORT**: Redis server port (default: 6379)
- **REDIS_PASSWORD**: Redis server password

### Email Configuration
- **EMAIL_HOST**: SMTP server host
- **EMAIL_PORT**: SMTP server port
- **EMAIL_HOST_USER**: SMTP username
- **EMAIL_HOST_PASSWORD**: SMTP password
- **EMAIL_USE_TLS**: Enable TLS encryption

### SMS Configuration
- **SMS_API**: SMS service API key
- **SMS_TEMPLATE_ID**: Default SMS template ID

### Security Configuration
- **CSRF_TRUSTED_ORIGINS**: Comma-separated list of trusted origins
- **SECURE_SSL_REDIRECT**: Enable SSL redirect in production

## Installation

### Prerequisites
- Docker and Docker Compose
- Git

### Steps

1. **Clone the repository:**
    ```bash
    git clone https://github.com/jam4li/asoud.git
    cd asoud/
    ```

2. **Create environment file:**
    ```bash
    cp .env.example .env
    # Edit .env with your configuration
    ```

3. **For development:**
    ```bash
    docker-compose -f docker-compose.dev.yaml build
    docker-compose -f docker-compose.dev.yaml up -d
    ```

4. **For production:**
    ```bash
    docker-compose -f docker-compose.prod.yaml build
    docker-compose -f docker-compose.prod.yaml up -d
    ```

5. **Run migrations:**
    ```bash
    docker-compose exec web python manage.py migrate
    ```

6. **Create superuser:**
    ```bash
    docker-compose exec web python manage.py createsuperuser
    ```

7. **Collect static files (production):**
    ```bash
    docker-compose exec web python manage.py collectstatic --noinput
    ```

## Development

### Running the Development Server
```bash
# Start all services
docker-compose -f docker-compose.dev.yaml up

# Start in background
docker-compose -f docker-compose.dev.yaml up -d

# View logs
docker-compose logs -f web
```

### Making Migrations
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### Managing Dependencies
```bash
# Add new package to requirements.txt then rebuild
docker-compose build web
```

### Code Quality
```bash
# Install development tools
pip install flake8 black isort

# Format code
black .

# Sort imports
isort .

# Check code style
flake8 .
```

## Testing

### Running Tests
```bash
# Run all tests
docker-compose exec web python manage.py test

# Run specific app tests
docker-compose exec web python manage.py test apps.item

# Run with coverage
docker-compose exec web coverage run --source='.' manage.py test
docker-compose exec web coverage report
```

### Test Structure
- Unit tests for models: `apps/*/tests/test_models.py`
- API tests: `apps/*/tests/test_views.py`
- Integration tests: `apps/*/tests/test_integration.py`

## API Documentation

### Accessing API Documentation
- **Postman Collection**: Import `Asoud API Document-v1.8.postman_collection (2).json`
- **Interactive API Browser**: Visit `/api/` when running the development server
- **OpenAPI Schema**: Available at `/api/schema/`

### Authentication
Most endpoints require authentication. Use JWT tokens:
```bash
# Login to get token
POST /api/auth/login/
{
    "username": "your_username",
    "password": "your_password"
}

# Use token in subsequent requests
Authorization: Bearer <your_token>
```

### Main API Endpoints
- **Authentication**: `/api/auth/`
- **Products**: `/api/products/`
- **Orders**: `/api/orders/`
- **Cart**: `/api/cart/`
- **Chat**: `/api/chat/`
- **SMS**: `/api/sms/`
- **Payments**: `/api/payments/`

## Production Deployment

### Security Checklist
- [ ] Set `DEBUG = False`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Use strong `SECRET_KEY`
- [ ] Enable HTTPS redirects
- [ ] Configure CSRF protection
- [ ] Set secure cookie settings
- [ ] Use non-root user in containers
- [ ] Regular security updates

### Monitoring
- **Application logs**: `/asoud/logs/`
- **Grafana dashboard**: Configure with provided credentials
- **Database monitoring**: Use built-in PostgreSQL tools

### Backup Strategy
```bash
# Database backup
docker-compose exec db pg_dump -U $DATABASE_USERNAME $DATABASE_NAME > backup.sql

# Media files backup
docker-compose exec web tar -czf media_backup.tar.gz /asoud/media/
```

## Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests: `docker-compose exec web python manage.py test`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

### Code Standards
- Follow PEP 8 style guide
- Write docstrings for all functions and classes
- Add tests for new features
- Update documentation as needed

### Issue Reporting
Please use GitHub Issues to report bugs or request features. Include:
- Detailed description
- Steps to reproduce
- Expected vs actual behavior
- Environment details

## License

This project is proprietary software. All rights reserved.

## Support

For support and questions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation in `/docs/`