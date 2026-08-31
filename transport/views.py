from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from django.http import JsonResponse
from decimal import Decimal
import calendar

from .models import User, Parent, Bus, Student, Assistant, Attendance, Notification, RouteAssignment, Route, Stop, Fee, Payment


# Create your views here.
def index(request):
    """ Home page - redirects to appropraite dashboard if logged in """

    return render (request, 'transport/index.html')


def register(request):
    """ Handle user registration """

    # If user is already logged in, redirect to appropriate dashboard
    if request.user.is_authenticated:
        return redirect('index')

    context = {
        'form_data': request.POST
    }

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
            return render(request, 'transport/register.html', context)

        if not username:
            messages.error(request, 'Please fill in your username')
            return render(request, 'transport/register.html', context)

        if not full_name:
            messages.error(request, 'Please fill in your full name')
            return render(request, 'transport/register.html', context)

        if not password:
            messages.error(request, 'Please fill in your password')
            return render(request, 'transport/register.html', context)

        if not confirm_password:
            messages.error(request, 'Please confirm your password')
            return render(request, 'transport/register.html', context)

        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'transport/register.html', context)

        # Conditional validation based on user type
        if user_type == 'parent':
            if not email:
                messages.error(request, 'Please fill in your email')
                return render(request, 'transport/register.html', context)
            if not phone_number:
                messages.error(request, 'Please fill in your phone number')
                return render(request, 'transport/register.html', context)
            if not home_address:
                messages.error(request, 'Please fill in your home address')
                return render(request, 'transport/register.html', context)
        elif user_type == 'assistant':
            if not phone_number:
                messages.error(request, 'Please fill in your phone number')
                return render(request, 'transport/register.html', context)

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
    return render(request, 'transport/register.html')


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
    """ Dashboard for the parent to have an overview of the system """
    if request.user.user_type != 'parent':
        messages.error(request, 'Access denied. You are not a parent.')
        return redirect('index')
    else:
        return render (request, 'transport/parent_dashboard.html')


@login_required
def assistant_dashboard(request):
    """ Dashboard for the assistant to have an overview of the system. """
    if request.user.user_type != 'assistant':
        messages.error(request, 'Access denied. You are not an assistant.')
        return redirect('index')
    else:
        return render (request, 'transport/assistant_dashboard.html')


@login_required
def admin_dashboard(request):
    """ Dashboard for the admin to have an overview of the system """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. You are not an admin.')
        return redirect('index')
    else:
        return render (request, 'transport/admin_dashboard.html')


@login_required
def manage_system(request):
    """ Central location to manage the models """
    # Only allow admins
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. You are not an admin.')
        return redirect('index')

    total_buses = Bus.objects.count()
    total_students = Student.objects.count()
    total_routes = Route.objects.count()
    total_parents = Parent.objects.count()
    total_assistants = Assistant.objects.count()

    context = {
        'total_buses': total_buses,
        'total_students': total_students,
        'total_routes': total_routes,
        'total_parents': total_parents,
        'total_assistants': total_assistants
    }

    return render(request, 'transport/manage_system.html', context)


@login_required
def student_list(request):
    """ Display list of all students and add student """
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

            # Send notification to parent
            notify_parents_about_new_student(student)

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
def student_detail(request, student_id):
    """ View detailed information about a specific person """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can edit students.')
        return redirect('index')

    student = get_object_or_404(Student, id = student_id)

    # Get today's attendance
    today = timezone.now().date()
    today_attendance = Attendance.objects.filter(student = student, date = today).first()

    # Get attendance history (last 30 records)
    attendance_records = Attendance.objects.filter(student = student).order_by('-date')[:30]

    # Calculate statistics
    total_records = Attendance.objects.filter(student = student).count()
    present_count = Attendance.objects.filter(student = student, status__in = ['picked_up', 'dropped_off']).count()
    absent_count = Attendance.objects.filter(student = student, status = 'absent').count()

    context = {
        'student': student,
        'today': today,
        'today_attendance': today_attendance,
        'attendance_records': attendance_records,
        'total_records': total_records,
        'present_count': present_count,
        'absent_count': absent_count
    }

    return render(request, 'transport/student_detail.html', context)


@login_required
def edit_student(request, student_id):
    """ Edit a student's information """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can edit students.')
        return redirect('index')

    student = get_object_or_404(Student, id = student_id)
    old_bus = student.bus

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
                new_bus = Bus.objects.get(registration = bus_registration)

                # If bus changed, notify parent
                if old_bus != new_bus:
                    student.bus = new_bus
                    notify_parents_about_bus_change(student, old_bus, new_bus)
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
        is_active = request.POST.get('is_active') == 'on'
        student.is_active = is_active

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
        student.save()
        messages.success(request, f'Student "{student.name}" has been reactivated.')
        return redirect('student_list')

    context = {
        'student': student
    }

    return render(request, 'transport/confirm_reactivate.html', context)


@login_required
def bus_list(request):
    """ Add a bus and see bus statistics """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can view all buses.')
        return redirect('index')

    # Get all routes
    routes = Route.objects.all()

    # Get all buses
    buses = Bus.objects.all().order_by('registration')

    # Calculate statistics
    total_buses = buses.count()
    active_buses = buses.filter(is_active = True).count()
    inactive_buses = buses.filter(is_active = False).count()

    # Calculate capacity utilization for each bus
    for bus in buses:
        student_count = Student.objects.filter(bus = bus, is_active = True).count()

        if bus.capacity > 0:
            utilization = (student_count / bus.capacity * 100)
        else:
            utilization = 0

        bus.student_count = student_count
        bus.utilization_percent = utilization
        bus.utilization = f"{utilization:.0f}%"

        if utilization > 90:
            bus.progress_color = "bg-danger"
        elif utilization > 70:
            bus.progress_color = "bg-warning"
        else:
            bus.progress_color = "bg-success"

    context = {
        'routes': routes,
        'buses': buses,
        'total_buses': total_buses,
        'active_buses': active_buses,
        'inactive_buses': inactive_buses
    }

    # Get form data
    if request.method == 'POST':
        bus_registration = request.POST.get('bus_registration')
        driver_name = request.POST.get('driver_name')
        capacity = request.POST.get('capacity')
        route_name = request.POST.get('route_name')

        # Validation
        if not bus_registration:
            messages.error(request, 'Please enter the bus registration.')
            return render(request, 'transport/bus_list.html', context)
        if not capacity:
            messages.error(request, 'Please enter the bus capacity.')
            return render(request, 'transport/bus_list.html', context)
        if not driver_name:
            messages.error(request, "Please enter the driver's name.")
            return render(request, 'transport/bus_list.html', context)
        if not route_name:
            messages.error(request, 'Please enter the route name the bus will be using.')
            return render(request, 'transport/bus_list.html', context)

        # Validate capacity
        try:
            capacity = int(capacity)
            if capacity <= 0:
                messages.error(request, 'Capacity must be a positive number')
                return render(request, 'transport/bus_list.html', context)
        except ValueError:
            messages.error(request, 'Capacity must be a number.')
            return render(request, 'transport/bus_list.html', context)

        # Check for duplicate registration
        if Bus.objects.filter(registration = bus_registration).exists():
            messages.error(request, f'Bus {bus_registration} already exists.')
            return render(request, 'transport/bus_list.html', context)

        try:
            # Create bus
            bus = Bus.objects.create(
                registration = bus_registration,
                driver_name = driver_name,
                capacity = capacity,
                route_name = route_name,
                is_active = True
            )
            messages.success(request, f'Bus "{bus_registration}" added successfully!')
            return redirect('bus_list')

        except Exception as e:
            messages.error(request, f'Error adding bus: {str(e)}')
            return render(request, 'transport/bus_list.html', context)

    else:
        return render(request, 'transport/bus_list.html', context)


