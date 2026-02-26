from cryptography.fernet import Fernet

from app.core.config import settings

fernet = Fernet(settings.ENCRYPTION_KEY.encode())
