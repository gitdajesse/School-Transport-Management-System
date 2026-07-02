from django.shortcuts import render
from .models import User, Parent, Bus, Student, Assistant, Attendance, Notification, RouteAssignment

# Create your views here.
def index(request):
    return render (request, 'transport/index.html')

def register(request):
    return render (request, 'transport/register.html')

def login(request):
    return render (request, 'transport/login.html')

def logout(request):
    pass




