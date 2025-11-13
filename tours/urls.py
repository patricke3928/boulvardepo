from django.urls import path
from . import views

app_name = 'tours'

urlpatterns = [
    path('', views.home_view, name='home'),  
    path('tours/', views.tour_list, name='tour_list'),
    path('search/', views.search_tours, name='search_tours'),
    path('book/<int:pk>/', views.book_tour, name='book_tour'),
    path('<int:tour_id>/', views.tour_detail, name='tour_detail'),
    
]
