
# Project Structure

This document explains the organization and architecture of the DocMan_MCP project.

## Directory Structure

```
DocMan_MCP/
├── __pycache__/                    # Python bytecode cache
├── config/                         # Configuration files
│   ├── __init__.py
│   ├── __pycache__/
│   └── db.py                       # Database configuration
├── docs/                           # Documentation
│   ├── api.md                      # API reference
│   ├── changelog.md                # Version history
│   ├── index.md                    # Main documentation
│   ├── setup.md                    # Setup instructions
│   ├── structure.md                # This file
│   └── usage.md                    # Usage guide
├── src/                            # Source code
│   ├── models/                     # Data models
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── db_models.py            # SQLAlchemy models
│   │   └── schemas.py              # Pydantic schemas
│   ├── routers/                    # API route handlers
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── documents_router.py     # Document endpoints
│   │   ├── project_router.py       # Project endpoints
│   │   ├── summary_router.py       # Summary endpoints
│   │   └── user_router.py          # User endpoints
│   ├── services/                   # Business logic
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── pdf_parser.py           # PDF processing
│   │   └── summary_service.py      # Summary generation
│   ├── uploads/                    # File upload directory
│   ├── utils/                      # Utility functions
│   │   ├── __pycache__/
│   │   ├── .env                    # Environment variables
│   │   └── Summary_agent.py        # AI summary agent
│   ├── openapi.json                # OpenAPI specification
│   ├── README.md                   # Source code readme
│   └── requirements.txt            # Python dependencies
├── .gitignore                      # Git ignore rules
├── main.py                         # Application entry point
└── mkdocs.yml                      # Documentation configuration
```

## Architecture Overview

### Layered Architecture

The project follows a layered architecture pattern:

1. **Presentation Layer** (`routers/`)
   - API endpoints and request/response handling
   - Input validation and serialization
   - HTTP status code management

2. **Business Logic Layer** (`services/`)
   - Core business logic and rules
   - Data processing and transformation
   - Integration with external services

3. **Data Access Layer** (`models/`)
   - Database models and schemas
   - Data validation and serialization
   - ORM configurations

4. **Infrastructure Layer** (`config/`, `utils/`)
   - Database connections
   - Environment configuration
   - Utility functions

### Component Responsibilities

#### Configuration (`config/`)

**`db.py`**
- Database connection setup
- SQLAlchemy engine configuration
- Session management
- Database URL configuration

#### Models (`src/models/`)

**`db_models.py`**
- SQLAlchemy ORM models
- Database table definitions
- Relationships between entities
- Database constraints

**`schemas.py`**
- Pydantic models for API serialization
- Request/response validation
- Data transformation schemas
- Type definitions

#### Routers (`src/routers/`)

**`documents_router.py`**
- Document CRUD operations
- File upload handling
- Document listing and filtering
- Document deletion

**`project_router.py`**
- Project management endpoints
- Project CRUD operations
- Project-document associations
- Project metadata handling

**`summary_router.py`**
- Summary generation endpoints
- Document summarization
- Project-level summarization
- Summary caching (future)

**`user_router.py`**
- User management endpoints
- User registration and authentication
- User profile management
- User-document associations

#### Services (`src/services/`)

**`pdf_parser.py`**
- PDF text extraction
- Metadata extraction
- Error handling for corrupted files
- Support for various PDF formats

**`summary_service.py`**
- Summary generation orchestration
- Integration with Summary Agent
- Text preprocessing
- Summary caching and optimization

#### Utils (`src/utils/`)

**`Summary_agent.py`**
- AI-powered summarization
- Placeholder for custom implementation
- Integration with AI services
- Summary quality optimization

**`.env`**
- Environment variables
- Database credentials
- API keys and secrets
- Configuration flags

## Data Flow

### Document Upload Flow

