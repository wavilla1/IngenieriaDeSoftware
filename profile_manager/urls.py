"""URL configuration for the Profile Manager project."""
from django.urls import path, include

urlpatterns = [
    path("", include("candidates.urls")),
    path("jobs/", include("jobs.urls")),
    path("matching/", include("matching.urls")),
]
