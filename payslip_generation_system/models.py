import os
import random
import string
from django.utils.timezone import now
from django.db import models

# Create your models here.

class User(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=255)  # Unique email for each user
    contact_number = models.CharField(max_length=20)
    division = models.CharField(max_length=100)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)  # store hashed password
    type = models.CharField(max_length=50)       # e.g., admin, staff
    status = models.CharField(max_length=20)     # e.g., active, inactive

    class Meta:
        db_table = 'users'
        
    def __str__(self):
        return self.username

class Employee(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    YES_NO_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No'),
    ]

    EDUCATION_CHOICES = [
        ('High School', 'High School'),
        ('College', 'College'),
        ('Postgraduate', 'Postgraduate'),
        ('Others', 'Others'),
    ]

    employee_no = models.CharField(max_length=255, default='Unknown')
    fullname = models.CharField(max_length=255, default='Unknown')
    date_hired = models.DateField()
    position = models.CharField(max_length=100)
    educational_attainment = models.CharField(
        max_length=50, 
        choices=EDUCATION_CHOICES, 
        null=True,  # Allow null values
        blank=True  # Allow the field to be left blank in forms
    )
    birthdate = models.DateField()
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    fund_source = models.CharField(max_length=100)
    tax_declaration = models.CharField(
        max_length=3, 
        choices=YES_NO_CHOICES, 
        null=True,  # Allow NULL values in the database
        blank=True  # Allow blank values in forms
    )
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    eligibility = models.CharField(max_length=3, choices=YES_NO_CHOICES)

    def __str__(self):
        return f"{self.position} - {self.date_hired}"

def generate_filename(instance, filename):
    employee_name = instance.employee.fullname.replace(' ', '_')
    base_name, extension = os.path.splitext(filename)
    new_filename = f"{employee_name}_{base_name}{extension}"
    return os.path.join('employee_attachments', new_filename)

class EmployeeAttachment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attachments')

    # Use the custom function to generate a random filename for each uploaded file
    file = models.FileField(upload_to=generate_filename)  # Attach to the 'employee_attachments/' folder

    def delete(self, *args, **kwargs):
        # Delete the file from the file system
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        super().delete(*args, **kwargs)
        
    def __str__(self):
        return self.file.name
    

class Adjustment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    # Name of the adjustment (e.g., Bonus, Deductions)
    name = models.CharField(max_length=255)
    
    # Type of adjustment (e.g., Income, Deduction)
    TYPE_CHOICES = [
        ('Income', 'Income'),
        ('Deduction', 'Deduction'),
    ]
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    
    # Amount of the adjustment (e.g., 1000.00, -500.00)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Details about the adjustment (e.g., reason or description)
    details = models.TextField()
    
    # Computation method for the adjustment (e.g., Percentage, Flat Amount)
    computation = models.CharField(max_length=50)
    
    # Month and Period for the adjustment
    month = models.CharField(max_length=20, choices=[ 
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
        ('December', 'December')
    ], null=True) 
    
     # To store Month (January - December)
    cutoff = models.CharField(max_length=10, choices=[('1st', '1st'), ('2nd', '2nd')])  # Cutoff (1st or 2nd)

    
    # Status of the adjustment (e.g., Pending, Approved, Rejected)
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    
    # Remarks or notes about the adjustment (e.g., any extra information)
    remarks = models.TextField(null=True, blank=True)

    # Timestamps to track when adjustments were created/updated
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Adjustment'
        verbose_name_plural = 'Adjustments'
