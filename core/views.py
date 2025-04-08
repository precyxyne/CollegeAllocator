from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
import datetime
from .models import (
    Department, Teacher, Subject, Application, Allocation,
    Exam, InvigilationPreference, InvigilationAllocation
)
from .forms import (
    DepartmentForm, TeacherForm, SubjectForm, ApplicationForm,
    ExamForm, InvigilationPreferenceForm, AllocateSubjectsForm,
    AllocateInvigilationForm
)
from .algorithms import allocate_subjects, allocate_invigilation_duties
from django.contrib.auth.models import User
def home(request):
    context = {
        'teacher_count': Teacher.objects.count(),
        'subject_count': Subject.objects.count(),
        'exam_count': Exam.objects.count(),
    }
    return render(request, 'home.html', context)
def subject_list(request, department_name):
    department = get_object_or_404(Department, name=department_name)
    subjects = Subject.objects.filter(department=department)
    return render(request, 'departments/subjects.html', {'department': department, 'subjects': subjects})

# Department views
class DepartmentListView(ListView):
    model = Department
    template_name = 'departments/department_list.html'
    context_object_name = 'departments'

class DepartmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'departments/department_form.html'
    success_url = reverse_lazy('department-list')
    
    def test_func(self):
        return self.request.user.is_staff

# Teacher views
class TeacherListView(ListView):
    model = Teacher
    template_name = 'teachers/teacher_list.html'
    context_object_name = 'teachers'

class TeacherDetailView(DetailView):
    model = Teacher
    template_name = 'teachers/teacher_detail.html'
    context_object_name = 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.get_object()
        context['allocated_subjects'] = Allocation.objects.filter(teacher=teacher)
        context['invigilation_duties'] = InvigilationAllocation.objects.filter(teacher=teacher)
        return context

class TeacherCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'teachers/teacher_form.html'
    success_url = reverse_lazy('teacher-list')
    
    def test_func(self):
        return self.request.user.is_staff

# Subject views
class SubjectListView(ListView):
    model = Subject
    template_name = 'subjects/subject_list.html'
    context_object_name = 'subjects'

class SubjectDetailView(DetailView):
    model = Subject
    template_name = 'subjects/subject_detail.html'
    context_object_name = 'subject'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subject = self.get_object()
        context['applications'] = Application.objects.filter(subject=subject)
        context['allocation'] = Allocation.objects.filter(subject=subject).first()
        return context

class SubjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'subjects/subject_form.html'
    success_url = reverse_lazy('subject-list')
    
    def test_func(self):
        return self.request.user.is_staff

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already taken.')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already registered.')
            else:
                user = User.objects.create_user(username=username, email=email, password=password1)
                user.save()
                messages.success(request, 'Registration successful. You can now log in.')
                return redirect('login')
        else:
            messages.error(request, 'Passwords do not match.')

    return render(request, 'register.html')
# Application views
@login_required
def apply_for_subject(request):
    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        messages.error(request, "You must be registered as a teacher to apply for subjects.")
        return redirect('home')
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST, teacher=teacher)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Application submitted successfully!")
                return redirect('my-applications')
            except IntegrityError:
                messages.error(request, "You have already applied for this subject.")
    else:
        form = ApplicationForm(teacher=teacher)
    
    return render(request, 'applications/apply.html', {'form': form})

@login_required
def my_applications(request):
    try:
        teacher = request.user.teacher
        applications = Application.objects.filter(teacher=teacher)
        return render(request, 'applications/my_applications.html', {'applications': applications})
    except Teacher.DoesNotExist:
        messages.error(request, "You must be registered as a teacher to view applications.")
        return redirect('home')

# Exam views
@login_required
def exam_list(request):
    exams = Exam.objects.all()
    
    # Apply filters
    if 'date' in request.GET and request.GET['date']:
        exams = exams.filter(date=request.GET['date'])
    
    if 'start_time_after' in request.GET and request.GET['start_time_after']:
        start_time = datetime.datetime.strptime(request.GET['start_time_after'], '%H:%M').time()
        exams = exams.filter(start_time__gte=start_time)
    
    if 'end_time_before' in request.GET and request.GET['end_time_before']:
        end_time = datetime.datetime.strptime(request.GET['end_time_before'], '%H:%M').time()
        exams = exams.filter(end_time__lte=end_time)
    
    context = {
        'exams': exams,
    }
    return render(request, 'exams/exam_list.html', context)

