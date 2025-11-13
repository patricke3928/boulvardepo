import secrets
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Avg, Count

from travelbook.utils.telegram_notify import send_telegram_message
from blog.forms import BlogForm
from .models import Tour, Booking, Review
from .forms import BookingForm




def generate_rsa_password():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    return pem.decode('utf-8')[:16]


def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR", "unknown")


def get_user_agent(request):
    return request.META.get("HTTP_USER_AGENT", "unknown")




def home_view(request):
    return render(request, 'tours/home.html')


def search_tours(request):
    query = request.GET.get('q', '').strip()
    tours = Tour.objects.filter(title__icontains=query) if query else Tour.objects.all()

    data = [{
        'id': t.id,
        'title': t.title,
        'description': (t.description or '')[:100],
        'price': str(t.price),
        'image': t.image.url if getattr(t, 'image', None) and t.image else '/static/images/default_avatar.png',
    } for t in tours]

    return JsonResponse({'tours': data})




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
                now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                msg = (
                    f"🆕 <b>New Registration</b>\n"
                    f"👤 User: <code>{user.username}</code>\n"
                    f"📧 Email: <code>{user.email or '—'}</code>\n"
                    f"⏰ Time: {now}\n"
                    f"🌐 IP: <code>{ip}</code>\n"
                    f"💻 User-Agent: {ua}"
                )
                send_telegram_message(msg)
            except Exception as e:
                print("Telegram send failed:", e)

            return redirect('users:profile')

    return render(request, 'users/register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")

            try:
                ip = get_client_ip(request)
                ua = get_user_agent(request)
                now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                msg = (
                    f"✅ <b>User Logged In</b>\n"
                    f"👤 User: <code>{user.username}</code>\n"
                    f"⏰ Time: {now}\n"
                    f"🌐 IP: <code>{ip}</code>\n"
                    f"💻 User-Agent: {ua}"
                )
                send_telegram_message(msg)
            except Exception as e:
                print("Telegram send failed:", e)

            return redirect('users:profile')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect('tours:tour_list')


def profile_view(request):
    bookings = Booking.objects.filter(user=request.user).select_related('tour')
    stats = {
        'total_bookings': bookings.count(),
        'reviews': Review.objects.filter(user=request.user).count(),
        'avg_rating': Review.objects.filter(user=request.user).aggregate(Avg('rating'))['rating__avg'] or 0,
    }
    return render(request, 'users/profile.html', {"user": request.user, "stats": stats, "bookings": bookings})




def tour_list(request):
    tours = Tour.objects.all().annotate(review_count=Count('tour_reviews'))
    return render(request, 'tours/tour_list.html', {'tours': tours})


def tour_detail(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    reviews = tour.tour_reviews.all().order_by('-created_at')
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    if request.method == 'POST' and request.user.is_authenticated:
        rating = int(request.POST.get('rating', 5))
        text = request.POST.get('text', '').strip()

        if text:
            Review.objects.create(tour=tour, user=request.user, rating=rating, text=text)
            messages.success(request, "Your review has been added!")

            try:
                msg = (
                    f"📝 <b>New Review Added</b>\n"
                    f"🏝 Tour: <b>{tour.title}</b>\n"
                    f"👤 User: <code>{request.user.username}</code>\n"
                    f"⭐ Rating: {rating}\n"
                    f"💬 Comment: {text}"
                )
                send_telegram_message(msg)
            except Exception as e:
                print("Telegram send failed:", e)

            return redirect('tours:tour_detail', tour_id=tour.id)
        else:
            messages.error(request, "Comment cannot be empty.")

    return render(request, 'tours/tour_detail.html', {
        'tour': tour,
        'reviews': reviews,
        'average_rating': average_rating,
    })


def book_tour(request, pk):
    tour = get_object_or_404(Tour, pk=pk)
    if request.method == 'POST':
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        guests = int(request.POST.get('guests', 1))

        Booking.objects.create(
            user=request.user,
            tour=tour,
            check_in=check_in,
            check_out=check_out,
            guests=guests
        )

        try:
            ip = get_client_ip(request)
            ua = get_user_agent(request)
            now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            msg = (
                f"📌 <b>New Booking Created</b>\n"
                f"🏝 Tour: <b>{tour.title}</b>\n"
                f"👤 User: <code>{request.user.username}</code>\n"
                f"👥 Guests: {guests}\n"
                f"⏰ Time: {now}\n"
                f"🌐 IP: <code>{ip}</code>\n"
                f"💻 User-Agent: {ua}"
            )
            send_telegram_message(msg)
        except Exception as e:
            print("Telegram send failed:", e)

        messages.success(request, "Tour booked successfully!")
        return redirect('tours:tour_list')

    form = BookingForm()
    return render(request, 'tours/book_tour.html', {'tour': tour, 'form': form})




def create_blog_post(request):
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            blog = form.save(commit=False)
            blog.owner = request.user
            blog.save()

            try:
                msg = (
                    f"📰 <b>New Blog Post Published</b>\n"
                    f"👤 Author: <b>{blog.owner.username}</b>\n"
                    f"🕓 Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"📖 Title: <b>{blog.title}</b>\n\n"
                    f"{blog.description[:300]}..."
                )
                send_telegram_message(msg)
            except Exception as e:
                print("Telegram send failed:", e)

            messages.success(request, "Blog post created successfully!")
            return redirect('blog:list')
    else:
        form = BlogForm()

    return render(request, 'blog/create_blog.html', {'form': form})


def create_tour(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price', 0)
        image = request.FILES.get('image')

        tour = Tour.objects.create(
            title=title,
            description=description,
            price=price,
            image=image
        )

        try:
            msg = (
                f"🌍 <b>New Tour Created</b>\n"
                f"🏝 Title: <b>{tour.title}</b>\n"
                f"💰 Price: ${tour.price}\n"
                f"🕓 Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"📜 Description:\n{tour.description[:300]}..."
            )
            send_telegram_message(msg)
        except Exception as e:
            print("Telegram send failed:", e)

        messages.success(request, "Tour created successfully!")
        return redirect('tours:tour_list')

    return render(request, 'tours/create_tour.html')


