from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),

    # Departments
    path('departments/', views.DepartmentListView.as_view(), name='department-list'),
    path('departments/new/', views.DepartmentCreateView.as_view(), name='department-create'),
    path('departments/<str:department_name>/subjects/', views.subject_list, name='subject-list'),
    
    # Teachers
    path('teachers/', views.TeacherListView.as_view(), name='teacher-list'),
    path('teachers/<int:pk>/', views.TeacherDetailView.as_view(), name='teacher-detail'),
    path('teachers/new/', views.TeacherCreateView.as_view(), name='teacher-create'),
    
    # Subjects
    path('subjects/', views.SubjectListView.as_view(), name='subject-list'),
    path('subjects/<int:pk>/', views.SubjectDetailView.as_view(), name='subject-detail'),
    path('subjects/new/', views.SubjectCreateView.as_view(), name='subject-create'),
    
    # Applications
    path('apply/', views.apply_for_subject, name='apply'),
    path('my-applications/', views.my_applications, name='my-applications'),
    
    # Exams
    path('exams/', views.exam_list, name='exam-list'),
    path('exams/new/', views.exam_create, name='exam-create'),
    
    # Invigilation
    path('invigilation/submit/', views.submit_invigilation_preference, name='submit-invigilation'),
    path('invigilation/my-preferences/', views.my_invigilation_preferences, name='my-invigilation-preferences'),
    
    # Allocation
    path('allocate/subjects/', views.allocate_subjects_view, name='allocate-subjects'),
    path('allocate/invigilation/', views.allocate_invigilation_view, name='allocate-invigilation'),
    path('allocations/', views.AllocationListView.as_view(), name='allocation-list'),
    path('invigilation-allocations/', views.invigilation_allocation_list, name='invigilation-allocation-list'),
]