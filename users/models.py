from django.db import models
from django.contrib.auth.models import User
from tours.models import Tour
from django.utils import timezone
from django.conf import settings
import uuid
from .crypto import encrypt_text, decrypt_text


class Device(models.Model):
    device_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Device {self.device_id} ({self.owner.username})"
    


def avatar_upload_path(instance, filename):
    return f'avatars/user_{instance.user.id}/{filename}'

class Profile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to=avatar_upload_path, default='avatars/default-avatar.png')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    birth_year = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"


class VaultEntry(models.Model):
    """
    Secure password vault entry using RSA-2048 encryption.
    Passwords are encrypted with RSA public key and decrypted with private key.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vault_entries')
    title = models.CharField(max_length=255)
    login = models.CharField(max_length=255, blank=True)
    password_encrypted = models.BinaryField(default=b'')

    url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def set_password(self, raw_password):
        """Encrypt and store password using RSA."""
        if raw_password:
            self.password_encrypted = encrypt_text(raw_password)
        else:
            self.password_encrypted = b''

    def get_password(self):
        """Decrypt and retrieve password using RSA."""
        if self.password_encrypted:
            return decrypt_text(self.password_encrypted)
        return ''

    def __str__(self):
        return f"{self.title} ({self.owner.username})"


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_reviews')
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='tour_user_reviews')
    rating = models.PositiveSmallIntegerField()
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.tour.title}"



class PasswordEntry(models.Model):
    """
    Password manager entry with RSA-2048 encryption.
    Used for storing passwords for various accounts and services.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_entries')
    title = models.CharField(max_length=200)
    login = models.CharField(max_length=200, blank=True)
    password_encrypted = models.BinaryField()
    url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def set_password(self, raw_password):
        """Encrypt and store password using RSA."""
        self.password_encrypted = encrypt_text(raw_password)

    def get_password(self):
        """Decrypt and retrieve password using RSA."""
        return decrypt_text(self.password_encrypted)

    def __str__(self):
        return f"{self.title} ({self.owner.username})"
