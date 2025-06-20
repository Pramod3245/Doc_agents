from fastapi import FastAPI
from config.db import connect_to_mongo, close_mongo_connection
from src.routers import documents_router, project_router, user_router
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
import json
from datetime import datetime

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
app.include_router(user_router.router, prefix="/api/v1", tags=["users"])

@app.get("/")
def root():
    return {"message": "Welcome to DocMan_MCP!"}

# Custom JSON file exporter
class JSONFileSpanExporter(SpanExporter):
    def __init__(self, file_path):
        self.file_path = file_path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

    def export(self, spans):
        data = []
        for span in spans:
            data.append({
                'name': span.name,
                'context': {
                    'trace_id': span.context.trace_id,
                    'span_id': span.context.span_id
                },
                'parent_id': span.parent.span_id if span.parent else None,
                'start_time': datetime.fromtimestamp(span.start_time / 1e9).isoformat(),
                'end_time': datetime.fromtimestamp(span.end_time / 1e9).isoformat(),
                'attributes': dict(span.attributes),
                'events': [
                    {
                        'name': event.name,
                        'timestamp': datetime.fromtimestamp(event.timestamp / 1e9).isoformat(),
                        'attributes': dict(event.attributes)
                    } for event in span.events
                ],
                'status': str(span.status.status_code),
                'resource': dict(span.resource.attributes)
            })
        with open(self.file_path, 'a') as f:
            for entry in data:
                f.write(json.dumps(entry, indent=2) + '\n')
        return SpanExportResult.SUCCESS

    def shutdown(self):
        pass

# OpenTelemetry setup
trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({SERVICE_NAME: "DocMan_MCP"})
    )
)
tracer = trace.get_tracer(__name__)
json_exporter = JSONFileSpanExporter("otel_traces/trace_log.json")
span_processor = BatchSpanProcessor(json_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)


