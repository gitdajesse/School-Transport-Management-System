from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError

from .models import User, Parent, Bus, Student, Assistant, Attendance, Notification, RouteAssignment

# Create your views here.
def index(request):
    """ Home page - redirects to appropraite dashboard if logged in """

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


@login_required
def manage_system(request):
    if request.method == "POST":

        # Get form data
        full_name = request.POST.get('full_name')
        grade = request.POST.get('grade')
        parent_name = request.POST.get('parent_name')
        bus = request.POST.get('bus')
        pick_up = request.POST.get('pick_up')
        drop_off = request.POST.get('drop_off')
        emergency_contact = request.POST.get('emergency_contact')

        # Validation
        if not full_name:
            messages.error(request, "Please fill in the student's name.")
            return render(request, 'transport/manage_system.html')
        if not grade:
            messages.error(request, "Please fill in the student's grade.")
            return render(request, 'transport/manage_system.html')
        if not parent_name:
            messages.error(request, "Please fill in the student's parent name")
            return render(request, 'transport/manage_system.html')
        if not bus:
            messages.error(request, "Please fill in the bus related to the student")
            return render(request, 'transport/manage_system.html')
        if not pick_up:
            messages.error(request, "Please fill in the pick up location")
            return render(request, 'transport/manage_system.html')
        if not drop_off:
            messages.error(request, "Please fill in the drop off location")
            return render(request, 'transport/manage_system.html')
        if not emergency_contact:
            messages.error(request, "Please fill in the student's emergency contact")
            return render(request, 'transport/manage_system.html')

        # Create student
        # Not fully functional
        student = student.objects.create(
            name = full_name,
            grade = grade,
            parent = parent_name,
            bus = bus,
            pick_up_location = pick_up,
            drop_off_location = drop_off,
            emergency_contact = emergency_contact,
        )

        messages.success(request, f'Successfully added {full_name} as a student')
    else:
        return render(request, 'transport/manage_system.html')
