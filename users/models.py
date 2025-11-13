from django.db import models
from django.contrib.auth.models import User
from tours.models import Tour
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings
import uuid


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


FERNET_KEY = getattr(settings, 'FERNET_KEY', Fernet.generate_key())
fernet = Fernet(FERNET_KEY)



class VaultEntry(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vault_entries')
    title = models.CharField(max_length=255)
    login = models.CharField(max_length=255, blank=True)
    password_encrypted = models.BinaryField(default=b'')

    url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def set_password(self, raw_password):
        if raw_password:
            self.password_encrypted = fernet.encrypt(raw_password.encode())
        else:
            self.password_encrypted = b''

    def get_password(self):
        if self.password_encrypted:
            return fernet.decrypt(self.password_encrypted).decode()
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
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_entries')
    title = models.CharField(max_length=200)
    login = models.CharField(max_length=200, blank=True)
    password_encrypted = models.BinaryField()
    url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def set_password(self, raw_password):
        self.password_encrypted = fernet.encrypt(raw_password.encode())

    def get_password(self):
        return fernet.decrypt(self.password_encrypted).decode()

    def __str__(self):
        return f"{self.title} ({self.owner.username})"
