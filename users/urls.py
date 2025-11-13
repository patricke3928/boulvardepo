from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/clear-avatar/', views.clear_avatar, name='clear_avatar'),
    path('admins/', views.admins_list, name='admins_list'),
    path('make-admin/<int:user_id>/', views.make_admin, name='make_admin'),
    path('bookings/', views.user_bookings, name='user_bookings'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),



    path('vault/', views.vault_list, name='vault_list'),
    path('vault/add/', views.vault_create, name='vault_create'),
    path('vault/<int:pk>/edit/', views.vault_edit, name='vault_edit'),
    path('vault/<int:pk>/delete/', views.vault_delete, name='vault_delete'),
    path('vault/<int:pk>/reveal/', views.vault_reveal, name='vault_reveal'),
    path('vault/', views.vault_list, name='password_vault'),
    path('vault/generate_rsa/', views.generate_rsa_password_view, name='generate_rsa_password'),

    
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)