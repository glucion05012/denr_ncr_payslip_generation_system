from django.contrib import admin
from django.urls import path
from . import views
from payslip_generation_system import views as views_pgs
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    
    path('test/', views.test, name='test'),
    
    # login page
    path('login/', views.login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('add_employee_profile/', views.add_employee, name='add_employee_profile'),
    path('add-employee/', views.add_employee, name='add_employee'),
    path('employee/edit/<int:emp_id>/', views.edit_employee, name='edit_employee'),
    path('employee/delete/<int:emp_id>/', views.delete_employee, name='delete_employee'),
    path('attachments/delete/<int:attachment_id>/', views.delete_attachment, name='delete_attachment'),

    # get data from database
    path('employee-data/', views.employee_data_json, name='employee_data_json'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)