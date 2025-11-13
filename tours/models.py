from django.db import models
from django.contrib.auth.models import User
from django.apps import AppConfig

class Tour(models.Model):
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    location = models.CharField(max_length=100)
    description = models.TextField()
    available_seats = models.IntegerField()
    image = models.ImageField(upload_to='tours/', null=True, blank=True)

    def __str__(self):
        return self.title

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE)
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=[('active', 'Active'), ('cancelled', 'Cancelled')], default='active')
    cancel_reason = models.CharField(max_length=100, blank=True, null=True)
    cancel_time = models.DateTimeField(blank=True, null=True)


    def __str__(self):
        return f"{self.user.username} - {self.tour.title}"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tour_reviews')
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='tour_reviews')
    rating = models.PositiveSmallIntegerField()
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.rating}⭐"
    


