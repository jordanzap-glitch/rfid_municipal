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

from .import sysadmin_views, views, munadmin_views, centeradmin_views, centerstaff_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    #login
    path('', views.LOGIN,name='login'),
    path('doLogin', views.doLogin, name='doLogin'),
    path('doLogout', views.doLogout, name='doLogout'),
    path('registration', views.registration_member, name='registration_member'),
    
    
    # admin
    path('sysadmin/home', sysadmin_views.home, name='sysadmin_home'),
    # show registration form
    path('sysadmin/register', sysadmin_views.REGISTRATION_MEMBER, name='sysadmin_register'),
    # ajax
    path('ajax/municipalities/', sysadmin_views.get_municipalities, name='ajax_municipalities'),
    path('ajax/barangays/', sysadmin_views.get_barangays, name='ajax_barangays'),
    
    #municipal admin
    path('municipaladmin/home', munadmin_views.home, name='municipaladmin_home'),
    
    
    #center admin
    path('admincenter/home', centeradmin_views.home, name='admincenter_home'),
    path('admincenter/approval_table', centeradmin_views.APPROVAL_TABLE, name='approval_table'),
    path('centeradmin/get_bsr_center_info', centeradmin_views.GET_BSR_CENTER_INFO, name='get_bsr_center_info'),
    
    
    #center staff
    path('centerstaff/home', centerstaff_views.home, name='centerstaff_home'),
    path('centerstaff/med_form', centerstaff_views.med_form, name='med_form'),
    path('api/registration/<str:rfid>/', centerstaff_views.registration_api, name='registration_api'),
]+ static(settings.MEDIA_URL,document_root = settings.MEDIA_ROOT)
