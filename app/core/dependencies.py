import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.repository.user_repo import UserRepository
from app.schemas.auth import UserResponse
from app.services.auth_service import AuthService
from utils.errors import InvalidTokenError, TokenExpiredError, UserNotFoundError, UserInactiveError
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=True)


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    repo = UserRepository(db)
    return AuthService(repo, db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    service: AuthService = Depends(get_auth_service),
) -> User:
    token = credentials.credentials
    
    try:
        return await service.get_current_user(token)
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (InvalidTokenError, UserNotFoundError, UserInactiveError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )