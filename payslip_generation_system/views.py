from django.shortcuts import render, redirect
from django.db import connection
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from .models import Employee, EmployeeAttachment
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect

# Create your views here.
def test(request):
    return render(request, 'test.html')

def index(request):
    return render(request, 'login.html')

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE username = %s AND password = %s",
                [username, password]
            )
            user = cursor.fetchone()

        if user:
            # Successful login
           return JsonResponse({
                'success': True, 
                'message': 'Login successful', 
                'redirect_url': '/dashboard/',
            })
        else:
            # Invalid credentials
            return JsonResponse({
                'success': False, 
                'message': 'Invalid username or password', 
                'redirect_url': '/login/',
            })

    # Handle GET or other methods
    return render(request, 'login.html')

def dashboard(request):
    return render(request, 'dashboard.html')

def add_employee(request):
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        date_hired = request.POST.get('date_hired')
        position = request.POST.get('position')
        education = request.POST.get('educational_attainment')
        birthdate = request.POST.get('birthdate')
        gender = request.POST.get('gender')
        fund_source = request.POST.get('fund_source')
        tax_declaration = request.POST.get('with_tax_declaration')
        salary = request.POST.get('salary')
        eligibility = request.POST.get('eligibility')

        # Handle multiple file uploads
        uploaded_files = request.FILES.getlist('attachments')

        # Create the employee object first
        employee = Employee.objects.create(
            fullname=fullname,
            date_hired=date_hired,
            position=position,
            educational_attainment=education,
            birthdate=birthdate,
            gender=gender,
            fund_source=fund_source,
            tax_declaration=tax_declaration,
            salary=salary,
            eligibility=eligibility
        )

        # Save each file in the "employee_attachments" folder inside the media directory
        for f in uploaded_files:
            # Django will handle saving the file with a random name
            EmployeeAttachment.objects.create(
                employee=employee,  # Associate with the employee
                file=f              # Save the file in the "employee_attachments" folder inside the media directory
            )

        messages.success(request, 'Employee added successfully!')
        return redirect('dashboard')

    return render(request, 'add_emp.html')

def edit_employee(request, emp_id):
    employee = get_object_or_404(Employee, id=emp_id)

    if request.method == "POST":
        # Get form data
        fullname = request.POST.get("fullname")
        position = request.POST.get("position")
        educational_attainment = request.POST.get("educational_attainment")
        birthdate = request.POST.get("birthdate")
        gender = request.POST.get("gender")
        fund_source = request.POST.get("fund_source")
        tax_declaration = request.POST.get("with_tax_declaration")
        salary = request.POST.get("salary")
        eligibility = request.POST.get("eligibility")

        # Update the employee
        employee.fullname = fullname
        employee.position = position
        employee.educational_attainment = educational_attainment
        employee.birthdate = birthdate
        employee.gender = gender
        employee.fund_source = fund_source
        employee.tax_declaration = tax_declaration
        employee.salary = salary
        employee.eligibility = eligibility
        employee.save()

        # Send response back
        messages.success(request, "Employee details updated successfully.")
        return redirect('dashboard')
    
    # Display the employee data in a form
    return render(request, "edit_employee.html", {"employee": employee})

def delete_employee(request, emp_id):
    employee = get_object_or_404(Employee, id=emp_id)

    if request.method == "POST":
        # Delete all associated attachments
        for attachment in employee.attachments.all():
            attachment.delete()  # Delete the file from the storage

        # Now delete the employee
        employee.delete()
        return JsonResponse({"success": True, "message": "Employee deleted successfully!"})

    return JsonResponse({"success": False, "message": "Invalid request method!"})

def employee_data_json(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    queryset = Employee.objects.all()

    if search_value:
        queryset = queryset.filter(
            Q(fullname__icontains=search_value) |
            Q(position__icontains=search_value)
    )

    total_records = queryset.count()

    paginator = Paginator(queryset, length)
    page_number = (start // length) + 1
    page = paginator.get_page(page_number)

    data = []
    for emp in page:
        salary = f"₱{emp.salary:,.2f}"
        
        data.append([
            emp.fullname,
            emp.date_hired.strftime('%Y-%m-%d'),
            emp.position,
            emp.educational_attainment,
            emp.birthdate.strftime('%Y-%m-%d'),
            emp.gender,
            emp.fund_source,
            emp.tax_declaration,
            salary,
            emp.eligibility,
            f"<button class='edit-btn' data-id='{emp.id}'>Edit</button> <button class='delete-btn' data-id='{emp.id}'>Delete</button>"
        ])

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data
    })