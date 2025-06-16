
# API Reference

This document provides detailed information about all API endpoints available in DocMan_MCP.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API uses basic authentication. JWT authentication will be implemented in future versions.

## Endpoints

### Health Check

#### GET /
Check if the API is running.

**Response:**
```json
{
  "message": "Welcome to DocMan_MCP!"
}
```

---

## Documents API

### Create Document

#### POST /documents/

Create a new document record.

**Request Body:**
```json
{
  "title": "string",
  "file_path": "string",
  "project_id": 1
}
```

**Response:**
```json
{
  "id": 1,
  "title": "string",
  "file_path": "string",
  "owner_id": 1,
  "project_id": 1,
  "uploaded_at": "2023-01-01T00:00:00"
}
```

### List Documents

#### GET /documents/

Retrieve a list of all documents.

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum number of records to return (default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "title": "string",
    "file_path": "string",
    "owner_id": 1,
    "project_id": 1,
    "uploaded_at": "2023-01-01T00:00:00"
  }
]
```

### Get Document

#### GET /documents/{document_id}

Retrieve a specific document by ID.

**Path Parameters:**
- `document_id` (int): The ID of the document

**Response:**
```json
{
  "id": 1,
  "title": "string",
  "file_path": "string",
  "owner_id": 1,
  "project_id": 1,
  "uploaded_at": "2023-01-01T00:00:00"
}
```

### Upload Document

#### POST /documents/upload/

Upload a document file.

**Request:**
- Content-Type: `multipart/form-data`
- Body: File upload

**Response:**
```json
{
  "info": "file 'filename.pdf' saved at 'src/uploads/filename.pdf'",
  "document": {
    "id": 1,
    "title": "filename.pdf",
    "file_path": "src/uploads/filename.pdf",
    "owner_id": 1,
    "project_id": null,
    "uploaded_at": "2023-01-01T00:00:00"
  }
}
```

### Delete Document

#### DELETE /documents/{document_id}

Delete a specific document.

**Path Parameters:**
- `document_id` (int): The ID of the document

**Response:**
```json
{
  "message": "Document deleted successfully"
}
```

---

## Projects API

### Create Project

#### POST /projects/

Create a new project.

**Request Body:**
```json
{
  "name": "string",
  "description": "string"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "string",
  "description": "string",
  "owner_id": 1,
  "created_at": "2023-01-01T00:00:00",
  "documents": []
}
```

### List Projects

#### GET /projects/

Retrieve a list of all projects.

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum number of records to return (default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "name": "string",
    "description": "string",
    "owner_id": 1,
    "created_at": "2023-01-01T00:00:00",
    "documents": []
  }
]
```

### Get Project

#### GET /projects/{project_id}

Retrieve a specific project by ID.

**Path Parameters:**
- `project_id` (int): The ID of the project

**Response:**
```json
{
  "id": 1,
  "name": "string",
  "description": "string",
  "owner_id": 1,
  "created_at": "2023-01-01T00:00:00",
  "documents": [
    {
      "id": 1,
      "title": "string",
      "file_path": "string",
      "owner_id": 1,
      "project_id": 1,
      "uploaded_at": "2023-01-01T00:00:00"
    }
  ]
}
```

### Update Project

#### PUT /projects/{project_id}

Update a specific project.

**Path Parameters:**
- `project_id` (int): The ID of the project

**Request Body:**
```json
{
  "name": "string",
  "description": "string"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "string",
  "description": "string",
  "owner_id": 1,
  "created_at": "2023-01-01T00:00:00",
  "documents": []
}
```

### Delete Project

#### DELETE /projects/{project_id}

Delete a specific project.

**Path Parameters:**
- `project_id` (int): The ID of the project

**Response:**
```json
{
  "message": "Project deleted successfully"
}
```

---

## Summary API

### Generate Document Summary

#### POST /summary/document/{document_id}

Generate a summary for a specific document.

**Path Parameters:**
- `document_id` (int): The ID of the document

**Response:**
```json
{
  "document_id": 1,
  "document_title": "string",
  "summary": "Generated summary text..."
}
```

### Generate Project Summary

#### POST /summary/project/{project_id}

Generate a consolidated summary for all documents in a project.

**Path Parameters:**
- `project_id` (int): The ID of the project

**Response:**
```json
{
  "project_id": 1,
  "project_name": "string",
  "document_count": 5,
  "summary": "Generated project summary text..."
}
```

---

## Users API

### Create User

#### POST /users/

Create a new user.

**Request Body:**
```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "string",
  "email": "user@example.com",
  "created_at": "2023-01-01T00:00:00"
}
```

### List Users

#### GET /users/

Retrieve a list of all users.

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum number of records to return (default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "username": "string",
    "email": "user@example.com",
    "created_at": "2023-01-01T00:00:00"
  }
]
```

### Get User

#### GET /users/{user_id}

Retrieve a specific user by ID.

**Path Parameters:**
- `user_id` (int): The ID of the user

**Response:**
```json
{
  "id": 1,
  "username": "string",
  "email": "user@example.com",
  "created_at": "2023-01-01T00:00:00"
}
```

### Delete User

#### DELETE /users/{user_id}

Delete a specific user.

**Path Parameters:**
- `user_id` (int): The ID of the user

**Response:**
```json
{
  "message": "User deleted successfully"
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Error message describing the bad request"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["field_name"],
      "msg": "Error message",
      "type": "error_type"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

