from django import forms
from .models import Teacher, Subject, Application, Exam, InvigilationPreference, Department

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['department', 'seniority', 'expertise']

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'department', 'required_expertise']

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['subject']
        
    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop('teacher', None)
        super(ApplicationForm, self).__init__(*args, **kwargs)
        
    def save(self, commit=True):
        instance = super(ApplicationForm, self).save(commit=False)
        instance.teacher = self.teacher
        if commit:
            instance.save()
        return instance
    
class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['subject', 'date', 'start_time', 'end_time', 'hall']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

class InvigilationPreferenceForm(forms.ModelForm):
    class Meta:
        model = InvigilationPreference
        fields = ['exam', 'rank', 'consecutive_slot_requested']
        
    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop('teacher', None)
        super(InvigilationPreferenceForm, self).__init__(*args, **kwargs)
        
    def save(self, commit=True):
        instance = super(InvigilationPreferenceForm, self).save(commit=False)
        instance.teacher = self.teacher
        if commit:
            instance.save()
        return instance

class AllocateSubjectsForm(forms.Form):
    academic_year = forms.CharField(max_length=9, help_text="Format: YYYY-YYYY")

class AllocateInvigilationForm(forms.Form):
    pass  # No additional fields needed, just a submit button