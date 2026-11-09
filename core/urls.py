from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('home/', views.home_view, name='home_alt'),
    path('favicon.ico', views.favicon_view, name='favicon'),
    path('healthcheck/', views.healthcheck, name='healthcheck'),
]
