from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import router as api_router

app = FastAPI(title="MigPAL Backend", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)

@app.get("/")
def root():
    return {
        "name": "MigPAL API",
        "version": "1.0.0",
        "status": "operational",
        "docs": f"{settings.api_prefix}/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
