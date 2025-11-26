from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta

from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token

router = APIRouter()
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = UserRepository.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    try:
        # Check if user exists
        existing_user = UserRepository.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        existing_username = UserRepository.get_user_by_username(user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = UserRepository.create_user(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        
        return {
            "id": new_user['user_id'],
            "email": new_user['email'],
            "username": new_user['username'],
            "full_name": new_user.get('full_name'),
            "is_active": new_user['is_active'],
            "created_at": new_user['created_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    try:
        user = UserRepository.get_user_by_username(user_data.username)
        
        if not user or not verify_password(user_data.password, user['hashed_password']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.get('is_active', True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user['username'], "user_id": user['user_id']}, 
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    return {
        "id": current_user['user_id'],
        "email": current_user['email'],
        "username": current_user['username'],
        "full_name": current_user.get('full_name'),
        "is_active": current_user['is_active'],
        "created_at": current_user['created_at']
    }
