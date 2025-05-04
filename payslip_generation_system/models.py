import os
import random
import string
from django.utils.timezone import now
from django.db import models

# Create your models here.

class User(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
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

def generate_random_filename(instance, filename):
    # Generate a random string for the filename
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))  # 8-character random string
    # Get the file extension
    extension = filename.split('.')[-1]
    # Combine random string with the file extension
    new_filename = f'{random_string}.{extension}'
    # Return the path where the file should be saved
    return os.path.join('employee_attachments', new_filename)

class EmployeeAttachment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attachments')
    
    # Use the custom function to generate a random filename for each uploaded file
    file = models.FileField(upload_to=generate_random_filename)  # Attach to the 'employee_attachments/' folder

    def delete(self, *args, **kwargs):
        # Delete the file from the file system
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        super().delete(*args, **kwargs)
        
    def __str__(self):
        return self.file.name