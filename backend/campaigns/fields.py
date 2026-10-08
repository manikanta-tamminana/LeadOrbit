from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models


_PREFIX = 'enc:v1:'


def _fernet():
    key = getattr(settings, 'LEADORBIT_TOKEN_ENCRYPTION_KEY', '')
    if not key:
        raise ImproperlyConfigured(
            'LEADORBIT_TOKEN_ENCRYPTION_KEY must be set before storing OAuth tokens.'
        )
    try:
        return Fernet(key.encode('ascii'))
    except (ValueError, UnicodeEncodeError) as exc:
        raise ImproperlyConfigured(
            'LEADORBIT_TOKEN_ENCRYPTION_KEY must be a valid Fernet key.'
        ) from exc


def encrypt_token(value):
    if value is None or value == '' or value.startswith(_PREFIX):
        return value
    return _PREFIX + _fernet().encrypt(value.encode('utf-8')).decode('ascii')


def decrypt_token(value):
    if value is None or not value.startswith(_PREFIX):
        # Allows old plaintext records to be read during deployment migration.
        return value
    try:
        return _fernet().decrypt(value[len(_PREFIX):].encode('ascii')).decode('utf-8')
    except (InvalidToken, UnicodeEncodeError) as exc:
        raise ImproperlyConfigured('Stored OAuth token could not be decrypted.') from exc


class EncryptedTextField(models.TextField):
    """Encrypt sensitive OAuth tokens at rest while exposing plaintext to app code."""

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return encrypt_token(value)

    def from_db_value(self, value, expression, connection):
        return decrypt_token(value)

    def to_python(self, value):
        return decrypt_token(value)
