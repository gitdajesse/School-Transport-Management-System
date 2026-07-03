from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect

from .models import User, Parent, Bus, Student, Assistant, Attendance, Notification, RouteAssignment

# Create your views here.
def index(request):
    """ Home page - redirects to appropraite dashboard if logged in """

    return render (request, 'transport/index.html')

def register(request):
    return render (request, 'transport/register.html')

def login(request):
    return render (request, 'transport/login.html')

def logout(request):
    pass


def parent_dashboard(request):
    return render (request, 'transport/parent_dashboard.html')


def assistant_dashboard(request):
    return render (request, 'transport/assistant_dashboard.html')


def admin_dashboard(request):
    return render (request, 'transport/admin_dashboard.html')
