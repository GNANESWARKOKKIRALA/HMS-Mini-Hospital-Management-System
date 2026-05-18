from django.urls import path
from . import views

urlpatterns = [
    path('book/<int:slot_id>/', views.book_slot, name='book_slot'),
]
