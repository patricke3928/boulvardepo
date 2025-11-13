from django.contrib import admin
from .models import Tour, Booking

@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ('title', 'price')
    search_fields = ('title', 'description')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'tour', 'check_in', 'check_out', 'guests', 'created_at')
    search_fields = ('user__username', 'tour__title')
