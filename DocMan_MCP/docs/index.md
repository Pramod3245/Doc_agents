
# DocMan_MCP

DocMan_MCP is a comprehensive document management system built with FastAPI that provides powerful document organization, storage, and AI-powered summarization capabilities.

## Features

- **Document Management**: Upload, organize, and manage documents efficiently
- **Project Organization**: Group related documents into projects
- **AI-Powered Summarization**: Generate intelligent summaries for individual documents and entire projects
- **User Management**: Multi-user support with authentication
- **RESTful API**: Complete REST API for all operations
- **PDF Support**: Advanced PDF parsing and text extraction
- **Metadata Extraction**: Automatic extraction of document metadata

## Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT-based authentication
- **File Processing**: PyPDF2 for PDF handling
- **API Documentation**: Automatic OpenAPI/Swagger documentation

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r src/requirements.txt
   ```

2. Set up environment variables in `src/utils/.env`

3. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

4. Access the API documentation at `http://localhost:8000/docs`

## Project Structure

The project follows a modular architecture with clear separation of concerns:

- `config/`: Database configuration and settings
- `src/models/`: Database models and Pydantic schemas
- `src/routers/`: API route handlers
- `src/services/`: Business logic and services
- `src/utils/`: Utility functions and helpers
- `docs/`: Comprehensive documentation

## API Endpoints

### Documents
- `POST /documents/` - Create a new document
- `GET /documents/` - List all documents
- `GET /documents/{id}` - Get specific document
- `POST /documents/upload/` - Upload document file
- `DELETE /documents/{id}` - Delete document

### Projects
- `POST /projects/` - Create a new project
- `GET /projects/` - List all projects
- `GET /projects/{id}` - Get specific project
- `PUT /projects/{id}` - Update project
- `DELETE /projects/{id}` - Delete project

### Summaries
- `POST /summary/document/{id}` - Generate document summary
- `POST /summary/project/{id}` - Generate project summary

### Users
- `POST /users/` - Create a new user
- `GET /users/` - List all users
- `GET /users/{id}` - Get specific user
- `DELETE /users/{id}` - Delete user

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

