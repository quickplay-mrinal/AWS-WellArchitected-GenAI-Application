from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from app.api.routes.auth import get_current_user
from app.core.config import settings
import boto3
from botocore.exceptions import ClientError
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

s3_client = boto3.client('s3', region_name=settings.AWS_REGION)

@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Upload Well-Architected Framework documents to S3"""
    try:
        # Validate file type
        allowed_extensions = ['.pdf', '.txt', '.md', '.docx']
        file_ext = file.filename[file.filename.rfind('.'):]
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Upload to S3
        file_key = f"documents/{current_user['user_id']}/{file.filename}"
        
        s3_client.upload_fileobj(
            file.file,
            settings.S3_DOCS_BUCKET,
            file_key,
            ExtraArgs={'ContentType': file.content_type}
        )
        
        return {
            "message": "File uploaded successfully",
            "file_name": file.filename,
            "s3_key": file_key,
            "bucket": settings.S3_DOCS_BUCKET
        }
        
    except ClientError as e:
        logger.error(f"Error uploading to S3: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )

@router.get("/documents")
async def list_documents(current_user = Depends(get_current_user)):
    """List uploaded documents"""
    try:
        prefix = f"documents/{current_user['user_id']}/"
        
        response = s3_client.list_objects_v2(
            Bucket=settings.S3_DOCS_BUCKET,
            Prefix=prefix
        )
        
        documents = []
        for obj in response.get('Contents', []):
            documents.append({
                "file_name": obj['Key'].split('/')[-1],
                "size": obj['Size'],
                "last_modified": obj['LastModified'].isoformat(),
                "s3_key": obj['Key']
            })
        
        return {"documents": documents}
        
    except ClientError as e:
        logger.error(f"Error listing S3 objects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents"
        )

@router.delete("/documents/{file_name}")
async def delete_document(
    file_name: str,
    current_user = Depends(get_current_user)
):
    """Delete a document from S3"""
    try:
        file_key = f"documents/{current_user['user_id']}/{file_name}"
        
        s3_client.delete_object(
            Bucket=settings.S3_DOCS_BUCKET,
            Key=file_key
        )
        
        return {"message": "File deleted successfully"}
        
    except ClientError as e:
        logger.error(f"Error deleting from S3: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )
