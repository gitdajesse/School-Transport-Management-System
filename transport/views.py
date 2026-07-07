from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError

from .models import User, Parent, Bus, Student, Assistant, Attendance, Notification, RouteAssignment

# Create your views here.
def index(request):
    """ Home page - redirects to appropraite dashboard if logged in """

    if request.user.is_authenticated:
        # Redirect based on user type
        if request.user.user_type == 'parent':
            return redirect('parent_dashboard')
        elif request.user.user_type == 'assistant':
            return redirect('assistant_dashboard')
        elif request.user.user_type == 'admin':
            return redirect('admin_dashboard')
        else:
            return render(request, 'transport/index.html')
    else:
        return render (request, 'transport/index.html')

def register(request):
    """ Handle user registration """

    # If user is already logged in, redirect to appropriate dashboard
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        # Get form data
        user_type = request.POST.get('user_type')
        username = request.POST.get('username')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone_number = request.POST.get('phone_number')
        home_address = request.POST.get('home_address')

        # Validation
        if not user_type or user_type not in ['admin', 'parent', 'assistant']:
            messages.error(request, 'Please select a valid user type')
            return render(request, 'transport/register.html')

        if not username:
            messages.error(request, 'Please fill in your username')
            return render(request, 'transport/register.html')

        if not full_name:
            messages.error(request, 'Please fill in your full name')
            return render(request, 'transport/register.html')

        if not password:
            messages.error(request, 'Please fill in your password')
            return render(request, 'transport/register.html')

        if not confirm_password:
            messages.error(request, 'Please confirm your password')
            return render(request, 'transport/register.html')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'transport/register.html')

        # Conditional validation based on user type
        if user_type == 'parent':
            if not email:
                messages.error(request, 'Please fill in your email')
                return render(request, 'transport/register.html')
            if not phone_number:
                messages.error(request, 'Please fill in your phone number')
                return render(request, 'transport/register.html')
            if not home_address:
                messages.error(request, 'Please fill in your home address')
                return render(request, 'transport/register.html')
        elif user_type == 'assistant':
            if not phone_number:
                messages.error(request, 'Please fill in your phone number')
                return render(request, 'transport/register.html')

        try:
            # Create user
            user = User.objects.create_user(
                username = username,
                email = email,
                password = password
            )
            # Add custom fields
            user.user_type = user_type
            user.phone_number = phone_number or ''
            user.save()

            # Create profile based on user type
            if user_type == 'parent':
                Parent.objects.create(
                    user = user,
                    name = full_name,
                    email = email or '',
                    phone_number = phone_number or '',
                    home_address = home_address or ''
                )
            elif user_type == 'assistant':
                Assistant.objects.create(
                    user = user,
                    name = full_name,
                    email = email or '',
                    phone_number = phone_number or ''
                )

            # Login user after registration
            login(request, user)
            messages.success(request, f'Registration successful! Welcome {full_name}!')

            # Redirect based to user_type
            if user_type == 'parent':
                return redirect('parent_dashboard')
            elif user_type == 'assistant':
                return redirect('assistant_dashboard')
            else:
                return redirect('admin_dashboard')

        except IntegrityError:
            messages.error(request, 'Username already exists. Please choose a different username.')
            return render(request, 'transport/register.html')
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return render(request, 'transport/register.html')

    # Get request
    return render (request, 'transport/register.html')

def login_view(request):
    """ Handles user login """

    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username:
            messages.error(request, 'Please provide your username')
            return render(request, 'transport/login.html')

        if not password:
            messages.error(request, 'Please provide your password')
            return render(request, 'transport/login.html')

        # Authenticate user
        user = authenticate(request, username = username, password = password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')

            # Redirect based on user type
            if user.user_type == 'parent':
                return redirect('parent_dashboard')
            elif user.user_type == 'assistant':
                return redirect('assistant_dashboard')
            elif user.user_type == 'admin':
                return redirect('admin_dashboard')
            else:
                return redirect('index')
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, 'transport/login.html')

    return render (request, 'transport/login.html')

def logout_view(request):
    """ Handles user logout """

    logout(request)
    messages.info(request, 'You have been logged out successfully')
    return redirect('index')

@login_required
def parent_dashboard(request):
    if request.user.user_type != 'parent':
        messages.error(request, 'Access denied. You are not a parent.')
        return redirect('index')
    else:
        return render (request, 'transport/parent_dashboard.html')

@login_required
def assistant_dashboard(request):
    if request.user.user_type != 'assistant':
        messages.error(request, 'Access denied. You are not an assistant.')
        return redirect('index')
    else:
        return render (request, 'transport/assistant_dashboard.html')


@login_required
def admin_dashboard(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. You are not an admin.')
        return redirect('index')
    else:
        context = {
            'total_students': Student.objects.count(),
            'total_parents': Parent.objects.count(),
            'total_assistants': Assistant.objects.count(),
            'total_buses': Bus.objects.count()
        }
        return render (request, 'transport/admin_dashboard.html', context)
