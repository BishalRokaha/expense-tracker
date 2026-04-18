from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from supabase import Client

from app.config import settings
from app.features.auth.schemas import RegisterRequest, LoginRequest, TokenResponse
from app.features.auth.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    InvalidTokenError,
)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # token valid for 1 hour


class AuthService:
    """
    Handles all authentication logic:
    - Registering new users (hashing password, storing in DB)
    - Logging in (verifying password, issuing JWT)
    - Verifying JWT tokens on protected routes
    """

    def __init__(self, client: Client):
        self._client = client

    # Helpers 
    def _hash_password(self, plain: str) -> str:
        return pwd_context.hash(plain)

    def _verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    def _create_access_token(self, user_id: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {"sub": user_id, "exp": expire}
        return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)

    #  Public methods 
    def register(self, data: RegisterRequest) -> TokenResponse:
        # Check if email already exists
        existing = (
            self._client.table("users")
            .select("id")
            .eq("email", data.email)
            .execute()
        )
        if existing.data:
            raise UserAlreadyExistsError(f"Email '{data.email}' is already registered.")

        # Store the hashed password 
        hashed = self._hash_password(data.password)
        result = (
            self._client.table("users")
            .insert({"email": data.email, "hashed_password": hashed})
            .execute()
        )
        user = result.data[0]
        token = self._create_access_token(user["id"])
        return TokenResponse(access_token=token, user_id=user["id"])

    def login(self, data: LoginRequest) -> TokenResponse:
        # Fetch user by email
        result = (
            self._client.table("users")
            .select("*")
            .eq("email", data.email)
            .execute()
        )
        if not result.data:
            raise InvalidCredentialsError("Invalid email or password.")

        user = result.data[0]

        if not self._verify_password(data.password, user["hashed_password"]):
            raise InvalidCredentialsError("Invalid email or password.")

        token = self._create_access_token(user["id"])
        return TokenResponse(access_token=token, user_id=user["id"])

    def verify_token(self, token: str) -> str:
        """
        Decodes and validates a JWT token.
        Returns the user_id (stored in the 'sub' claim).
        Raises InvalidTokenError if the token is invalid or expired.
        """
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise InvalidTokenError("Token has no subject.")
            return user_id
        except JWTError:
            raise InvalidTokenError("Token is invalid or has expired.")