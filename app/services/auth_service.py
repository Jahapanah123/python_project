import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_opaque_refresh_token,
    hash_password,
    hash_token,
    verify_password_safe,
)
from app.core.config import settings
from app.schemas.auth import MessageResponse, TokenResponse, UserResponse
from app.services.protocol import UserRepositoryProto
from utils.errors import (
    InvalidCredentialsError,
    RefreshTokenExpiredError,
    RefreshTokenNotFoundError,
    RefreshTokenRevokedError,
    UserAlreadyExistsError,
    UserInactiveError,
    UserNotFoundError,
    InvalidTokenError,
)


class AuthService:
    def __init__(self, repo: UserRepositoryProto, session: AsyncSession):
        self.repo = repo
        self.session = session

    async def register(self, email: str, password: str) -> UserResponse:
        existing = await self.repo.get_user_by_email(email)
        if existing is not None:
            raise UserAlreadyExistsError(f"Email '{email}' is already registered.")

        hashed = hash_password(password)
        user = await self.repo.create_user(email=email, hashed_password=hashed)
        await self.session.commit()

        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.repo.get_user_by_email(email)

        if not verify_password_safe(password, user.hashed_password if user else None):
            raise InvalidCredentialsError("Invalid email or password.")

        if user is None:
            raise InvalidCredentialsError("Invalid email or password.")

        if not user.is_active:
            raise UserInactiveError("This account has been deactivated.")

        return await self._issue_tokens(user)

    async def refresh_tokens(self, raw_refresh_token: str) -> TokenResponse:
        incoming_hash = hash_token(raw_refresh_token)
        token_record = await self.repo.get_refresh_token_by_hash(incoming_hash)

        if token_record is None:
            raise RefreshTokenNotFoundError("Refresh token not found.")

        if token_record.revoked:
            await self.repo.revoke_all_user_tokens(token_record.user_id)
            await self.session.commit()
            raise RefreshTokenRevokedError(
                "Refresh token reuse detected. All sessions have been terminated."
            )

        if token_record.is_expired:
            raise RefreshTokenExpiredError("Refresh token has expired. Please log in again.")

        user = await self.repo.get_user_by_id(token_record.user_id)
        if user is None:
            raise UserNotFoundError("User associated with this token no longer exists.")
        if not user.is_active:
            raise UserInactiveError("This account has been deactivated.")

        async with self.session.begin_nested():
            await self.repo.revoke_refresh_token_by_hash(incoming_hash)
            new_tokens = await self._issue_tokens_no_commit(user)

        await self.session.commit()
        return new_tokens

    async def logout(self, raw_refresh_token: str) -> MessageResponse:
        token_hash = hash_token(raw_refresh_token)
        token_record = await self.repo.get_refresh_token_by_hash(token_hash)

        if token_record is not None and not token_record.revoked:
            await self.repo.revoke_refresh_token_by_hash(token_hash)
            await self.session.commit()

        return MessageResponse(message="Logged out successfully.")

    async def get_current_user(self, access_token: str) -> User:
        payload = decode_access_token(access_token)
        user_id_str: str = payload["sub"]

        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise InvalidTokenError("Token subject is not a valid UUID.")

        user = await self.repo.get_user_by_id(user_id)
        print("AUTH USER:", user)
        print("AUTH USER ID:", user.id if user else None)
        print("AUTH USER ACTIVE:", user.is_active if user else None)
        if user is None:
            raise UserNotFoundError("User not found.")
        if not user.is_active:
            raise UserInactiveError("Account is deactivated.")

        return user

    async def _issue_tokens(self, user) -> TokenResponse:
        raw_refresh_token = generate_opaque_refresh_token()
        hashed = hash_token(raw_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        await self.repo.create_refresh_token(
            user_id=user.id,
            token_hash=hashed,
            expires_at=expires_at,
        )
        await self.session.commit()

        access_token = create_access_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
        )

    async def _issue_tokens_no_commit(self, user) -> TokenResponse:
        raw_refresh_token = generate_opaque_refresh_token()
        hashed = hash_token(raw_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        await self.repo.create_refresh_token(
            user_id=user.id,
            token_hash=hashed,
            expires_at=expires_at,
        )

        access_token = create_access_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
        )