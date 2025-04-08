from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='auth/logout.html'), name='logout'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
]