1. **Client Request** → `documents_router.py`
2. **File Validation** → `pdf_parser.py`
3. **File Storage** → `src/uploads/`
4. **Database Record** → `db_models.py`
5. **Response** → Client

### Summary Generation Flow

1. **Client Request** → `summary_router.py`
2. **Document Retrieval** → `db_models.py`
3. **Text Extraction** → `pdf_parser.py`
4. **Summary Generation** → `summary_service.py` → `Summary_agent.py`
5. **Response** → Client

### Project Management Flow

1. **Client Request** → `project_router.py`
2. **Project Operations** → `db_models.py`
3. **Document Association** → Database relationships
4. **Response** → Client

## Database Schema

### Tables

#### Users
- `id` (Primary Key)
- `username` (Unique)
- `email` (Unique)
- `hashed_password`
- `created_at`

#### Projects
- `id` (Primary Key)
- `name`
- `description`
- `owner_id` (Foreign Key → Users)
- `created_at`

#### Documents
- `id` (Primary Key)
- `title`
- `file_path`
- `owner_id` (Foreign Key → Users)
- `project_id` (Foreign Key → Projects, Optional)
- `uploaded_at`

### Relationships

- **User → Projects**: One-to-Many
- **User → Documents**: One-to-Many
- **Project → Documents**: One-to-Many

## API Design Patterns

### RESTful Conventions

- **GET**: Retrieve resources
- **POST**: Create new resources
- **PUT**: Update existing resources
- **DELETE**: Remove resources

### Response Patterns

- **Success**: HTTP 200/201 with data
- **Not Found**: HTTP 404 with error message
- **Validation Error**: HTTP 422 with details
- **Server Error**: HTTP 500 with error message

### Pagination

- **Query Parameters**: `skip` and `limit`
- **Default Values**: skip=0, limit=100
- **Response Format**: Array of items

## Security Considerations

### Authentication

- JWT-based authentication (planned)
- Password hashing
- Session management

### Authorization

- User-based resource access
- Project ownership validation
- Document access control

### File Security

- File type validation
- Size limitations
- Secure file storage
- Path traversal prevention

## Extensibility Points

### Adding New File Types

1. Extend `pdf_parser.py` or create new parsers
2. Update `summary_service.py` to handle new types
3. Add validation in routers

### Custom Summary Agents

1. Implement `Summary_agent.py` interface
2. Add configuration options
3. Integrate with external AI services

### Additional Endpoints

1. Create new router files
2. Define schemas in `models/`
3. Add business logic in `services/`
4. Register routes in `main.py`

## Testing Strategy

### Unit Tests

- Test individual functions and methods
- Mock external dependencies
- Validate business logic

### Integration Tests

- Test API endpoints
- Validate database operations
- Test file processing

### End-to-End Tests

- Test complete workflows
- Validate user scenarios
- Performance testing

## Deployment Considerations

### Environment Configuration

- Separate configs for dev/staging/prod
- Environment-specific database URLs
- Secret management

### Scalability

- Database connection pooling
- File storage optimization
- Caching strategies
- Load balancing

### Monitoring

- Application logging
- Performance metrics
- Error tracking
- Health checks

## Future Enhancements

### Planned Features

1. **Authentication & Authorization**
   - JWT implementation
   - Role-based access control
   - OAuth integration

2. **Advanced File Processing**
   - Word document support
   - Excel file processing
   - Image text extraction (OCR)

3. **Enhanced Summarization**
   - Multiple summary types
   - Custom summary templates
   - Summary comparison

4. **API Improvements**
   - GraphQL support
   - Webhook notifications
   - Batch operations

5. **User Interface**
   - Web dashboard
   - Mobile application
   - Admin panel

### Technical Improvements

1. **Performance**
   - Async processing
   - Background tasks
   - Caching layer

2. **Reliability**
   - Error recovery
   - Data backup
   - Health monitoring

3. **Security**
   - Audit logging
   - Encryption at rest
   - Rate limiting

