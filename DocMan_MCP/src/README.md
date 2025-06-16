
# DocMan_MCP Source Code

This directory contains the source code for the DocMan_MCP document management system.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables in `utils/.env`

3. Run the application:
   ```bash
   cd ..
   uvicorn main:app --reload
   ```

## Directory Structure

- `models/`: Database models and Pydantic schemas
- `routers/`: API route handlers
- `services/`: Business logic and services
- `utils/`: Utility functions and configuration
- `uploads/`: File upload directory

## Key Files

- `requirements.txt`: Python dependencies
- `openapi.json`: OpenAPI specification
- `utils/.env`: Environment configuration

## Development

For detailed development instructions, see the main documentation in the `docs/` directory.

## Testing

Run tests with:
```bash
pytest
```

## API Documentation

When the application is running, visit:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

