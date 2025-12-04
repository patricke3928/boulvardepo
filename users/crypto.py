

import base64
import json
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from django.conf import settings
from django.core.cache import cache
import os



def _get_or_generate_rsa_keys():
    
    
    private_key_pem = getattr(settings, "RSA_PRIVATE_KEY", None)
    public_key_pem = getattr(settings, "RSA_PUBLIC_KEY", None)
    
    if private_key_pem and public_key_pem:
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode() if isinstance(private_key_pem, str) else private_key_pem,
            password=None
        )
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode() if isinstance(public_key_pem, str) else public_key_pem
        )
        return private_key, public_key
    
  
    cached_keys = cache.get('rsa_keys')
    if cached_keys:
        private_key = serialization.load_pem_private_key(
            cached_keys['private'].encode(),
            password=None
        )
        public_key = serialization.load_pem_public_key(
            cached_keys['public'].encode()
        )
        return private_key, public_key
    
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    
   
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()
    
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    
    cache.set('rsa_keys', {
        'private': private_pem,
        'public': public_pem
    }, 30 * 24 * 60 * 60) 
    
    return private_key, public_key


def get_public_key():
    
    _, public_key = _get_or_generate_rsa_keys()
    return public_key


def get_private_key():
    
    private_key, _ = _get_or_generate_rsa_keys()
    return private_key


def export_keys():
    
    private_key, public_key = _get_or_generate_rsa_keys()
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()
    
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    
    return {
        'private_key': private_pem,
        'public_key': public_pem
    }


def encrypt_text(plaintext: str) -> bytes:
  
    if not isinstance(plaintext, str):
        plaintext = str(plaintext)
    
    public_key = get_public_key()
    
  
    plaintext_bytes = plaintext.encode('utf-8')
    
    if len(plaintext_bytes) > 190:
        
        encrypted = public_key.encrypt(
            plaintext_bytes[:190],
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return base64.b64encode(encrypted)
    
    encrypted = public_key.encrypt(
        plaintext_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    return base64.b64encode(encrypted)


def decrypt_text(encrypted_token: bytes) -> str:
  
    if isinstance(encrypted_token, str):
        encrypted_token = encrypted_token.encode()
    
    private_key = get_private_key()
    
    try:
        encrypted_bytes = base64.b64decode(encrypted_token)
        decrypted = private_key.decrypt(
            encrypted_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")



def encrypt_text_fernet_compat(plaintext: str) -> bytes:
    
    return encrypt_text(plaintext)


def decrypt_text_fernet_compat(token: bytes) -> str:
    
    return decrypt_text(token)
