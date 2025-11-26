from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # App
    APP_NAME: str = "AWS Well-Architected GenAI Assessment"
    ENVIRONMENT: str = "development"
    
    # AWS
    AWS_REGION: str = "ap-southeast-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    
    # DynamoDB
    DYNAMODB_TABLE_NAME: str = "WellArchitectedApp"
    
    # Bedrock
    BEDROCK_MODEL_ID: str = "anthropic.claude-sonnet-4-20250514-v1:0"
    BEDROCK_INFERENCE_PROFILE_ARN: str = ""
    BEDROCK_KNOWLEDGE_BASE_ID: str = ""
    
    # S3
    S3_DOCS_BUCKET: str = ""
    S3_REPORTS_BUCKET: str = ""
    
    # Security
    SECRET_KEY: str
    ENCRYPTION_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
