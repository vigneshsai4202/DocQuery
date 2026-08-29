from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import conversations, documents, query
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="AI document intelligence platform — upload PDFs, ask questions, get grounded answers with source citations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_prefix = settings.API_V1_PREFIX
app.include_router(documents.router, prefix=_prefix)
app.include_router(query.router, prefix=_prefix)
app.include_router(conversations.router, prefix=_prefix)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "app": settings.APP_NAME}
