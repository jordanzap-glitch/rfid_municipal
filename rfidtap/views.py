from django.shortcuts import render,redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, logout, login, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import path, include, reverse
from django.http import JsonResponse
from app.models import CustomUser
from django.db.models import Q

def LOGIN(request):
    return render(request,'index.html')


#login for the user

def doLogin(request):
    if request.method == "POST":
        user_input = request.POST.get('email')  # Can be email or username
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')

        # Find user by email or username
        try:
            user_obj = CustomUser.objects.get(Q(email=user_input) | Q(username=user_input))
            username = user_obj.username  # authenticate requires username, not email
        except CustomUser.DoesNotExist:
            messages.error(request, 'Invalid Email/Username or Password')
            return redirect('login')

        # Authenticate
        user = authenticate(request=request, username=username, password=password)

        if user is not None:
            login(request, user)
            user_type = user.user_type

            # ✅ Session Expiry
            if remember_me:
                request.session.set_expiry(2592000)  # 30 days
            else:
                request.session.set_expiry(0)  # Session ends when browser closes

            # ✅ Redirect Based on User Type
            if user_type == '1':
                return redirect('hoo_home')
            elif user_type == '2':
                return redirect('sysadmin_home')
            elif user_type == '3':
                return redirect('member_home')
            else:
                messages.error(request, 'Invalid user type.')
                return redirect('login')

        else:
            messages.error(request, 'Invalid Email/Username or Password')
            return redirect('login')

    return redirect('login')
