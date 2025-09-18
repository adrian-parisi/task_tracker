# Task Tracker

A comprehensive task management system built with Django REST Framework, React, and Celery for AI-powered task management.

## Features

### Core Functionality
- **Task Management**: Create, read, update, and delete tasks with full CRUD operations
- **Project Organization**: Tasks are organized under projects with unique task keys
- **User Management**: Authentication and user roles (developers, project managers)
- **Activity Tracking**: Complete audit trail of task changes and activities
- **Smart Tagging**: JSON-based tag system for flexible task categorization

### AI-Powered Features
- **Smart Estimate**: AI-powered task estimation based on similar tasks
- **Smart Rewrite**: AI-enhanced task descriptions with user story format
- **Smart Summary**: Asynchronous AI-generated task summaries with real-time updates via Server-Sent Events

### Technical Features
- **RESTful API**: Complete REST API with Django REST Framework
- **Real-time Updates**: Server-Sent Events for asynchronous operations
- **Comprehensive Testing**: Full test suite with pytest
- **API Documentation**: Auto-generated OpenAPI documentation with drf-spectacular
- **Database Optimization**: Indexed queries and efficient data structures

## Architecture

### Backend (Django)
- **Django 4.2**: Web framework
- **Django REST Framework**: API framework
- **Celery**: Asynchronous task processing (file-based broker)
- **SQLite**: Database (development)
- **drf-spectacular**: API documentation

### Frontend (React)
- **React 18**: User interface
- **TypeScript**: Type safety
- **Axios**: HTTP client
- **Server-Sent Events**: Real-time updates

### AI Services
- **Mocked AI Service**: Development and testing
- **Real AI Service**: Production-ready AI integration
- **Factory Pattern**: Easy service switching

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 16+

### 1. Backend Setup

```bash
# Clone the repository
git clone <repository-url>
cd task_tracker

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

The backend will be available at `http://localhost:8000`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

The frontend will be available at `http://localhost:3000`

### 3. Celery Setup (for AI features)

```bash
# Create Celery broker directory (if it doesn't exist)
mkdir -p /tmp/celery_broker

# In a new terminal, start Celery worker
cd task_tracker
source venv/bin/activate
celery -A task_tracker worker --loglevel=info

# In another terminal, start Celery beat (for periodic tasks)
celery -A task_tracker beat --loglevel=info
```

## API Documentation

Once the backend is running, you can access the API documentation at:
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

## Testing

### Run All Tests
```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests with pytest
DJANGO_SETTINGS_MODULE=task_tracker.settings python -m pytest --nomigrations

# Run with coverage
DJANGO_SETTINGS_MODULE=task_tracker.settings python -m pytest --nomigrations --cov=.
```

### Run Specific Test Suites
```bash
# Backend tests only
DJANGO_SETTINGS_MODULE=task_tracker.settings python -m pytest tasks/ ai_tools/ --nomigrations

# Frontend tests only
cd frontend
npm test
```

## Project Structure

```
task_tracker/
├── accounts/                 # User management
├── ai_tools/                # AI-powered features
│   ├── services/            # AI service implementations
│   ├── views/               # AI endpoint views
│   └── tasks.py             # Celery tasks
├── common/                  # Shared utilities
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API services
│   │   └── types/           # TypeScript types
│   └── package.json
├── tasks/                   # Core task management
│   ├── models/              # Database models
│   ├── views/               # API views
│   └── tests/               # Test suites
├── task_tracker/            # Django project settings
├── manage.py
├── requirements.txt
└── README.md
```

## Key Models

### Task
- **Project**: Belongs to a project (required)
- **Title**: Task title (3-200 characters)
- **Description**: Detailed task description
- **Status**: TODO, IN_PROGRESS, BLOCKED, DONE
- **Estimate**: Story points (0-100)
- **Assignee**: Assigned user
- **Reporter**: User who created the task
- **Tags**: JSON array of tag names
- **Key**: Auto-generated unique key (e.g., "TST-1")

### Project
- **Code**: Short project code (e.g., "TST")
- **Name**: Project name
- **Description**: Project description
- **Owner**: Project owner
- **Is Active**: Active status

### TaskActivity
- **Task**: Related task
- **Type**: Activity type (CREATED, UPDATED_STATUS, etc.)
- **Actor**: User who performed the action
- **Field**: Field that was changed
- **Before/After**: Values before and after change

## AI Features

### Smart Estimate
- **Endpoint**: `POST /api/ai-tools/tasks/{task_id}/smart-estimate/`
- **Type**: Synchronous
- **Returns**: Suggested points, confidence score, rationale

### Smart Rewrite
- **Endpoint**: `POST /api/ai-tools/tasks/{task_id}/smart-rewrite/`
- **Type**: Synchronous
- **Returns**: Enhanced title and user story format

### Smart Summary
- **Endpoint**: `POST /api/ai-tools/tasks/{task_id}/smart-summary/`
- **Type**: Asynchronous
- **Returns**: Operation ID and SSE URL
- **Updates**: Real-time progress via Server-Sent Events

## Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Celery (file-based broker for development)
CELERY_BROKER_URL=filesystem://
CELERY_BROKER_TRANSPORT_OPTIONS={"data_folder_in": "/tmp/celery_broker", "data_folder_out": "/tmp/celery_broker"}
CELERY_RESULT_BACKEND=django-db

# AI Services
AI_SERVICE_TYPE=mock_ai  # or 'ai' for production
```

## Development

### Adding New Features
1. Create models in appropriate app
2. Add API views with proper serializers
3. Write comprehensive tests
4. Update API documentation
5. Add frontend components if needed

### Code Style
- **Python**: Follow PEP 8
- **JavaScript/TypeScript**: Use Prettier and ESLint
- **Tests**: Aim for 90%+ coverage
- **Documentation**: Update README for new features

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure production database
- [ ] Set up production Celery broker (Redis/RabbitMQ)
- [ ] Configure static file serving
- [ ] Set up logging
- [ ] Configure CORS for frontend
- [ ] Set up monitoring


## Troubleshooting

### Common Issues

1. **Database Migration Errors**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Celery Connection Issues**
   - Ensure `/tmp/celery_broker` directory exists
   - Check CELERY_BROKER_URL in settings
   - Verify file permissions for the broker directory

3. **Frontend Build Issues**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **Test Failures**
   ```bash
   # Use --nomigrations flag for test database issues
   python -m pytest --nomigrations
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
