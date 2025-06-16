
# Usage Guide

This guide provides examples and best practices for using DocMan_MCP effectively.

## Getting Started

### 1. Start the Application

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Access the API Documentation

Open your browser and navigate to:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## Basic Workflows

### User Management

#### Creating a User

```bash
curl -X POST "http://localhost:8000/users/" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "john_doe",
       "email": "john@example.com",
       "password": "secure_password"
     }'
```

#### Listing Users

```bash
curl -X GET "http://localhost:8000/users/"
```

### Project Management

#### Creating a Project

```bash
curl -X POST "http://localhost:8000/projects/" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Research Project",
       "description": "A project for research documents"
     }'
```

#### Updating a Project

```bash
curl -X PUT "http://localhost:8000/projects/1" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Updated Research Project",
       "description": "Updated description"
     }'
```

### Document Management

#### Uploading a Document

```bash
curl -X POST "http://localhost:8000/documents/upload/" \
     -F "file=@/path/to/your/document.pdf"
```

#### Creating a Document Record

```bash
curl -X POST "http://localhost:8000/documents/" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Important Document",
       "file_path": "src/uploads/document.pdf",
       "project_id": 1
     }'
```

#### Listing Documents

```bash
# Get all documents
curl -X GET "http://localhost:8000/documents/"

# Get documents with pagination
curl -X GET "http://localhost:8000/documents/?skip=0&limit=10"
```

### Summary Generation

#### Generate Document Summary

```bash
curl -X POST "http://localhost:8000/summary/document/1"
```

#### Generate Project Summary

```bash
curl -X POST "http://localhost:8000/summary/project/1"
```

## Advanced Usage

### Working with the Summary Agent

The Summary Agent is a placeholder that you need to implement. Here's how to integrate your own summarization logic:

1. **Edit the Summary Agent**: Modify `src/utils/Summary_agent.py`
2. **Implement the methods**:
   - `generate_summary(text_content)`: For individual document summaries
   - `generate_project_summary(combined_summaries)`: For project-level summaries

Example implementation:

```python
class SummaryAgent:
    def __init__(self):
        # Initialize your AI model or API client here
        pass
    
    def generate_summary(self, text_content: str) -> str:
        # Your summarization logic here
        # This could use OpenAI, Hugging Face, or any other AI service
        return "Your generated summary"
    
    def generate_project_summary(self, combined_summaries: str) -> str:
        # Your project-level summarization logic here
        return "Your generated project summary"
```

### File Processing

#### Supported File Types

- **PDF**: Full text extraction and metadata parsing
- **Text files**: Direct text processing
- **Future**: Word documents, Excel files, etc.

#### PDF Processing Example

```python
from services.pdf_parser import PDFParser

parser = PDFParser()
text = parser.extract_text_from_pdf("path/to/document.pdf")
metadata = parser.get_pdf_metadata("path/to/document.pdf")
```

### Database Operations

#### Direct Database Access

```python
from config.db import SessionLocal
from models.db_models import Document, Project, User

db = SessionLocal()

# Query documents
documents = db.query(Document).filter(Document.project_id == 1).all()

# Create a new project
new_project = Project(name="New Project", owner_id=1)
db.add(new_project)
db.commit()
```

## Integration Examples

### Python Client

```python
import requests

class DocManClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def upload_document(self, file_path):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{self.base_url}/documents/upload/", files=files)
        return response.json()
    
    def get_summary(self, document_id):
        response = requests.post(f"{self.base_url}/summary/document/{document_id}")
        return response.json()

# Usage
client = DocManClient()
result = client.upload_document("my_document.pdf")
summary = client.get_summary(result['document']['id'])
```

### JavaScript/Node.js Client

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

class DocManClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async uploadDocument(filePath) {
        const form = new FormData();
        form.append('file', fs.createReadStream(filePath));
        
        const response = await axios.post(`${this.baseUrl}/documents/upload/`, form, {
            headers: form.getHeaders()
        });
        
        return response.data;
    }
    
    async getSummary(documentId) {
        const response = await axios.post(`${this.baseUrl}/summary/document/${documentId}`);
        return response.data;
    }
}

// Usage
const client = new DocManClient();
client.uploadDocument('my_document.pdf')
    .then(result => client.getSummary(result.document.id))
    .then(summary => console.log(summary));
```

## Best Practices

### File Organization

1. **Use Projects**: Group related documents into projects for better organization
2. **Meaningful Names**: Use descriptive titles for documents and projects
3. **Regular Cleanup**: Periodically remove unused documents and projects

### Performance Optimization

1. **Pagination**: Use skip and limit parameters for large datasets
2. **Batch Operations**: Process multiple documents together when possible
3. **Caching**: Implement caching for frequently accessed summaries

### Security Considerations

1. **File Validation**: Validate uploaded files before processing
2. **Access Control**: Implement proper user authentication and authorization
3. **Data Sanitization**: Sanitize all user inputs

### Error Handling

1. **Check Response Status**: Always check HTTP status codes
2. **Handle Exceptions**: Implement proper error handling in your client code
3. **Retry Logic**: Implement retry logic for transient failures

## Troubleshooting

### Common Issues

1. **File Upload Fails**
   - Check file size limits
   - Verify upload directory permissions
   - Ensure sufficient disk space

2. **Summary Generation Errors**
   - Verify Summary Agent implementation
   - Check document text extraction
   - Review error logs

3. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check connection string in `.env`
   - Ensure database exists

### Debugging Tips

1. **Enable Debug Mode**: Set `DEBUG=True` in your `.env` file
2. **Check Logs**: Monitor application logs for errors
3. **Use API Documentation**: Test endpoints using the interactive docs
4. **Database Inspection**: Use PostgreSQL tools to inspect database state

## Performance Monitoring

### Metrics to Track

1. **Response Times**: Monitor API response times
2. **File Processing Time**: Track document processing duration
3. **Database Performance**: Monitor query execution times
4. **Storage Usage**: Track file storage consumption

### Optimization Strategies

1. **Database Indexing**: Add indexes for frequently queried fields
2. **File Compression**: Compress stored files to save space
3. **Async Processing**: Use background tasks for heavy operations
4. **Caching**: Implement Redis or similar for caching summaries

