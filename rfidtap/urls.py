"""
URL configuration for rfidtap project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .import sysadmin_views, views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    #login
    path('', views.LOGIN,name='login'),
    path('doLogin', views.doLogin, name='doLogin'),
    
    
    # admin
    path('sysadmin/home', sysadmin_views.home, name='sysadmin_home'),
    # show registration form
    path('sysadmin/register', sysadmin_views.registration_member, name='sysadmin_register'),
    # ajax
    path('ajax/municipalities/', sysadmin_views.get_municipalities, name='ajax_municipalities'),
    path('ajax/barangays/', sysadmin_views.get_barangays, name='ajax_barangays'),
]+ static(settings.MEDIA_URL,document_root = settings.MEDIA_ROOT)
