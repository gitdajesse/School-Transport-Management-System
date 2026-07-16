from django.shortcuts import render, redirect, get_object_or_404
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
    # Only allow admins
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. You are not an admin.')
        return redirect('index')

    return render(request, 'transport/manage_system.html')


@login_required
def student_list(request):
    """ Display list of all students """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can view all students.')
        return redirect('index')

    # Get all parents and buses for dropdowns
    parents = Parent.objects.all()
    buses = Bus.objects.all()

    context = {
        'parents': parents,
        'buses': buses,
    }

    # Handle form submission
    if request.method == "POST":
        # Get form data
        full_name = request.POST.get('full_name')
        grade = request.POST.get('grade')
        parent_name = request.POST.get('parent_name')
        bus_registration = request.POST.get('bus')
        pick_up = request.POST.get('pick_up')
        drop_off = request.POST.get('drop_off')
        emergency_contact = request.POST.get('emergency_contact')

        # Save entered data so form does not reset
        context['form_data'] = {
            'full_name': full_name,
            'grade': grade,
            'parent_name': parent_name,
            'bus': bus_registration,
            'pick_up': pick_up,
            'drop_off': drop_off,
            'emergency_contact': emergency_contact,
        }

        # Validation
        if not full_name:
            messages.error(request, "Please fill in the student's name.")
            context['form_data'] = request.POST
            return render(request, 'transport/student_list.html', context)
        if not grade:
            messages.error(request, "Please fill in the student's grade.")
            context['form_data'] = request.POST
            return render(request, 'transport/student_list.html', context)
        if not parent_name:
            messages.error(request, "Please select a parent for the student")
            context['form_data'] = request.POST
            return render(request, 'transport/student_list.html', context)
        if not bus_registration:
            messages.error(request, "Please select a bus for the student")
            context['form_data'] = request.POST
            return render(request, 'transport/student_list.html', context)
        if not pick_up:
            messages.error(request, "Please fill in the pick up location")
            context['form_data'] = request.POST
            return render(request, 'transport/student_list.html', context)
        if not drop_off:
            messages.error(request, "Please fill in the drop off location")
            context['form_data'] = request.POST
            return render(request, 'transport/student_list.html', context)
        if not emergency_contact:
            messages.error(request, "Please fill in the student's emergency contact")
            context['form_data'] = request.POST
            return render(request, 'transport/student_list.html', context)

        try:
            # Find the parent
            parent = Parent.objects.get(name = parent_name)
        except Parent.DoesNotExist:
            messages.error(request, 'Parent not found. Please register the parent first.')
            return render(request, 'transport/student_list.html', context)

        try:
            # Find the bus
            bus_obj = Bus.objects.get(registration = bus_registration)
        except Bus.DoesNotExist:
            messages.error(request, 'Bus not found. Please register the bus first.')
            return render(request, 'transport/student_list.html', context)

        # Check if student already exists
        existing_student = Student.objects.filter(
            name = full_name,
            parent = parent,
            is_active = True
        ).first()

        if existing_student:
            messages.warning(request, 'Student already exists for this parent.')
            return redirect('student_list')

        try:
            # Create student
            student = Student.objects.create(
                name = full_name,
                grade = grade,
                parent = parent,
                bus = bus_obj,
                pick_up_location = pick_up,
                drop_off_location = drop_off,
                emergency_contact = emergency_contact,
                is_active = True
            )

            messages.success(request, f'Successfully added {full_name} as a student!')

            # Redirect to student list
            return redirect('student_list')

        except Exception as e:
            messages.error(request, f'Error adding student: {str(e)}')
            return render(request, 'transport/student_list.html', context)

    else:
        students = Student.objects.all().order_by('name')

        # Count active vs inactive
        active_students = students.filter(is_active = True).count()
        inactive_students = students.filter(is_active = False).count()

        # Group by grade
        grades = {}

        for student in students:
            if student.grade not in grades:
                grades[student.grade] = 0
            grades[student.grade] += 1

        context.update({
            'students': students,
            'total_students': students.count(),
            'active_students': active_students,
            'inactive_students': inactive_students,
            'grades': grades
        })

        return render(request, 'transport/student_list.html', context)


@login_required
def edit_student(request, student_id):
    """ Edit a student's information """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can edit students.')
        return redirect('index')

    student = get_object_or_404(Student, id = student_id)

    # Access the form
    if request.method == 'POST':
        # Update student
        student.name = request.POST.get('full_name', student.name)
        student.grade = request.POST.get('grade', student.grade)
        student.pick_up_location = request.POST.get('pick_up', student.pick_up_location)
        student.drop_off_location = request.POST.get('drop_off', student.drop_off_location)
        student.emergency_contact = request.POST.get('emergency_contact', student.emergency_contact)

        # Update bus if changed
        bus_registration = request.POST.get('bus')
        if bus_registration:
            try:
                bus_obj = Bus.objects.get(registration = bus_registration)
                student.bus = bus_obj
            except Bus.DoesNotExist:
                messages.error(request, 'Bus not found.')

        # Update parent if changed
        parent_name = request.POST.get('parent_name')
        if parent_name:
            try:
                parent = Parent.objects.get(name = parent_name)
                student.parent = parent
            except Parent.DoesNotExist:
                messages.error(request, 'Parent not found.')

        # Update active status
        is_active = request.POST.get('is_active')
        student.is_active = is_active == 'on'

        student.save()
        messages.success(request, f'Student "{ student.name }" updated successfully!')
        return redirect('student_list')

    # Get request, show edit form
    else:
        parents = Parent.objects.all()
        buses = Bus.objects.all()

        context = {
            'student': student,
            'parents': parents,
            'buses': buses
        }
        return render(request, 'transport/edit_student.html', context)


@login_required
def deactivate_student(request, student_id):
    """ Deactivate a student """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can deactivate students.')
        return redirect('index')

    student = get_object_or_404(Student, id = student_id)

    if request.method == 'POST':
        student.is_active = False
        student.save()
        messages.success(request, f'"{student.name}" has been deactivated.')
        return redirect('student_list')

    context = {
        'student': student
    }

    return render(request, 'transport/confirm_deactivated.html', context)


@login_required
def reactivate_student(request, student_id):
    """ Reactivate a deactivated student """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can reactivate students.')

    student = get_object_or_404(Student, id = student_id)

    if request.method == 'POST':
        student.is_active = True
        student.is_active()
        messages.success(request, f'Student "{student.name}" has been reactivated.')
        return redirect('student_list')

    context = {
        'student': student
    }

    return render(request, 'transport/confirm_reactivate.html', context)


@login_required
def bus_list(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can view all buses.')
        return redirect('index')

    return render(request, 'transport/bus_list.html')
