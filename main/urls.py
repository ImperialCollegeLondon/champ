from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("", views.index, name="index"),
    path("submit", views.submit, name="submit"),
    path("status/<str:job_id>/", views.status, name="status"),
    path("delete/<str:job_id>/", views.delete, name="delete"),
]
