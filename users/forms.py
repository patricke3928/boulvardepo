from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
from .models import PasswordEntry
from .models import VaultEntry
import uuid
from .models import Device


class DeviceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        device_id = request.COOKIES.get('device_id')
        if not device_id:
            device_id = str(uuid.uuid4())
            request.new_device_id = device_id
        response = self.get_response(request)
        if hasattr(request, 'new_device_id'):
            response.set_cookie('device_id', request.new_device_id, max_age=10*365*24*60*60)
        return response


class VaultEntryForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = VaultEntry
        fields = ['title', 'login', 'password']

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.set_password(self.cleaned_data['password'])
        if commit:
            instance.save()
        return instance
    



class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False)
    gender = forms.ChoiceField(choices=Profile.GENDER_CHOICES, required=False)
    birth_year = forms.IntegerField(required=False, min_value=1900, max_value=2100)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email', 'password1', 'password2', 'gender', 'birth_year']

def save(self, commit=True):
    user = super().save(commit=False)
    user.email = self.cleaned_data['email']
    user.first_name = self.cleaned_data['first_name']
    
    if commit:
        user.save()
        
        profile, created = Profile.objects.get_or_create(user=user)
        profile.gender = self.cleaned_data['gender']
        profile.birth_year = self.cleaned_data['birth_year']
        profile.save()
    
    return user

from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar']


class PasswordEntryForm(forms.ModelForm):
    plain_password = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = PasswordEntry
        fields = ['title', 'login', 'url', 'notes']

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw_password = self.cleaned_data.get('plain_password', '')
        if raw_password:
            instance.set_password(raw_password)
        if commit:
            instance.save()
        return instance

    def __init__(self, *args, **kwargs):
        
        self.instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)       


