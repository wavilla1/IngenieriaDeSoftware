"""URL patterns for the matching app."""
from django.urls import path
from matching import views

urlpatterns = [
    path("recommendations/<str:name>/", views.recommendations, name="recommendations"),
]
