"""URL patterns for the jobs app."""
from django.urls import path
from jobs import views

urlpatterns = [
    path("", views.job_list, name="jobs"),
    path("apply/<str:job_name>/", views.apply, name="apply"),
    path("create/", views.create_job, name="create_job"),
    path("<str:name>/edit/", views.edit_job, name="edit_job"),
    path("<str:name>/delete/", views.delete_job, name="delete_job"),
]