@login_required
def edit_bus(request, bus_id):
    """ Edit an existing bus """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can edit buses.')
        return redirect('index')

    bus = get_object_or_404(Bus, id = bus_id)
    students = Student.objects.filter(bus = bus, is_active = True).order_by('name')
    student_count = students.count()

    utilization = (student_count / bus.capacity * 100) if bus.capacity > 0 else 0

    if request.method == 'POST':
        # Get form data
        registration = request.POST.get('bus_registration')
        driver_name = request.POST.get('driver_name')
        capacity = request.POST.get('capacity')
        route_name = request.POST.get('route_name')
        is_active = request.POST.get('is_active') == 'on'

        # Validatiion
        if not registration:
            messages.error(request, 'Please enter the bus registration.')
            return redirect('edit_bus', bus_id = bus_id)
        if not driver_name:
            messages.error(request, 'Please enter the bus registration.')
            return redirect('edit_bus', bus_id = bus_id)
        if not capacity:
            messages.error(request, 'Please enter the bus registration.')
            return redirect('edit_bus', bus_id = bus_id)
        if not route_name:
            messages.error(request, 'Please enter the bus registration.')
            return redirect('edit_bus', bus_id = bus_id)

        # Validate capacity
        try:
            capacity = int(capacity)
            if capacity <= 0:
                messages.error(request, 'Cannot must be a positive number.')
                return redirect('edit_bus', bus_id = bus_id)
        except ValueError:
            messages.error(request, 'Capacity must be a valid number.')
            return redirect('edit_bus', bus_id = bus_id)

        # Check for duplicate registration (excluding current bus)
        if Bus.objects.filter(registration = registration).exclude(id = bus_id).exists():
            messages.error(request, f'Bus "{registration}" already exists.')
            return redirect('edit_bus', bus_id = bus_id)

        try:
            # Update bus
            bus.registration = registration
            bus.driver_name = driver_name
            bus.capacity = capacity
            bus.route_name = route_name
            bus.is_active = is_active
            bus.save()

            messages.success(request, f'Bus "{registration}" updated sucessfully!')
            return redirect('bus_list')

        except Exception as e:
            messages.error(request, f'Error updating bus: {str(e)}')
            return redirect('edit_bus', bus_id = bus_id)

    else:
        # GET request
        context = {
            'bus': bus,
            'utilization': utilization
        }
        return render(request, 'transport/edit_bus.html', context)


@login_required
def deactivate_bus(request, bus_id):
    """ Deactivate a bus """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can deactivate buses.')
        return redirect('index')

    bus = get_object_or_404(Bus, id = bus_id)

    # Check if students are assigned to this bus
    students = Student.objects.filter(bus = bus, is_active = True)

    if students.exists():
        messages.warning(request, f'Bus "{bus.registration}" has {students.count()} students assigned. ' 'Please reassign students before deactivating.')
        return redirect('bus_list')

    if request.method == 'POST':
        for student in students:
            notify_parents_about_bus_change(student, bus, None)

        bus.is_active = False
        bus.save()

        messages.success(request, f'Bus "{bus.registration}" has been deactivated.')
        return redirect('bus_list')

    else:
        context = {
            'bus': bus,
            'student_count': students.count()
        }

        return render(request, 'transport/confirm_deactivate_bus.html', context)


@login_required
def reactivate_bus(request, bus_id):
    """ Reactiavte a deactivated bus """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can reactivate buses.')
        return redirect('index')

    bus = get_object_or_404(Bus, id = bus_id)

    if request.method == 'POST':
        bus.is_active = True
        bus.save()

        messages.success(request, f'Bus "{bus.registration}" has been reactivated.')
        return redirect('bus_list')

    else:
        context = {
            'bus': bus
        }

        return render(request, 'transport/confirm_reactivate_bus.html', context)


@login_required
def bus_detail(request, bus_id):
    """ View detailed information about a specific bus """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can view bus details.')
        return redirect('index')

    bus = get_object_or_404(Bus, id = bus_id)
    students = Student.objects.filter(bus = bus, is_active = True).order_by('name')

    student_count = students.count()
    utilization = (student_count / bus.capacity * 100) if bus.capacity > 0 else 0
    available = bus.capacity - student_count

    context = {
        'bus': bus,
        'students': students,
        'student_count': student_count,
        'utilization': utilization,
        'available': available
    }

    return render(request, 'transport/bus_detail.html', context)


@login_required
def route_list(request):
    """ Display all routes and handle route creation """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can manage routes.')
        return redirect('index')

    # Get all routes
    routes = Route.objects.all().order_by('name')

    # Calculate statistics
    total_routes = routes.count()
    active_routes = routes.filter(is_active = True).count()
    inactive_routes = routes.filter(is_active = False).count()

    # Get stop count for each route
    for route in routes:
        route.stop_count = route.stops.count()
        route.student_count = Student.objects.filter(bus__route_name = route.name, is_active = True).count()

    context = {
        'routes': routes,
        'total_routes': total_routes,
        'active_routes': active_routes,
        'inactive_routes': inactive_routes,
    }

    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        description = request.POST.get('description')

        # Validation
        if not name:
            messages.error(request, 'Please enter a route name.')
            return render(request, 'transport/route_list.html', context)

        # Check for duplicate
        if Route.objects.filter(name = name).exists():
            messages.error(request, f'Route "{name}" already exists.')
            return render(request, 'transport/route_list.html', context)

        try:
            route = Route.objects.create(
                name = name,
                description = description or '',
                is_active = True
            )
            messages.success(request, f'Route "{name}" created successfully!')
            return redirect('route_list')
        except Exception as e:
            messages.error(request, f'Error creating route: {str(e)}')
            return render(request, 'transport/route_list.html', context)

    else:
        return render(request, 'transport/route_list.html', context)


@login_required
def route_detail(request, route_id):
    """ View detailed information about a specific route """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins cam view route details.')
        return redirect('index')

    route = get_object_or_404(Route, id = route_id)
    stops = route.stops.all().order_by('order')

    # Get students on this route
    students = Student.objects.filter(bus__route_name = route.name, is_active = True).order_by('name')

    # Get the bus assigned to this route(if any)
    assigned_bus = Bus.objects.filter(route_name = route.name, is_active = True).first()

    context = {
        'route': route,
        'stops': stops,
        'students': students,
        'student_count': students.count(),
        'assigned_bus': assigned_bus,
    }

    return render(request, 'transport/route_detail.html', context)


