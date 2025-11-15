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

from .import sysadmin_views, views, munadmin_views, centeradmin_views, centerstaff_views, pesostaff_views, pesoadmin_views


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
    path('sysadmin/cycle', sysadmin_views.CYCLE_CREATE, name='sysadmin_cycle_create'),
    path('sysadmin/cycle/activate/<int:ay_id>/', sysadmin_views.CYCLE_ACTIVATE, name='sysadmin_cycle_activate'),
    # ajax
    path('ajax/municipalities/', sysadmin_views.get_municipalities, name='ajax_municipalities'),
    path('ajax/barangays/', sysadmin_views.get_barangays, name='ajax_barangays'),
    
    #municipal admin
    path('municipaladmin/home', munadmin_views.home, name='municipaladmin_home'),
    
    
    #center admin
    path('admincenter/home', centeradmin_views.home, name='admincenter_home'),
    path('admincenter/approval_table_meds', centeradmin_views.APPROVAL_TABLE_MEDS, name='approval_table_meds'),
    path('admincenter/get_bsr_center_info_meds', centeradmin_views.GET_BSR_CENTER_INFO_MEDS, name='get_bsr_center_info_meds'),
    path('admincenter/approval_table_burials', centeradmin_views.APPROVAL_TABLE_BURIALS, name='approval_table_burials'),
    path('admincenter/get_bsr_center_info_burials', centeradmin_views.GET_BSR_CENTER_INFO_BURIALS, name='get_bsr_center_info_burials'),
    
    
    #center staff
    path('centerstaff/home', centerstaff_views.home, name='centerstaff_home'),
    path('centerstaff/med_form', centerstaff_views.MED_FORM, name='med_form'),
    path('centerstaff/burial_form', centerstaff_views.BURIAL_FORM, name='burial_form'),
    path('get/registration_burials/<str:rfid>/', centerstaff_views.GET_REGISTRATION_BURIALS, name='get_registration_burials'),
    path('get/registration/<str:rfid>/', centerstaff_views.GET_REGISTRATION, name='get_registration'),
    
    
    #peso admin
    path('adminpeso/home', pesoadmin_views.home, name='adminpeso_home'),
    
    #peso staff
    path('pesostaff/home', pesostaff_views.home, name='pesostaff_home'),
    path('pesostaff/reap_form', pesostaff_views.REAP_FORM, name='reap_form'),
    path('pesostaff/reap_release', pesostaff_views.REAP_RELEASE, name='reap_release'),
    path('pesostaff/release_reap/', pesostaff_views.RELEASE_REAP, name='release_reap'),
    path('pesostaff/tupad_form', pesostaff_views.TUPAD_FORM, name='tupad_form'),
    path('get/registration_reap/<str:rfid>/', pesostaff_views.GET_REGISTRATION_REAP, name='get_registration_reap'),
    path('get/registration_tupad/<str:rfid>/', pesostaff_views.GET_REGISTRATION_TUPAD, name='get_registration_tupad'),  
    
]+ static(settings.MEDIA_URL,document_root = settings.MEDIA_ROOT)