@login_required
def exam_create(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('exam-list')
    
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Exam created successfully!")
            return redirect('exam-list')
    else:
        form = ExamForm()
    
    return render(request, 'exams/exam_form.html', {'form': form})

@login_required
def exam_update(request, pk):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('exam-list')
    
    exam = get_object_or_404(Exam, pk=pk)
    
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, "Exam updated successfully!")
            return redirect('exam-list')
    else:
        form = ExamForm(instance=exam)
    
    return render(request, 'exams/exam_form.html', {'form': form})

# Invigilation preference views
@login_required
def submit_invigilation_preference(request):
    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        messages.error(request, "You must be registered as a teacher to submit invigilation preferences.")
        return redirect('home')
    
    if request.method == 'POST':
        form = InvigilationPreferenceForm(request.POST, teacher=teacher)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Invigilation preference submitted successfully!")
                return redirect('my-invigilation-preferences')
            except IntegrityError:
                messages.error(request, "You have already submitted a preference for this exam.")
    else:
        form = InvigilationPreferenceForm(teacher=teacher)
    
    return render(request, 'invigilation/submit_preference.html', {'form': form})

@login_required
def my_invigilation_preferences(request):
    try:
        teacher = request.user.teacher
        preferences = InvigilationPreference.objects.filter(teacher=teacher)
        return render(request, 'invigilation/my_preferences.html', {'preferences': preferences})
    except Teacher.DoesNotExist:
        messages.error(request, "You must be registered as a teacher to view invigilation preferences.")
        return redirect('home')

# Allocation views
@login_required
def allocate_subjects_view(request):
    if not request.user.is_staff:
        messages.error(request, "You must be an administrator to allocate subjects.")
        return redirect('home')
    
    if request.method == 'POST':
        form = AllocateSubjectsForm(request.POST)
        if form.is_valid():
            academic_year = form.cleaned_data['academic_year']
            allocations = allocate_subjects(academic_year)
            messages.success(request, f"{len(allocations)} subjects allocated successfully!")
            return redirect('allocation-list')
    else:
        form = AllocateSubjectsForm()
    
    return render(request, 'allocations/allocate_subjects.html', {'form': form})

@login_required
def allocate_invigilation_view(request):
    if not request.user.is_staff:
        messages.error(request, "You must be an administrator to allocate invigilation duties.")
        return redirect('home')
    
    if request.method == 'POST':
        form = AllocateInvigilationForm(request.POST)
        if form.is_valid():
            allocations = allocate_invigilation_duties()
            messages.success(request, f"{len(allocations)} invigilation duties allocated successfully!")
            return redirect('invigilation-allocation-list')
    else:
        form = AllocateInvigilationForm()
    
    return render(request, 'invigilation/allocate_invigilation.html', {'form': form})

class AllocationListView(ListView):
    model = Allocation
    template_name = 'allocations/allocation_list.html'
    context_object_name = 'allocations'
    
@login_required
def invigilation_allocation_list(request):
    allocations = InvigilationAllocation.objects.all().order_by('exam__date', 'exam__start_time')
    teachers = Teacher.objects.all()
    
    # Apply filters
    if 'date' in request.GET and request.GET['date']:
        allocations = allocations.filter(exam__date=request.GET['date'])
    
    if 'start_time_after' in request.GET and request.GET['start_time_after']:
        start_time = datetime.datetime.strptime(request.GET['start_time_after'], '%H:%M').time()
        allocations = allocations.filter(exam__start_time__gte=start_time)
    
    if 'teacher' in request.GET and request.GET['teacher']:
        allocations = allocations.filter(teacher_id=request.GET['teacher'])
    
    context = {
        'allocations': allocations,
        'teachers': teachers,
    }
    return render(request, 'invigilation/invigilation_allocation_list.html', context)