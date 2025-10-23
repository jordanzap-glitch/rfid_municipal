from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Register your models here.
# Always put the models here to edit in the admin dashboard of django
class UserModel(UserAdmin):
    list_display = ['id','last_name','first_name', 'username', 'user_type']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    list_filter = ['is_active', 'is_staff', 'user_type']

admin.site.register(CustomUser, UserModel)
admin.site.register(Registration)
admin.site.register(RifdAuth)