from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api.routes import auth, credentials, scan, report, s3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AWS Well-Architected GenAI Assessment API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"AWS Region: {settings.AWS_REGION}")
    yield
    logger.info("Shutting down application...")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="GenAI-powered AWS Well-Architected Framework Assessment Platform",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(credentials.router, prefix="/api/credentials", tags=["Credentials"])
app.include_router(scan.router, prefix="/api/scan", tags=["Scanning"])
app.include_router(report.router, prefix="/api/report", tags=["Reports"])
app.include_router(s3.router, prefix="/api/s3", tags=["S3 Documents"])

@app.get("/")
async def root():
    return {
        "message": "AWS Well-Architected GenAI Assessment API",
        "version": "1.0.0",
        "status": "running",
        "bedrock_model": settings.BEDROCK_MODEL_ID
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
