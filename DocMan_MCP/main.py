from fastapi import FastAPI
from config.db import connect_to_mongo, close_mongo_connection
from src.routers import documents_router, project_router, summary_router, user_router, translation_router

app = FastAPI(
    title="DocMan_MCP",
    description="A comprehensive document management system with AI-powered summarization",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    connect_to_mongo()

@app.on_event("shutdown")
def shutdown_event():
    close_mongo_connection()

# Include routers
app.include_router(documents_router.router, prefix="/api/v1", tags=["documents"])
app.include_router(project_router.router, prefix="/api/v1", tags=["projects"])
app.include_router(summary_router.router, prefix="/api/v1", tags=["summaries"])
app.include_router(user_router.router, prefix="/api/v1", tags=["users"])
app.include_router(translation_router.router, prefix="/api/v1", tags=["translation"])

@app.get("/")
def root():
    return {"message": "Welcome to DocMan_MCP!"}


