class InvalidCredentialsError(Exception):
    """Raised when email or password is incorrect."""
 
 
class UserAlreadyExistsError(Exception):
    """Raised when trying to register an email that already exists."""
 
 
class InvalidTokenError(Exception):
    """Raised when a JWT token is missing, expired, or tampered with."""