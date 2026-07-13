from django.contrib import admin  # Imports Django's admin module.
from django.urls import path  # Imports the function for defining URL routes.
from . import views  # Imports views from the current app.

urlpatterns = [  # Maps URLs to their corresponding views.
    path('', views.LandingPageView.as_view(), name='landing'),
]
