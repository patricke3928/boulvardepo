

import base64
import hashlib
from cryptography.fernet import Fernet
from django.conf import settings

def _get_fernet():
  
    master = getattr(settings, "CRYPTO_MASTER_KEY", None) or settings.SECRET_KEY
    
    digest = hashlib.sha256(master.encode('utf-8')).digest()
    key = base64.urlsafe_b64encode(digest)  
    return Fernet(key)

def encrypt_text(plaintext: str) -> bytes:
    f = _get_fernet()
    return f.encrypt(plaintext.encode('utf-8'))

def decrypt_text(token: bytes) -> str:
    f = _get_fernet()
    return f.decrypt(bytes(token)).decode('utf-8')
