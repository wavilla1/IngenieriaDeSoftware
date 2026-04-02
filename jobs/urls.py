"""URL patterns for the jobs app."""
from django.urls import path
from jobs import views

urlpatterns = [
    path("", views.job_list, name="jobs"),
    path("apply/<str:job_name>/", views.apply, name="apply"),
]
