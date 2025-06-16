
# Setup Guide

This guide will help you set up DocMan_MCP on your local development environment.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- pip (Python package installer)

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd DocMan_MCP
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r src/requirements.txt
```

### 4. Database Setup

#### Install PostgreSQL
- **Ubuntu/Debian**: `sudo apt-get install postgresql postgresql-contrib`
- **macOS**: `brew install postgresql`
- **Windows**: Download from [PostgreSQL official website](https://www.postgresql.org/download/)

#### Create Database

```sql
CREATE DATABASE docman_db;
CREATE USER docman_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE docman_db TO docman_user;
```

### 5. Environment Configuration

Create and configure the environment file:

```bash
cp src/utils/.env.example src/utils/.env
```

Edit `src/utils/.env` with your database credentials:

```env
DATABASE_URL=postgresql://docman_user:your_password@localhost/docman_db
SECRET_KEY=your-secret-key-here
DEBUG=True
UPLOAD_FOLDER=src/uploads
```

### 6. Database Migration

```bash
# Create tables
python -c "from config.db import engine; from models.db_models import Base; Base.metadata.create_all(bind=engine)"
```

### 7. Create Upload Directory

```bash
mkdir -p src/uploads
```

### 8. Run the Application

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 9. Verify Installation

- Open your browser and go to `http://localhost:8000`
- Check the API documentation at `http://localhost:8000/docs`
- Test the health endpoint: `http://localhost:8000/`

## Development Setup

### Additional Development Dependencies

```bash
pip install pytest pytest-asyncio httpx
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
pip install black isort
black .
isort .
```

## Production Deployment

### Environment Variables

Set the following environment variables for production:

```env
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=your-production-secret-key
DEBUG=False
UPLOAD_FOLDER=/path/to/uploads
```

### Using Docker (Optional)

```dockerfile
FROM python:3.9

WORKDIR /app

COPY src/requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Reverse Proxy Setup

Configure nginx or Apache to proxy requests to your FastAPI application.

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify PostgreSQL is running
   - Check database credentials in `.env`
   - Ensure database exists

2. **Import Errors**
   - Verify virtual environment is activated
   - Check all dependencies are installed

3. **File Upload Issues**
   - Ensure upload directory exists and has write permissions
   - Check file size limits

### Getting Help

- Check the [API documentation](api.md)
- Review the [usage guide](usage.md)
- Open an issue on GitHub

