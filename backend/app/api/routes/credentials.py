from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.api.routes.auth import get_current_user
from app.repositories.credential_repository import CredentialRepository
from app.schemas.credential import CredentialCreate, CredentialResponse
from app.core.security import encrypt_credential, decrypt_credential

router = APIRouter()

@router.post("/", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    credential_data: CredentialCreate,
    current_user = Depends(get_current_user)
):
    # Encrypt credentials
    encrypted_access_key = encrypt_credential(credential_data.access_key)
    encrypted_secret_key = encrypt_credential(credential_data.secret_key)
    
    # Create credential
    credential = CredentialRepository.create_credential(
        user_id=current_user['user_id'],
        credential_name=credential_data.credential_name,
        encrypted_access_key=encrypted_access_key,
        encrypted_secret_key=encrypted_secret_key
    )
    
    return {
        "id": credential['credential_id'],
        "credential_name": credential['credential_name'],
        "is_active": credential['is_active'],
        "created_at": credential['created_at']
    }

@router.get("/", response_model=List[CredentialResponse])
async def list_credentials(current_user = Depends(get_current_user)):
    credentials = CredentialRepository.get_user_credentials(current_user['user_id'])
    
    return [
        {
            "id": cred['credential_id'],
            "credential_name": cred['credential_name'],
            "is_active": cred['is_active'],
            "created_at": cred['created_at']
        }
        for cred in credentials
    ]

@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    credential_id: str,
    current_user = Depends(get_current_user)
):
    credential = CredentialRepository.get_credential_by_id(credential_id)
    
    if not credential or credential['user_id'] != current_user['user_id']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )
    
    return {
        "id": credential['credential_id'],
        "credential_name": credential['credential_name'],
        "is_active": credential['is_active'],
        "created_at": credential['created_at']
    }

@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    credential_id: str,
    current_user = Depends(get_current_user)
):
    credential = CredentialRepository.get_credential_by_id(credential_id)
    
    if not credential or credential['user_id'] != current_user['user_id']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )
    
    CredentialRepository.delete_credential(current_user['user_id'], credential_id)
    return None
