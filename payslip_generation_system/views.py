from django.shortcuts import render, redirect
from django.db import connection
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from .models import Adjustment, Employee, EmployeeAttachment, User
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
import json
from decimal import Decimal
from django.db import connections

from datetime import datetime

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
            request.session['user_id'] = user[0]
            request.session['fullname'] = user[1]
            request.session['user_type'] = user[7] 
            
            if user[7] == 'employee':
                # Redirect to employee dashboard
                return JsonResponse({
                    'success': True, 
                    'message': 'Login successful', 
                    'redirect_url': 'payslip/',
                })
            else:
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
    if(request.session.get('user_type') == 'employee'):
        return render(request, 'payslip.html')
    else:
        return render(request, 'dashboard.html')

def add_employee(request):
    if request.method == 'POST':
        employee_no = request.POST.get('employee_no')
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

        # Check if a user with the same username already exists
        if User.objects.filter(name=fullname).exists():
            messages.error(request, 'A user already exists.')
            return redirect('add_employee_profile')
        
        # Create the employee object first
        employee = Employee.objects.create(
            employee_no=employee_no,
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
            
        fullname_parts = employee.fullname.split()
        if len(fullname_parts) >= 2:
            # Get the first word (firstname) and the last word (lastname)
            firstname = fullname_parts[0]
            lastname = fullname_parts[-1]
            full_name_concatenated = f"{firstname}{lastname}"
        
        User.objects.create(
            name=fullname,
            division=position,
            username=full_name_concatenated,
            password=birthdate,
            type="employee",
            status="1",
        )

        messages.success(request, 'Employee added successfully!')
        return redirect('dashboard')

    with connections['dniis_db'].cursor() as cursor:
        cursor.execute('SELECT * FROM systems_division')
        division = cursor.fetchall()
        
    with connections['dniis_db'].cursor() as cursor:
        cursor.execute('SELECT * FROM systems_section')
        section = cursor.fetchall()
        
    return render(request, 'add_emp.html', {
            'division': division,
            'section': section,
        })

def edit_employee(request, emp_id):
    employee = get_object_or_404(Employee, id=emp_id)

    if request.method == "POST":
        # Get form data
        employee_no = request.POST.get("employee_no")
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
        employee.employee_no = employee_no
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

        # Handle new attachments
        files = request.FILES.getlist('attachments')
        for file in files:
            # Create the EmployeeAttachment object
            EmployeeAttachment.objects.create(employee=employee, file=file)
            
        # Send response back
        messages.success(request, "Employee details updated successfully.")
        return redirect('dashboard')
    
    # Display the employee data in a form
    return render(request, "edit_employee.html", {"employee": employee})

def delete_attachment(request, attachment_id):
    if request.method == "POST":
        attachment = get_object_or_404(EmployeeAttachment, id=attachment_id)
        attachment.delete()
        return JsonResponse({"success": True, "message": "Attachment deleted."})
    return JsonResponse({"success": False, "message": "Invalid request."})

def delete_employee(request, emp_id):
    employee = get_object_or_404(Employee, id=emp_id)

    if request.method == "POST":
        # Delete all associated attachments
        for attachment in employee.attachments.all():
            attachment.delete()  # Delete the file from the storage

        # Delete all adjustments connected to this employee
        Adjustment.objects.filter(employee=employee).delete()
        
        # Now delete the employee
        employee.delete()
        return JsonResponse({"success": True, "message": "Employee deleted successfully!"})

    return JsonResponse({"success": False, "message": "Invalid request method!"})

def employee_data_json(request):
    user_type = request.session['user_type']
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    order_col_index = int(request.GET.get('order[0][column]', 0))
    order_dir = request.GET.get('order[0][dir]', 'asc')

    # Base queryset
    queryset = Employee.objects.all()

    # Section filtering by user_type
    section_map = {
        'preparator_meo_s': 43,
        'preparator_meo_e': 42,
        'preparator_meo_w': 44,
        'preparator_meo_n': 45
    }

    if user_type == 'admin':
        queryset = Employee.objects.all()
    elif user_type in section_map:
        queryset = Employee.objects.filter(section=section_map[user_type])
    else:
        # Return empty response immediately
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        })
        
    # Apply search filter
    if search_value:
        queryset = queryset.filter(
            Q(employee_no__icontains=search_value) |
            Q(fullname__icontains=search_value) |
            Q(position__icontains=search_value) |
            Q(educational_attainment__icontains=search_value) |
            Q(gender__icontains=search_value) |
            Q(fund_source__icontains=search_value) |
            Q(tax_declaration__icontains=search_value) |
            Q(eligibility__icontains=search_value)
        )

    total_records = queryset.count()

    # Ordering logic
    columns = [
        'employee_no', 'fullname', 'date_hired', 'position', 'educational_attainment',
        'birthdate', 'gender', 'fund_source', 'tax_declaration', 'salary', 'eligibility'
    ]
    order_column = columns[order_col_index] if order_col_index < len(columns) else 'date_hired'
    if order_dir == 'desc':
        order_column = f'-{order_column}'
    queryset = queryset.order_by(order_column)

    # Pagination
    paginator = Paginator(queryset, length)
    page_number = (start // length) + 1
    page = paginator.get_page(page_number)

    data = []
    for emp in page:
        salary = f"₱{emp.salary:,.2f}"
        data.append([
            emp.employee_no,
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
            f"""
            <button class='adjustments-btn btn btn-warning btn-sm view-btn' title='Adjustments' data-id='{emp.id}'>
                <i class="fas fa-list"></i>
            </button> 
            <button class='btn btn-info btn-sm view-btn' data-id='{emp.id}' title='Information' data-toggle='modal' data-target='#viewModal'>
                <i class="fas fa-eye"></i>
            </button> 
            <button class='edit-btn btn btn-primary btn-sm view-btn' title='Edit' data-id='{emp.id}'>
                <i class="fas fa-pen"></i>
            </button> 
            <button class='delete-btn btn btn-danger btn-sm view-btn' title='Delete' data-id='{emp.id}'>
                <i class="fas fa-trash"></i>
            </button>
            """
        ])

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data
    })

    
def view_employee(request, emp_id):
    employee = get_object_or_404(Employee, id=emp_id)
    attachments = EmployeeAttachment.objects.filter(employee=employee)
    
    # Prepare the employee data to send as JSON
    employee_data = {
        'employee_no': employee.employee_no,
        'fullname': employee.fullname,
        'date_hired': employee.date_hired.strftime('%Y-%m-%d'),
        'position': employee.position,
        'educational_attainment': employee.educational_attainment,
        'birthdate': employee.birthdate.strftime('%Y-%m-%d'),
        'gender': employee.gender,
        'fund_source': employee.fund_source,
        'tax_declaration': employee.tax_declaration,
        'salary': f"₱{employee.salary:,.2f}",
        'eligibility': employee.eligibility,
        'attachments': [
            {
                'file_url': attachment.file.url,
                'file_name': attachment.file.name.split('/')[-1],
                'attachment_id': attachment.id
            }
            for attachment in attachments
        ]
    }
    
    return JsonResponse({'employee': employee_data})

def adjustments_employee(request, emp_id):
    employee = get_object_or_404(Employee, id=emp_id)
    adjustments = Adjustment.objects.filter(employee=employee)
    return render(request, 'adjustments_employee.html', {
        'employee': employee,
        'adjustments': adjustments
    })

def add_adjustment(request, emp_id):
    employee = get_object_or_404(Employee, id=emp_id)
    if request.method == 'POST':
        
        name = request.POST['name']
        raw_amount = request.POST['amount']
        raw_amount_details = request.POST['details']

        # Compute amount if the adjustment is for "Late"
        if name == 'Late':
            try:
                minutes_late = float(raw_amount_details)
                daily_rate = float(employee.salary) / 22
                per_minute_rate = daily_rate / (8 * 60)
                computed_amount = round(per_minute_rate * minutes_late, 2)
            except Exception:
                computed_amount = Decimal('0.00')
        else:
            computed_amount = raw_amount  # use as is

        # Create the adjustment record
        Adjustment.objects.create(
            employee=employee,
            name=request.POST['name'],
            type=request.POST['type'],
            amount=computed_amount,
            details=request.POST.get('details', ''),
            month=request.POST.get('month'),
            cutoff=request.POST.get('cutoff'),
            status=request.POST.get('status', 'Pending'),
            remarks=request.POST.get('remarks', ''),
        )
        messages.success(request, 'Adjustment successfully added.')
        return redirect('adjustments_employee', emp_id=employee.id)

def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
    
def employee_adjustments_json(request, emp_id):
    employee = get_object_or_404(Employee, id=emp_id)

    draw = safe_int(request.GET.get('draw'), 1)
    start = safe_int(request.GET.get('start'), 0)
    length = safe_int(request.GET.get('length'), 10)
    search_value = request.GET.get('search[value]', '')

    queryset = Adjustment.objects.filter(employee=employee)

    if search_value:
        queryset = queryset.filter(
            Q(name__icontains=search_value) |
            Q(type__icontains=search_value) |
            Q(details__icontains=search_value) |
            Q(computation__icontains=search_value) |
            Q(cutoff__icontains=search_value) |
            Q(month__icontains=search_value) |
            Q(status__icontains=search_value) |
            Q(remarks__icontains=search_value)
        )

    total_records = Adjustment.objects.filter(employee=employee).count()
    filtered_records = queryset.count()

    columns = ['name', 'type', 'amount', 'details', 'cutoff_month', 'status', 'remarks', 'created_at']
    order_col_index = safe_int(request.GET.get('order[0][column]'), 0)
    order_dir = request.GET.get('order[0][dir]', 'asc')

    if 0 <= order_col_index < len(columns):
        order_column = 'month' if columns[order_col_index] == 'cutoff_month' else columns[order_col_index]
    else:
        order_column = 'created_at'

    if order_dir == 'desc':
        order_column = f'-{order_column}'

    queryset = queryset.order_by(order_column)[start:start + length]

    data = []
    for adj in queryset:
        details = f"{int(adj.details)} minutes" if adj.name == "Late" and adj.details.isdigit() else adj.details
        amount = (
            f"<span style='color:red'>(₱{adj.amount:,.2f})</span>"
            if adj.type == "Deduction"
            else f"<span style='color:green'>₱{adj.amount:,.2f}</span>"
        )

        data.append({
            "name": adj.name,
            "type": adj.type,
            "amount": amount,
            "details": details,
            "cutoff_month": f"{adj.month} - {adj.cutoff}",
            "status": adj.status,
            "remarks": adj.remarks,
            "created_at": adj.created_at.strftime('%Y-%m-%d %H:%M'),
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": filtered_records,
        "data": data
    })
    
def payslip(request):
    if request.session.get('user_type') == 'employee':
        # Get only the employee that matches the logged-in user's ID
        fullname = request.session.get('fullname')
        employees = Employee.objects.filter(fullname=fullname)
    else:
        employees = Employee.objects.all()
    # employees = Employee.objects.all()
    
    # Define month choices (you can make this dynamic if needed)
    month_choices = [
        ('January', 'January'),
        ('February', 'February'),
        ('March', 'March'),
        ('April', 'April'),
        ('May', 'May'),
        ('June', 'June'),
        ('July', 'July'),
        ('August', 'August'),
        ('September', 'September'),
        ('October', 'October'),
        ('November', 'November'),
        ('December', 'December'),
    ]

    # Get the current month
    current_month = datetime.now().strftime('%B') 

    if request.method == 'POST':
        # Get form data
        employee_id = request.POST.get('employee')
        selected_month = request.POST.get('month')
        selected_cutoff = request.POST.get('cutoff')

        # Fetch employee data
        employee = Employee.objects.get(id=employee_id)

        has_adjustments = Adjustment.objects.filter(
            employee=employee,
            month=selected_month,
            cutoff=selected_cutoff,
            status="Approved"
        ).exists()

        if not has_adjustments:
            messages.error(request, 'Payslip in process.')
            return redirect('payslip')
        
        # Assuming salary is stored as an amount, adjust accordingly
        basic_salary = employee.salary  # This might be calculated or stored in a field
        
        if(employee.tax_declaration == "Yes"):
             tax_deduction = Decimal('0.00')
        else:
            tax_deduction = employee.salary/2 * Decimal('0.03')  # Example: 10% tax deduction
        
        philhealth = employee.salary/2 * Decimal('0.05')
        
        #late
        late_adjustments = Adjustment.objects.filter(
            employee=employee,
            name="Late",
            month=selected_month,
            cutoff=selected_cutoff,
            status="Approved"
            # Adjusted condition to match selected month
        )
        
        late_amt_total = late_adjustments.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        late_min_total = late_adjustments.aggregate(Sum('details'))['details__sum'] or Decimal('0.00') 
        
        # Format the salary period
        salary_period = f"{selected_month} - {selected_cutoff}"
        
        #adjustment_minus
        all_adjustment_minus = Adjustment.objects.filter(
            employee=employee,
            type="Deduction",
            month=selected_month,
            cutoff=selected_cutoff,
            status="Approved"
            # Adjusted condition to match selected month
        ).exclude(name="Late")
        
        # Sum the amount for all adjustments
        total_adjustment_amount_minus = all_adjustment_minus.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')


     
        total_deductions = tax_deduction + philhealth + late_amt_total + total_adjustment_amount_minus


        #adjustment_plus
        all_adjustment_plus = Adjustment.objects.filter(
            employee=employee,
            type="Income",
            month=selected_month,
            cutoff=selected_cutoff,
            status="Approved"
            # Adjusted condition to match selected month
        )
        
        # Sum the amount for all adjustments
        total_adjustment_amount_plus = all_adjustment_plus.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        total_add = total_adjustment_amount_plus
        
        basic_salary_cutoff = basic_salary / 2  # Assuming the salary is for a month and you want half for the cutoff
        
        context = {
            'employee_no': employee.employee_no,
            'employee_name': employee.fullname,
            'position': employee.position,
            'employee_id': employee.id,
            'salary_period': salary_period,
            'selected_cutoff': selected_cutoff,
            'basic_salary_cutoff': basic_salary_cutoff,
            'tax_deduction': tax_deduction,
            'philhealth': philhealth,
            'late_amt_total': late_amt_total,
            'late_min_total': late_min_total,
            'total_adjustment_amount_minus': total_adjustment_amount_minus,
            'all_adjustment_minus': all_adjustment_minus,
            'total_adjustment_amount_plus': total_adjustment_amount_plus,
            'all_adjustment_plus': all_adjustment_plus,
            'total_deductions' : total_deductions,
            'total_add': total_add,
            'net_pay': basic_salary_cutoff - total_deductions + total_add,
            'employees': employees,  # Make sure to pass the employees list here
            'month_choices': month_choices,
            'current_month': current_month,
        }

        return render(request, 'payslip.html', context)

    # If it's a GET request, display the form with the employee and month choices
    return render(request, 'payslip.html', {
        'employees': employees,
        'month_choices': month_choices,
        'current_month': current_month,
    })