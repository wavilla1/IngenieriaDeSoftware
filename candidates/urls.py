"""URL patterns for the candidates app."""
from django.urls import path
from candidates import views

urlpatterns = [
    path("", views.create_candidate, name="create_candidate"),
    path("candidates/", views.candidate_list, name="candidate_list"),
    path("candidates/<str:name>/edit/", views.edit_candidate, name="edit_candidate"),
    path("candidates/<str:name>/delete/", views.delete_candidate, name="delete_candidate"),
]