@login_required
def edit_route(request, route_id):
    """ Edit an existing route """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can edit the routes.')
        return redirect('index')

    route = get_object_or_404(Route, id = route_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on'

        # Validation
        if not name:
            messages.error(request, 'Please enter a route name.')
            return redirect('edit_route', route_id = route_id)

        # Check for duplicate (excluding current route)
        if Route.objects.filter(name = name).exclude(id = route_id).exists():
            messages.error(request, f'Route "{name}" already exists.')
            return redirect('edit_route', route_id = route_id)

        try:
            route.name = name
            route.description = description
            route.is_active = is_active
            route.save()

            messages.success(request, f'Route "{name}" updated successfully!')
            return redirect('route_list')
        except Exception as e:
            messages.error(request, f'Error updating route: {str(e)}')
            return redirect('edit_route', route_id = route_id)

    context = {
        'route': route
    }

    return render(request, 'transport/edit_route.html', context)


@login_required
def deactivate_route(request, route_id):
    """ Deactivate a route """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can deactivate routes.')
        return redirect('index')

    route = get_object_or_404(Route, id = route_id)

    # Check if students are assigned to this route
    students = Student.objects.filter(bus__route_name = route.name, is_active = True)

    if request.method == 'POST':
        if students.exists():
            messages.warning(request, f'Route "{route.name}" has {students.count()} students assigned.' 'Please reassign students before deactivating.')
            return redirect('route_list')

        notify_parents_about_route_change(
            route,
            students,
            f"Route {route.name} has been deactivated. Please check for alternative arrangements."
        )

        route.is_active = False
        route.save()

        messages.success(request, f'Route "{route.name}" has been deactivated.')
        return redirect('route_list')

    context = {
        'route': route,
        'student_count': students.count()
    }

    return render(request, 'transport/confirm_deactivate_route.html', context)


@login_required
def reactivate_route(request, route_id):
    """ Reactivate a deactivated route """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins acn reactivate routes.')
        return redirect('index')

    route = get_object_or_404(Route, id = route_id)

    if request.method == 'POST':
        route.is_active = True
        route.save()

        messages.success(request, f'Route "{route.name}" has been reactivated.')
        return redirect('route_list')

    context = {
        'route': route
    }

    return render(request, 'transport/confirm_reactivate_route.html', context)


@login_required
def add_stop(request, route_id):
    """ Add a stop to a route """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can add stops.')
        return redirect('index')

    route = get_object_or_404(Route, id = route_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        order = request.POST.get('order')
        pickup_time = request.POST.get('pickup_time')
        dropoff_time = request.POST.get('dropoff_time')

        # Validation
        if not name:
            messages.error(request, 'Please enter the stop name.')
            return redirect('route_detail', route_id = route.id)
        if not address:
            messages.error(request, 'Please enter the stop address.')
            return redirect('route_detail', route_id = route.id)
        if not order:
            messages.error(request, 'Please enter the stop order.')
            return redirect('route_detail', route_id = route.id)

        try:
            order = int(order)
            if order < 1:
                messages.error(request, 'Order must be a positive number.')
                return redirect('route_detail', route_id = route.id)
        except ValueError:
            messages.error(request, 'Order must be a number.')
            return redirect('route_detail', route_id = route.id)

        # Check if order already exists for this route
        if Stop.objects.filter(route = route, order = order).exists():
            messages.error(request, f'Stop order {order} already exists for this route.')
            return redirect('route_detail', route_id = route.id)

        try:
            stop = Stop.objects.create(
                route = route,
                name = name,
                address = address,
                order = order,
                pickup_time = pickup_time or None,
                dropoff_time = dropoff_time or None,
                is_active = True
            )

            messages.success(request, f'Stop "{name}" added to route "{route.name}" !')
        except Exception as e:
            messages.error(request, f'Error adding stop: {str(e)}')
        return redirect('route_detail', route_id = route.id)
    else:
        messages.info(request, 'Please use the form on the route detail page to add stops.')
        return redirect('route_detail', route_id = route.id)


@login_required
def edit_stop(request, stop_id):
    """ Edit a stop """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can edit stops.')
        return redirect('index')

    stop = get_object_or_404(Stop, id = stop_id)
    route = stop.route

    if request.method == 'POST':
        name = request.POST.get('name')
        order = request.POST.get('order')
        address = request.POST.get('address')
        pickup_time = request.POST.get('pickup_time')
        dropoff_time = request.POST.get('dropoff_time')
        is_active = request.POST.get('is_active') == 'on'

        # Validation
        if not name:
            messages.error(request, 'Please enter the stop name.')
            return redirect('route_detail', route_id = route.id)
        if not address:
            messages.error(request, 'Please enter the stop address.')
            return redirect('route_detail', route_id = route.id)
        if not order:
            messages.error(request, 'Please enter the stop order.')
            return redirect('route_detail', route_id = route.id)

        try:
            order = int(order)
            if order < 1:
                messages.error(request, 'Order must be a positive number.')
                return redirect('route_detail', route_id = route.id)
        except ValueError:
            messages.error(request, 'Order must be a number.')
            return redirect('route_detail', route_id = route.id)

        # Check if order already exists(excluding this stop)
        if Stop.objects.filter(route = route, order = order).exclude(id = stop.id).exists():
            messages.error(request, f'Stop order {order} already exists for this route.')
            return redirect('route_detail', route_id = route.id)

        try:
            stop.name = name
            stop.order = order
            stop.address = address
            stop.pickup_time = pickup_time if pickup_time else None
            stop.dropoff_time = dropoff_time if dropoff_time else None
            stop.is_active = is_active
            stop.save()

            messages.success(request, f'Stop "{name}" updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating stop: {str(e)}')
        return redirect('route_detail', route_id = route.id)
    else:
        context = {
            'stop': stop,
            'route': route
        }

        return render(request, 'transport/edit_stop.html', context)


@login_required
def delete_stop(request, stop_id):
    """ Delete a stop """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. ONly admins can delete stops.')
        return redirect('index')

    stop = get_object_or_404(Stop, id = stop_id)
    route = stop.route

    if request.method == 'POST':
        stop_name = stop.name
        stop.delete()
        messages.success(request, f'Stop "{stop.name}" has been removed from route "{route.name}". ')
        return redirect('route_detail', route_id = route.id)

    else:
        context = {
            'stop': stop,
            'route': route
        }

        return render(request, 'transport/confirm_delete_stop.html', context)


def send_notification(recipient, notification_type, subject, message, delivery_method = 'app'):
    """ Helper function to create and send a notification """
    try:
        notification = Notification.objects.create(
            recipient = recipient,
            notification_type = notification_type,
            delivery_method = delivery_method,
            subject = subject,
            message = message,
            is_automatic = True,
            delivered = True,
            read = False
        )
        return notification

    except Exception as e:
        print(f"Error sending notification: {e}")
        return None


def notify_parents_about_bus_change(student, old_bus, new_bus):
    """ Notify parents when their child's bus changes """
    parent = student.parent
    user = parent.user

    subject = f"Bus change for {student.name}"
    message = f"""
    Dear {parent.name},

    Your child {student.name} has been reassigned to a different bus.

    Old Bus: {old_bus.registration if old_bus else 'None'} - {old_bus.route_name if old_bus else 'N/A'}
    New Bus: {new_bus.registration if new_bus else 'None'} - {new_bus.route_name if new_bus else 'N/A'}

    If you have any questions, please contact the school administration.

    Thank you,
    School Transport Management System
    """

    return send_notification(
        recipient = user,
        notification_type = 'bus',
        subject = subject,
        message = message,
        delivery_method = 'app'
    )


def notify_parents_about_route_change(route, affected_students, change_description):
    """ Notify parents when a route changes """
    notifications_sent = 0

    for student in affected_students:
        parent = student.parent
        user = parent.user

        subject = f"Route Change Alert - {route.name}"
        message = f"""
        Dear {parent.name},

        This is to inform you that there has been a change to the transport route for your child {student.name}.

        Route: {route.name}
        Change: {change_description}

        The updated route information is available in your dashboard.

        If you have any questions, please contact the school administration.

        Thank you,
        School Transport Management System
        """

        notification = send_notification(
            recipient = user,
            notification_type = 'route',
            subject = subject,
            message = message,
            delivery_method = 'app'
        )

        if notification:
            notifications_sent += 1

    return notifications_sent


def notify_parents_about_new_student(student):
    """ Notify parents when their child is added to the system """
    parent = student.parent
    user = parent.user

    subject = f"Welcome! {student.name} has been registered"
    message = f"""
    Dear {parent.name},

    This is to confirm that your child {student.name} has been successfully registered in the School Transport Management System.

    Student Details:
    - Name: {student.name}
    - Grade: {student.grade}
    - Bus: {student.bus.registration} - {student.bus.route_name}
    - Pickup: {student.pick_up_location}
    - Dropoff: {student.drop_off_location}

    You can track your child's transport progress through your parent dashboard.

    Thank you,
    School Transport Management System
    """

    return send_notification(
        recipient = user,
        notification_type = 'general',
        subject = subject,
        message = message,
        delivery_method = 'app'
    )


def notify_parents_about_new_bus(student, bus):
    """ Notify parents when their child is assigned to a new bus """
    parent = student.parent
    user = parent.user

    subject = f"Bus Assignment for {student.name}"
    message = f"""
    Dear {parent.name}

    Your child {student.name} has been assigned to a transport bus.

    Bus Details:
    - Registration: {bus.registration}
    - Driver: {bus.driver_name}
    - Route: {bus.route_name}
    - Capacity: {bus.capacity}

    You can track your child's transport progress through your parent dashboard.

    Thank you,
    School Transport Management System
    """

    return send_notification(
        recipient = user,
        notification_type = 'bus',
        subject = subject,
        message = message,
        delivery_method = 'app',
    )


@login_required
def parent_notifications(request):
    """ View for parent to see their notifications """
    if request.user.user_type != 'parent':
        messages.error(request, 'Access denied.')
        return redirect('index')

    notifications = Notification.objects.filter(recipient = request.user).order_by('-created_at')

    # Mark all as read
    unread_count = notifications.filter(read = False).count()
    total_count = notifications.count()
    read_count = total_count - unread_count

    context = {
        'notifications': notifications,
        'unread_count': unread_count,
        'read_count': read_count,
        'total_count': total_count
    }

    return render(request, 'transport/parent_notifications.html', context)


@login_required
def notification_detail(request, notification_id):
    """ View a specific notification """
    notification = get_object_or_404(Notification, id = notification_id, recipient = request.user)

    if not notification.read:
        notification.read = True
        notification.save()

    context = {
        'notification': notification
    }

    return render(request, 'transport/notification_detail.html', context)


@login_required
def mark_all_notifications_read(request):
    """ Mark all notifications as read """
    if request.user.user_type != 'parent':
        messages.error(request, 'Access denied.')
        return redirect('index')

    updated = Notification.objects.filter(recipient = request.user, read = False).update(read = True)

    messages.success(request, f'All notifications marked as read ({updated} updated).')
    return redirect('parent_notifications')


@login_required
def mark_notification_read(request, notification_id):
    """ Mark a single notification as read. """
    notification = get_object_or_404(Notification, id = notification_id, recipient = request.user)

    notification.read = True
    notification.save()

    messages.success(request, 'Notification marked as read.')
    return redirect('parent_notifications')

@login_required
def manage_attendance(request):
    """ Central location to manage the models """
    # Only allow assitants
    if request.user.user_type != 'assistant':
        messages.error(request, 'Access denied. You are not an admin.')
        return redirect('index')

    return render(request, 'transport/manage_attendance.html')


@login_required
def assistant_attendance(request):
    """
    View for assistants to recored attendance for their bus.
    Shows today's students and allows marking pickup/dropoff.
    """
    if request.user.user_type != 'assistant':
        messages.error(request, 'Access denied. Only assistants can record attendance.')
        return redirect('index')

    # Get the assistant's profile
    try:
        assistant = request.user.assistant_profile

        if not assistant.bus:
            messages.error(request, 'You have not been assigned to a bus yet.')
            return redirect('index')
    except Assistant.DoesNotExist:
        messages.error(request, 'Assistant profile not found.')
        return redirect('index')

    bus = assistant.bus
    today = timezone.now().date()

    # Get all students on this bus
    students = Student.objects.filter(bus = bus, is_active = True).order_by('name')

    # Create a list of student data with their attendance record
    student_attendance_data = []

    for student in students:
        # Get today's attendance record for this student
        try:
            record = Attendance.objects.get(student = student, date = today)
            has_record = True
            status = record.status
            status_display = record.get_status_display()
            is_picked_up = record.is_picked_up() if hasattr(record, 'is_picked_up') else status in ['picked_up', 'dropped_off']
            is_absent = record.is_absent() if hasattr(record, 'is_absent') else status == 'absent'
            is_dropped_off = record.is_dropped_off() if hasattr(record, 'is_dropped_off') else status == 'dropped_off'
            pickup_time = record.pickup_time
            dropoff_time = record.dropoff_time
            record_id = record.id
        except Attendance.DoesNotExist:
            has_record = False
            status = 'Pending'
            status_display = 'Pending'
            is_picked_up = False
            is_absent = False
            is_dropped_off = False
            pickup_time = None
            dropoff_time = None
            record_id = None

        student_attendance_data.append({
            'student': student,
            'record': record if has_record else None,
            'has_record': has_record,
            'status': status,
            'status_display': status_display,
            'is_picked_up': is_picked_up,
            'is_absent': is_absent,
            'is_dropped_off': is_dropped_off,
            'pickup_time': pickup_time,
            'dropoff_time':  dropoff_time,
            'record_id': record_id,
        })

    # Statistics
    total_students = students.count()
    picked_up = len([s for s in student_attendance_data if s['is_picked_up']])
    dropped_off = len([s for s in student_attendance_data if s['is_dropped_off']])
    absent = len([s for s in student_attendance_data if s['is_absent']])
    pending = total_students - picked_up - absent

    context = {
        'bus': bus,
        'student_attendance_data': student_attendance_data,
        'today': today,
        'total_students': total_students,
        'picked_up': picked_up,
        'dropped_off': dropped_off,
        'absent': absent,
        'pending': pending,
        'assistant': assistant,
    }
    return render(request, 'transport/assistant_attendance.html', context)


@login_required
def mark_attendance(request):
    """
    AJAX endpoint for marking student attendance.
    Handles pickup, dropoff, absent and late.
    """
    if request.user.user_type != 'assistant':
        return JsonResponse({
            'error': 'Access denied'}, status = 403
            )

    if request.method != 'POST':
        return JsonResponse({
            'error': 'Invalid request'}, status = 400
            )

    student_id = request.POST.get('student_id')
    action = request.POST.get('action')
    notes = request.POST.get('notes', '')

    if not student_id:
        return JsonResponse({
            'error': 'Missing field for student ID'}, status = 400
            )

    if not action:
        return JsonResponse({
            'error': 'Missing field for action'}, status = 400
            )

    try:
        student = Student.objects.get(id = student_id)
        assistant = request.user.assistant_profile

        # Verify student is on assistant's bus
        if student.bus != assistant.bus:
            return JsonResponse({
                'error': 'Student not on your bus'}, status = 403
                )

        today = timezone.now().date()
        attendance, created = Attendance.objects.get_or_create(
            student = student,
            date = today,
            defaults = {
                'bus': student.bus,
                'assistant': assistant,
                'recorded_by': request.user,
                'last_modified_by': request.user,
                'status': 'pending'
            }
        )

        # Mark the appropriate status
        if action == 'pickup':
            attendance.status = 'picked_up'
            attendance.pickup_time = timezone.now()
            if notes:
                attendance.notes = notes
            attendance.recorded_by = request.user
            attendance.last_modified_by = request.user
            attendance.save()

            send_pickup_notification(student, attendance)
            message = f"{student.name} marked as picked up"

        elif action == 'dropoff':
            if not attendance.pickup_time:
                return JsonResponse({
                    'error': 'Student was not picked up'}, status = 400
                    )
            attendance.status = 'dropped_off'
            attendance.dropoff_time = timezone.now()
            if notes:
                attendance.notes = notes
            attendance.last_modified_by = request.user
            attendance.save()

            send_dropoff_notification(student, attendance)
            message = f"{student.name} marked as dropped off"

        elif action == 'absent':
            attendance.status = 'absent'
            if notes:
                attendance.notes = notes
            attendance.recorded_by = request.user
            attendance.last_modified_by = request.user
            attendance.save()

            send_absent_notification(student, attendance)
            message = f"{student.name} marked as absent"

        elif action == 'late':
            attendance.status = 'late'
            attendance.pickup_time = timezone.now()
            if notes:
                attendance.notes = notes
            attendance.recorded_by = request.user
            attendance.last_modified_by = request.user
            attendance.save()

            send_late_notification(student, attendance)
            message = f"{student.name} marked as late"

        else:
            return JsonResponse({
                'error': 'Invalid action'}, status = 400
                )

        return JsonResponse({
            'success': True,
            'message': message,
            'status': attendance.status,
            'pickup_time': attendance.pickup_time.strftime('%I:%M %p') if attendance.pickup_time else None,
            'dropoff_time': attendance.dropoff_time.strftime('%I:%M %p') if attendance.dropoff_time else None,
            'is_picked_up': attendance.status in ['picked_up', 'dropped_off'],
            'is_dropped_off': attendance.status == 'dropped_off',
            'is_absent': attendance.status == 'absent',
            'is_late': attendance.status == 'late'
        })

    except Student.DoesNotExist:
        return JsonResponse({
            'error': 'Student not found'}, status = 404
            )
    except Assistant.DoesNotExist:
        return JsonResponse({
            'error': 'Assistant profile not found'}, status = 404
            )
    except Exception as e:
        return JsonResponse({
            'error': str(e)}, status = 500
            )


@login_required
def reset_attendance(request):
    """ Reset attendance for a specific student """
    if request.user.user_type != 'assistant':
        return JsonResponse({
            'error': 'Access denied'}, status = 403
        )

    if request.method != 'POST':
        return JsonResponse({
            'error': 'Invalid request method'}, status = 400
        )

    student_id = request.POST.get('student_id')

    if not student_id:
        return JsonResponse({
            'error': 'Student ID required'}, status = 400
        )

    try:
        student = Student.objects.get(id = student_id)
        assistant = request.user.assistant_profile

        # Verify student is on assistant's bus
        if student.bus != assistant.bus:
            return JsonResponse({
                'error': 'Student not on your bus'}, status = 403
            )

        today = timezone.now().date()

        # Delete today's attendance record
        deleted_count, _ = Attendance.objects.filter(student = student, date = today).delete()

        return JsonResponse({
            'success': True,
            'message': f'Attendance reset for {student.name}',
            'deleted': deleted_count > 0
        })
    except Student.DoesNotExist:
        return JsonResponse({
            'error': 'Student not found'}, status = 404
        )
    except Exception as e:
        return JsonResponse({
            'error': str(e)}, status = 500
        )


@login_required
def manage_payment(request):
    """ Central location to manage the models """
    # Only allow assitants
    if request.user.user_type != 'parent':
        messages.error(request, 'Access denied. You are not a parent.')
        return redirect('index')

    return render(request, 'transport/manage_payment.html')


@login_required
def parent_attendance(request):
    """
    View for parents to track their children's attendance.
    Shows all children and their current location.
    """
    if request.user.user_type != 'parent':
        messages.error(request, 'Access denied. Only parents can view attendance.')
        return redirect('index')

    try:
        parent = request.user.parent_profile
    except Parent.DoesNotExist:
        messages.error(request, 'Parent profile not found')
        return redirect('index')

    children = parent.children.filter(is_active = True).order_by('name')
    today = timezone.now().date()

    # Initialize counters
    total_children = children.count()
    absent_count = 0
    pending_count = 0
    picked_up_count = 0

    # Get today's attendance for each child
    attendance_data = []

    for child in children:
        try:
            record = Attendance.objects.get(student = child, date = today)

            # Count statuses
            if record.status == 'picked_up':
                picked_up_count += 1
            elif record.status == 'absent':
                absent_count += 1
            elif record.status == 'pending':
                pending_count += 1

            status = record.status
            pickup_time = record.pickup_time
            dropoff_time = record.dropoff_time
            has_record = True
        except Attendance.DoesNotExist:
            status = 'pending'
            pickup_time = None
            dropoff_time = None
            has_record = False
            pending_count += 1

        attendance_data.append({
            'student': child,
            'status': status,
            'pickup_time': pickup_time,
            'dropoff_time': dropoff_time,
            'has_record': has_record,
            'bus': child.bus,
            'grade': child.grade,
        })

    context = {
        'children': attendance_data,
        'today': today,
        'parent': parent,
        'total_children': total_children,
        'absent_count': absent_count,
        'pending_count': pending_count,
        'picked_up_count': picked_up_count
    }

    return render(request, 'transport/parent_attendance.html', context)


@login_required
def system_overview(request):
    """ Central location to manage the models """
    # Only allow assitants
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. You are not a admin.')
        return redirect('index')
    else:
        context = {
            'total_students': Student.objects.count(),
            'total_parents': Parent.objects.count(),
            'total_assistants': Assistant.objects.count(),
            'total_buses': Bus.objects.count()
        }

    return render(request, 'transport/system_overview.html', context)


@login_required
def admin_attendance_dashboard(request):
    """
    Admin dashboard for monitoring attendance across the system.
    """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can view the dashboard.')
        return redirect('index')

    today = timezone.now().date()
    start_of_week = today - timedelta(days = today.weekday())
    start_of_month = today.replace(day = 1)

    # Overall statistics for today
    total_students = Student.objects.filter(is_active = True).count()
    today_records = Attendance.objects.filter(date = today)
    picked_up = today_records.filter(status__in = ['picked_up', 'dropped_off']).count()
    dropped_off = today_records.filter(status = 'dropped_off').count()
    absent = today_records.filter(status = 'absent').count()
    late = today_records.filter(status = 'late').count()
    pending = total_students - today_records.count()

    # Statistics by bus
    bus_stats = []

    buses = Bus.objects.filter(is_active = True)

    for bus in buses:
        students_on_bus = Student.objects.filter(bus = bus, is_active = True).count()
        bus_today = Attendance.objects.filter(bus = bus, date = today)
        bus_stats.append({
            'bus': bus,
            'total': students_on_bus,
            'picked_up': bus_today.filter(status__in = ['picked_up', 'dropped_off']).count(),
            'absent': bus_today.filter(status = 'absent').count(),
            'pending': students_on_bus - bus_today.count(),
            'utilization': (bus_today.count() / students_on_bus * 100) if students_on_bus > 0 else 0,
        })

    # Weekly trends
    weekly_stats = []

    for i in range(7):
        date = start_of_week + timedelta(days = i)
        if date <= today:
            day_records = Attendance.objects.filter(date = date)
            weekly_stats.append({
                'date': date,
                'picked_up': day_records.filter(status__in = ['picked_up', 'dropped_off']).count(),
                'absent': day_records.filter(status = 'absent').count(),
                'total': Student.objects.filter(is_active = True).count()
            })

    # Recent activity
    recent_activity = Attendance.objects.filter(recorded_at__gte = timezone.now() - timedelta(hours = 24)).order_by('-recorded_at')[:10]

    # Absent students today (for quick action)
    absent_students = today_records.filter(status = 'absent').select_related('student', 'student__parent')

    context = {
        'today': today,
        'total_students': total_students,
        'picked_up': picked_up,
        'dropped_off': dropped_off,
        'absent': absent,
        'late': late,
        'pending': pending,
        'bus_stats': bus_stats,
        'weekly_stats': weekly_stats,
        'recent_activity': recent_activity,
        'absent_students': absent_students,
        'start_of_week': start_of_week,
        'stat_of_month': start_of_month,
    }

    return render(request, 'transport/admin_attendance.html', context)


@login_required
def attendance_detail(request, attendance_id):
    """
    View detailed information about a specific attendance record.
    """

    attendance = get_object_or_404(Attendance, id = attendance_id)

    # Check permissions
    if request.user.user_type == 'parent':
        try:
            parent = request.user.parent_profile
            if attendance.student not in parent.children.all():
                messages.error(request, 'Access denied. This is not your child.')
                return redirect('parent_attendance')
        except Parent.DoesNotExist:
            messages.error(request, 'Parent profile not found.')
            return redirect('index')

    elif request.user.user_type == 'assistant':
        try:
            assistant = request.user.assistant_profile
            if attendance.bus != assistant.bus:
                messages.error(request, 'Access denied. This is not your bus.')
                return redirect('assistant_attendance')
        except Assistant.DoesNotExist:
            messages.error(request, 'Assistant profile not found.')
            return redirect('index')

    # Get all records for this student
    all_student_records = Attendance.objects.filter(student = attendance.student)
    student_records = all_student_records.order_by('-date')[:30]

    total_records = all_student_records.count()

    days_absent = all_student_records.filter(status = 'absent').count()
    dropped_off = all_student_records.filter(status = 'dropped_off').count()
    picked_up = all_student_records.filter(status = 'picked_up').count()

    days_present = picked_up + dropped_off

    context = {
        'attendance': attendance,
        'student_records': student_records,
        'total_records': total_records,
        'days_present': days_present,
        'days_absent': days_absent,
        'timeline': attendance.get_formatted_timeline()
    }

    return render(request, 'transport/attendance_detail.html', context)


@login_required
def attendance_reports(request):
    """
    Generate and view attendance reports.
    """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can view reports.')
        return redirect('index')

    # Get filter parameters - ✅ Use GET method
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    bus_id = request.GET.get('bus')
    status_filter = request.GET.get('status')

    # Default to this month
    if not date_from:
        date_from = datetime.now().date().replace(day=1).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.now().date().strftime('%Y-%m-%d')

    # ✅ Build query FIRST
    records = Attendance.objects.all()

    # Apply filters
    if date_from:
        records = records.filter(date__gte=date_from)
    if date_to:
        records = records.filter(date__lte=date_to)
    if bus_id:
        records = records.filter(bus_id=bus_id)
    if status_filter:
        records = records.filter(status=status_filter)

    # ✅ Now calculate ALL statistics from the filtered records
    # Count by status
    late = records.filter(status='late').count()
    picked_up = records.filter(status='picked_up').count()
    dropped_off = records.filter(status='dropped_off').count()
    absent = records.filter(status='absent').count()
    pending = records.filter(status='pending').count()

    # Completed = picked_up + dropped_off
    completed = picked_up + dropped_off

    # Total records
    total_records = records.count()

    # Select related fields for display
    records = records.select_related('student', 'bus', 'student__parent')

    # Summary statistics by status
    status_summary = records.values('status').annotate(count=Count('status'))

    # Add status display names
    status_choices = dict(Attendance.ATTENDANCE_STATUS)
    for item in status_summary:
        item['get_status_display'] = status_choices.get(item['status'], item['status'])

    # Group by bus
    bus_summary = records.values('bus__registration', 'bus__route_name').annotate(
        total=Count('id'),
        picked_up_count=Count('id', filter=Q(status='picked_up')),
        dropped_off_count=Count('id', filter=Q(status='dropped_off')),
        absent_count=Count('id', filter=Q(status='absent')),
        late_count=Count('id', filter=Q(status='late')),
        pending_count=Count('id', filter=Q(status='pending')),
    ).order_by('-total')

    # Group by date
    date_summary = records.values('date').annotate(
        total=Count('id'),
        picked_up_count=Count('id', filter=Q(status='picked_up')),
        dropped_off_count=Count('id', filter=Q(status='dropped_off')),
        absent_count=Count('id', filter=Q(status='absent')),
        late_count=Count('id', filter=Q(status='late')),
    ).order_by('-date')

    # Get all buses for filter dropdown
    buses = Bus.objects.filter(is_active=True)

    context = {
        'records': records[:500],
        'total_records': total_records,
        'completed': completed,
        'picked_up': picked_up,
        'dropped_off': dropped_off,
        'absent': absent,
        'late': late,
        'pending': pending,
        'status_summary': status_summary,
        'bus_summary': bus_summary,
        'date_summary': date_summary,
        'buses': buses,
        'date_from': date_from,
        'date_to': date_to,
        'selected_bus': bus_id,
        'selected_status': status_filter,
    }

    return render(request, 'transport/attendance_reports.html', context)


@login_required
def edit_attendance(request, attendance_id):
    """
    Edit an existing attendance record (admin only)
    """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can edit attendance.')
        return redirect('index')

    attendance = get_object_or_404(Attendance, id = attendance_id)

    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')

        if not status:
            messages.error(request, 'Please select a status')
            return redirect('edit_attendance', attendance_id = attendance_id)

        attendance.status = status
        attendance.notes = notes
        attendance.last_modified_by = request.user
        attendance.save()

        messages.success(request, f'Attendance for {attendance.student.name} updated successfully.')
        return redirect('attendance_detail', attendance_id = attendance_id)

    context = {
        'attendance': attendance,
        'status_choices': Attendance.ATTENDANCE_STATUS,
    }

    return render(request, 'transport/edit_attendance.html', context)


def send_pickup_notification(student, attendance):
    """ Send notification to parent when student is picked up """
    try:
        parent = student.parent

        if not parent:
            print(f"No parent found for student: {student.name}")
            return

        if not parent.user:
            print(f"No user found for parent: {parent.name}")
            return

        message = f"""
        {student.name} has been picked up!

        Time: {attendance.pickup_time.strftime('%I:%M %p')}
        Bus: {student.bus.registration}
        Pickup Location: {student.pick_up_location}

        Your child is on the way to school.
        """

        # Send in-app notification
        Notification.objects.create(
            recipient = parent.user,
            notification_type = 'attendance',
            delivery_method = 'app',
            subject = f'{student.name} Picked up',
            message = message,
            is_automatic = True,
            delivered = True
        )
        print(f"Pickup notification sent to {parent.user.username}")

    except Exception as e:
        print(f"Error sending pickup notification: {e}")


def send_dropoff_notification(student, attendance):
    """ Send notification to parent when student is dropped off """
    try:
        parent = student.parent

        if not parent:
            print(f"No parent found for student: {student.name}")
            return

        if not parent.user:
            print(f"No user found for parent: {parent.name}")
            return

        message = f"""
        {student.name} has arrived at school!

        Time: {attendance.dropoff_time.strftime('%I:%M %p')}
        Bus: {student.bus.registration} - {student.bus.route_name}
        Dropoff Location: {student.drop_off_location}

        Your child has safely arrived.
        """

        Notification.objects.create(
            recipient = parent.user,
            notification_type = 'attendance',
            delivery_method = 'app',
            subject = f'{student.name} Arrived at School',
            message = message,
            is_automatic = True,
            delivered = True
        )
        print(f"Dropoff notification sent to {parent.user.username}")

    except Exception as e:
        print(f"Error sending dropoff notification: {e}")


def send_absent_notification(student, attendance):
    """ Send notification to parent when student is absent """
    try:
        parent = student.parent
        if not parent :
            print(f"No parent found for student: {student.name}")
            return

        if not parent.user:
            print(f"No user found for parent: {parent.name}")
            return

        message = f"""
        {student.name} was marked absent today.

        Date: {attendance.date.strftime('%A, %B %d, %Y')}
        Please contact the school for more information.
        """

        Notification.objects.create(
            recipient = parent.user,
            notification_type = 'attendance',
            delivery_method = 'app',
            subject = f'{student.name} Absent Today',
            message = message,
            is_automatic = True,
            delivered = True,
            read = False
        )
        print(f"Absent notification sent to {parent.user.username}")

    except Exception as e:
        print(f"Error sending absent notification: {e}")


def send_late_notification(student, attendance):
    """ Send notification to parent when student is late """
    try:
        parent = student.parent

        if not parent:
            print(f"No parent found for student: {student.name}")
            return

        if not parent.user:
            print(f"No user found for parent: {parent.name}")
            return

        message = f"""
        {student.name} was late today.

        Time: {attendance.pickup_time.strftime('%I:%M %p')}
        Please ensure your child is ready earlier tomorrow.
        """

        Notification.objects.create(
            recipient = parent.user,
            notification_type = 'attendance',
            delivery_method = 'app',
            subject = f'{student.name} Late Today',
            message = message,
            is_automatic = True,
            delivered = True
        )
        print(f" Late notification sent to {parent.user.username}")

    except Exception as e:
        print(f"Error sending late notification: {e}")


@login_required
def parent_list(request):
    """
    Display all parents with their children.
    Handles adding new parents.
    """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can manage parents.')
        return redirect('index')

    # Get all parents with student count
    parents = Parent.objects.all().annotate(child_count = Count('children')).order_by('name')

    # Calculate statistsics
    total_parents = parents.count()
    active_parents = parents.filter(user__is_active = True).count()
    inactive_parents = parents.filter(user__is_active = False).count()
    parents_with_children = parents.filter(child_count__gt = 0).count()

    context = {
        'parents': parents,
        'total_parents': total_parents,
        'active_parents': active_parents,
        'inactive_parents': inactive_parents,
        'parents_with_children': parents_with_children
    }

    # Handle POST request
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        home_address = request.POST.get('home_address')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validation
        if not full_name:
            messages.error(request, 'The full name is required.')
            return render(request, 'transport/parent_list.html', context)
        if not username:
            messages.error(request, 'The username is required.')
            return render(request, 'transport/parent_list.html', context)
        if not email:
            messages.error(request, 'The email is required.')
            return render(request, 'transport/parent_list.html', context)
        if not phone_number:
            messages.error(request, 'The phone_number is required.')
            return render(request, 'transport/parent_list.html', context)
        if not home_address:
            messages.error(request, 'The home_address is required.')
            return render(request, 'transport/parent_list.html', context)
        if not password:
            messages.error(request, 'The password is required.')
            return render(request, 'transport/parent_list.html', context)
        if not confirm_password:
            messages.error(request, 'Need to confirm your password.')
            return render(request, 'transport/parent_list.html', context)

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'transport/parent_list.html', context)

        try:
            # Create user
            user = User.objects.create_user(
                username = username,
                email = email,
                password = password
            )
            user.user_type = 'parent'
            user.phone_number = phone_number
            user.is_active = True
            user.save()

            # Create parent profile
            parent = Parent.objects.create(
                user = user,
                name = full_name,
                email = email,
                phone_number = phone_number,
                home_address = home_address
            )

            messages.success(request, f'Parent "{full_name}" added successfully!')
            return redirect('parent_list')

        except IntegrityError:
            messages.error(request, f'Username "{username}" already exists.')
            return render(request, 'trasnport/parent_list.html', context)

        except Exception as e:
            messages.error(request, f'Error adding parent: {str(e)}')
            return render(request, 'transport/parent_list.html', context)

    else:
        return render(request, 'transport/parent_list.html', context)


@login_required
def parent_detail(request, parent_id):
    """
    View detailed information about a specific parent.
    """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can view parent details.')
        return redirect('index')

    parent = get_object_or_404(Parent, id = parent_id)
    children = parent.children.filter(is_active = True).order_by('name')

    # Get statistics
    child_count = children.count()
    active_children = children.filter(is_active = True).count()

    # Get attendance stats for children
    for child in children:
        today_records = Attendance.objects.filter(
            student=child,
            date=timezone.now().date()
        )

        child.today_status = (
            today_records.first().status
            if today_records.exists()
            else 'pending'
        )

        child.total_records = child.attendance_records.count()

    context = {
        'parent': parent,
        'children': children,
        'child_count': child_count,
        'active_children': active_children
    }

    return render(request, 'transport/parent_detail.html', context)


@login_required
def edit_parent(request, parent_id):
    """ Edit an existing parent's information """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. ONly admins can edit parents.')
        return redirect('index')

    parent = get_object_or_404(Parent, id = parent_id)
    user = parent.user

    if request.method == 'POST':
        # Get form data
        full_name = request.POST.get('full_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        home_address = request.POST.get('home_address')
        is_active = request.POST.get('is_active') == 'on'

        # Validation
        if not full_name:
            messages.error(request, 'The full name is required.')
            return render(request, 'transport/edit_parent.html', {'parent': parent})
        if not username:
            messages.error(request, 'The username is required.')
            return render(request, 'transport/edit_parent.html', {'parent': parent})
        if not email:
            messages.error(request, 'The email is required.')
            return render(request, 'transport/edit_parent.html', {'parent': parent})
        if not phone_number:
            messages.error(request, 'The phone number is required.')
            return render(request, 'transport/edit_parent.html', {'parent': parent})
        if not home_address:
            messages.error(request, 'The home address is required.')
            return render(request, 'transport/edit_parent.html', {'parent': parent})

        try:
            # Update user
            if user.username != username:
                # Check if new username is taken
                if User.objects.filter(username = username).exclude(id = user.id).exists():
                    messages.error(request, f'Username "{username}" already exists.')
                    return redirect(request, 'transport/edit_parent.html', {'parent': parent})
                user.username = username

            user.email = email
            user.phone_number = phone_number
            user.is_active = is_active
            user.save()

            # Update parent profile
            parent.name = full_name
            parent.email = email
            parent.phone_number = phone_number
            parent.home_address = home_address
            parent.save()

            messages.success(request, f'Parent "{full_name}" updated successfully!')
            return redirect('parent_list')

        except Exception as e:
            messages.error(request, f'Error updating parent: {str(e)}')
            return render(request, 'transport/edit_parent.html', {'parent': parent})

    else:
        context = {
            'parent': parent,
            'user': user
        }

        return render(request, 'transport/edit_parent.html', context)


@login_required
def deactivate_parent(request, parent_id):
    """ Deactivate a parent """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. only admins can deactivate parents.')
        return redirect('index')

    parent = get_object_or_404(Parent, id = parent_id)
    user = parent.user

    # Check if parent has active children
    active_children = parent.children.filter(is_active = True)

    if request.method == 'POST':
        if active_children.exists():
            messages.warning(request, f'Parent "{parent.name}" has {active_children.count()} active children. ''Please reassign or deactivate children first.')
            return redirect('parent_list')

        user.is_active = False
        user.save()

        messages.success(request, f'Parent "{parent.name}" has been deactivated.')
        return redirect('parent_list')
    else:
        context = {
            'parent': parent,
            'active_children': active_children,
            'child_count': active_children.count()
        }

        return render(request, 'transport/confirm_deactivate_parent.html', context)


@login_required
def reactivate_parent(request, parent_id):
    """ Reactivate a deactivated parent """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can reactivate parents.')
        return redirect('index')

    parent = get_object_or_404(Parent, id = parent_id)
    user = parent.user

    if request.method == 'POST':
        user.is_active = True
        user.save()

        messages.success(request, f'Parent "{parent.name}" has been reactivated.')
        return redirect('parent_list')
    else:
        context = {
            'parent': parent
        }

        return render(request, 'transport/confirm_reactivate_parent.html', context)


@login_required
def assistant_list(request):
    """
    Display all assistants with their bus assignments and student.
    Handles adding new assistants.
    """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can manage assistants.')
        return redirect('index')

    # Get all assistants with student count on their bus
    assistants = Assistant.objects.all().annotate(student_count = Count('bus__students', filter = Q(bus__students__is_active = True))).order_by('name')

    # Calculate statistics
    total_assistants = assistants.count()
    active_assistants = assistants.filter(is_active = True).count()
    inactive_assistants = assistants.filter(is_active = False).count()
    assigned_assistants = assistants.filter(bus__isnull = False).count()
    unassigned_assistants = assistants.filter(bus__isnull = True).count()

    # Get all buses from dropdown
    buses = Bus.objects.filter(is_active = True)

    context = {
        'assistants': assistants,
        'total_assistants': total_assistants,
        'active_assistants': active_assistants,
        'inactive_assistants': inactive_assistants,
        'assigned_assistants': assigned_assistants,
        'unassigned_assistants': unassigned_assistants,
        'buses': buses
    }

    # Handle POST request
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        bus_id = request.POST.get('bus')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validation
        if not full_name:
            messages.error(request, 'The full name is required.')
            return render(request, 'transport/assistant_list.html', context)
        if not username:
            messages.error(request, 'The username is required.')
            return render(request, 'transport/assistant_list.html', context)
        if not email:
            messages.error(request, 'The email is required.')
            return render(request, 'transport/assistant_list.html', context)
        if not phone_number:
            messages.error(request, 'The phone_number is required.')
            return render(request, 'transport/assistant_list.html', context)
        if not password:
            messages.error(request, 'The password is required.')
            return render(request, 'transport/assistant_list.html', context)
        if not confirm_password:
            messages.error(request, 'Please confirm your password.')
            return render(request, 'transport/assistant_list.html', context)

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'transport/assistant_list.html', context)

        try:
            # Create user
            user = User.objects.create_user(
                username = username,
                email = email,
                password = password
            )
            user.user_type = 'assistant'
            user.phone_number = phone_number
            user.is_active = True
            user.save()

            # Get bus is selected
            bus_obj = None
            if bus_id:
                try:
                    bus_obj = Bus.objects.get(id = bus_id)
                except Bus.DoesNotExist:
                    messages.warning(request, 'Selected bus not found. Assistant created without bus assignment.')

            # Create assistant profile
            assistant = Assistant.objects.create(
                user = user,
                name = full_name,
                phone_number = phone_number,
                email = email,
                bus = bus_obj,
                is_active = True
            )

            messages.success(request, f'Assistant "{full_name}" added successfully!')
            return redirect('assistant_list')
        except IntegrityError:
            messages.error(request, f'Username "{username}" already exists.')
            return render(request, 'transport/assistant_list.html', context)
        except Exception as e:
            messages.error(request, f'Error adding assistant: {str(e)}')
            return render(request, 'transport/assistant_list.html', context)
    else:
        return render(request, 'transport/assistant_list.html', context)


@login_required
def assistant_detail(request, assistant_id):
    """
    View detailed information about a specific assistant.
    """
    if request.user.user_type != 'admin':
        messages.error(request, 'Acess denied. Only admins can view assistant details')
        return redirect('index')

    assistant = get_object_or_404(Assistant, id = assistant_id)

    # Get students on assistant's bus
    students_on_bus = []

    if assistant.bus:
        students_on_bus = Student.objects.filter(bus = assistant.bus, is_active = True).order_by('name')

    # Get attendance stats
    today = timezone.now().date()
    today_attendance = Attendance.objects.filter(assistant = assistant, date = today) if assistant else None

    context = {
        'assistant': assistant,
        'students_on_bus': students_on_bus,
        'student_count': len(students_on_bus),
        'today_attendance': today_attendance,
        'has_bus': assistant.bus is not None
    }

    return render(request, 'transport/assistant_detail.html', context)


@login_required
def edit_assistant(request, assistant_id):
    """
    Edit an existing assistant's information
    """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can edit assistants.')
        return redirect('index')

    assistant = get_object_or_404(Assistant, id = assistant_id)
    user = assistant.user

    # Get all active buses for dropdown
    buses = Bus.objects.filter(is_active = True)

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        bus_id = request.POST.get('bus')
        is_active = request.POST.get('is_active') == 'on'

        # Validation
        if not full_name:
            messages.error(request, 'The full name is required.')
            return render(request, 'transport/edit_assistant.html', {
                'assistant': assistant,
                'buses': buses,
            })
        if not username:
            messages.error(request, 'The username is required.')
            return render(request, 'transport/edit_assistant.html', {
                'assistant': assistant,
                'buses': buses,
            })
        if not email:
            messages.error(request, 'The email is required.')
            return render(request, 'transport/edit_assistant.html', {
                'assistant': assistant,
                'buses': buses,
            })
        if not phone_number:
            messages.error(request, 'The phone number is required.')
            return render(request, 'transport/edit_assistant.html', {
                'assistant': assistant,
                'buses': buses,
            })

        try:
            # Update user
            if user.username != username:
                # Check if new username is taken
                if User.objects.filter(username = username).exclude(id = user.id).exists():
                    messages.error(request, f'Username "{username}" already exists.')
                    return render(request, 'transport/edit_assistant.html', {
                        'assistant': assistant,
                        'buses': buses
                    })
                user.username = username

            user.email = email
            user.phone_number = phone_number
            user.is_active = is_active
            user.save()

            # Update bus
            bus_obj = None
            if bus_id:
                try:
                    bus_obj = Bus.objects.get(id = bus_id)
                except Bus.DoesNotExist:
                    messages.warning(request, 'Selected bus not found.')

            # Update assistant profile
            assistant.name = full_name
            assistant.email = email
            assistant.phone_number= phone_number
            assistant.bus = bus_obj
            assistant.is_active = is_active
            assistant.save()

            messages.success(request, f'Assistant "{full_name}" udpated successfully!')
            return redirect('assistant_list')

        except Exception as e:
            messages.error(request, f'Error updating assistant: {str(e)}')
            return render(request, 'transport/edit_assistant.html', {
                'assistant': assistant,
                'buses': buses
            })
    else:
        context = {
            'assistant': assistant,
            'user': user,
            'buses': buses
        }

        return render(request, 'transport/edit_assistant.html', context)


@login_required
def deactivate_assistant(request, assistant_id):
    """
    Deactivate an assistant
    """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can deactivate assistants.')
        return redirect('index')

    assistant = get_object_or_404(Assistant, id = assistant_id)
    user = assistant.user

    # Check if assistant has students on their bus
    students_on_bus = []

    if assistant.bus:
        students_on_bus = Student.objects.filter(bus = assistant.bus, is_active = True)

    if request.method == 'POST':
        if students_on_bus:
            messages.warning(request, f'Assistant "{assistant.name}" has {students_on_bus.count()} students on their bus. ''Please reassign students first.')
            return redirect('assistant_list')

        user.is_active = False
        user.save()

        assistant.is_active = False
        assistant.save()

        messages.success(request, f'Assistant "{assistant.name}" has been deactivated.')
        return redirect('assistant_list')

    context = {
        'assistant': assistant,
        'students_on_bus': students_on_bus,
        'student_count': len(students_on_bus)
    }

    return render(request, 'transport/confirm_deactivate_assistant.html', context)


@login_required
def reactivate_assistant(request, assistant_id):
    """ Reactivate a deactivated assistant """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Only admins can reactivate assistants.')
        return redirect('index')

    assistant = get_object_or_404(Assistant, id = assistant_id)
    user = assistant.user

    if request.method == 'POST':
        user.is_active = True
        user.save()

        assistant.is_active = True
        assistant.save()

        messages.success(request, f'Assistant "{assistant.name}" has been reactivated.')
        return redirect('assistant_list')

    context = {
        'assistant': assistant
    }

    return render(request, 'transport/confirm_reactivate_assistant.html', context)


@login_required
def student_attendance_history(request, student_id):
    """ View full attendance history for a soecific student. """
    student = get_object_or_404(Student, id = student_id)

    # Check permissions
    if request.user.user_type == 'parent':
        try:
            parent = request.user.parent_profile
            if student not in parent.children.all():
                messages.error(request, 'Access denied. This is not your child.')
                return redirect('parent_attendance')
        except Parent.DoesNotExist:
            messages.error(request, 'Parent profile not found.')
            return redirect('index')

    # Get all attendance records for this student
    records = student.attendance_records.all().order_by('-date')

    # Calculate statistics
    total_records = records.count()
    present_count = records.filter(status__in = ['picked_up', 'dropped_off']).count()
    absent_count = records.filter(status = 'absent').count()
    late_count = records.filter(status = 'late').count()

    context = {
        'student': student,
        'records': records,
        'total_records': total_records,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count
    }

    return render(request, 'transport/student_attendance_history.html', context)


@login_required
def parent_fee_dashboard(request):
    """ Parent's view of their children's fees. """
    if request.user.user_type != 'parent':
        messages.error(request, 'Access denied. Only parents can view fees.')
        return redirect('index')

    try:
        parent = request.user.parent_profile
    except Parent.DoesNotExist:
        messages.error(request, 'Parent profile not found.')
        return redirect('index')

    # Get all children
    children = parent.children.filter(is_active = True)

    # Get fee data for each child
    child_fee_data = []
    total_balance = Decimal('0.00')

    for child in children:
        fees = Fee.objects.filter(student = child).order_by('-year', '-term')
        total_balance += fees.filter(status__in = ['pending', 'partial', 'overdue']).aggregate(total_balance = Sum('balance'))['total_balance'] or Decimal('0.00')

        # Get latest fee status
        latest_fee = fees.first()

        child_fee_data.append({
            'student': child,
            'latest_fee': latest_fee,
            'fees': fees,
            'total_fees': fees.count(),
            'unpaid_fees': fees.filter(status__in = ['pending', 'partial', 'overdue']).count(),
        })

    # Get recent payment
    payments = Payment.objects.filter(fee__student__parent = parent).order_by('-payment_date')[:10]

    context = {
        'children': child_fee_data,
        'total_balance': total_balance,
        'payments': payments,
        'parent': parent,
    }

    return render(request, 'transport/parent_fee_dashboard.html', context)


@login_required
def fee_detail(request, fee_id):
    """ View details of a specific fee. """
    fee = get_object_or_404(Fee, id = fee_id)

    # Check permissions
    if request.user.user_type == 'parent':
        try:
            parent = request.user.parent_profile
            if fee.student not in parent.children.all():
                messages.error(request, 'Access denied. This is not your child.')
                return redirect('parent_fee_dashboard')
        except Parent.DoesNotExist:
                messages.error(request, 'Parent profile not found.')
                return redirect('index')

    # Get payments for this fee
    payments = fee.payments.all().order_by('-payment_date')

    context = {
        'fee': fee,
        'payments': payments,
        'balance_due': fee.get_balance_due()
    }

    return render(request, 'transport/fee_detail.html', context)


@login_required
def parent_pay_fee(request, fee_id):
    """ Initiate payment for a fee (parent view) """
    if request.user.user_type != 'parent':
        messages.error(request, 'Access denied.')
        return redirect('index')

    fee = get_object_or_404(Fee, id = fee_id)
    parent = request.user.parent_profile

    # Verify parent owns this student
    if fee.student not in parent.children.all():
        messages.error(request, 'Access denied. This is not your child.')
        return redirect('parent_fee_dashboard')

    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        reference_number = request.POST.get('reference_number', '')
        notes = request.POST.get('notes', '')

        try:
            amount = Decimal(amount)
            if amount <= 0:
                messages.error(request, 'Payment amount must be greater than zero.')
                return render(request, 'transport/parent_pay_fee.html', {'fee': fee})

            if amount > fee.get_balance_due():
                messages.error(request, f'Amount cannot exceed balance due: {fee.get_balance_due()}')
                return render(request, 'transport/parent_pay_fee.html', {'fee': fee})

            # Create payment
            payment = Payment.objects.create(
                fee = fee,
                amount = amount,
                payment_method = payment_method,
                reference_number = reference_number,
                payment_date = timezone.now(),
                recorded_by = request.user,
                notes = notes
            )

            # Update fee paid amount
            fee.paid_amount += amount
            fee.save()

            # Send confirmation notification
            send_fee_notification(
                fee.student.parent.user,
                'payment_confirmation',
                fee.student,
                amount,
                fee
            )

            messages.success(request, f'Payment of {amount} recorded successfully!')
            return redirect('fee_detail', fee_id = fee.id)

        except Exception as e:
            messages.error(request, f'Error processing payment: {str(e)}')

    context = {
        'fee': fee,
        'balance_due': fee.get_balance_due()
    }

    return render(request, 'transport/parent_pay_fee.html', context)

