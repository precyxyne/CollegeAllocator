from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Department(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    seniority = models.IntegerField(help_text="Years of experience")
    expertise = models.TextField(help_text="Comma-separated list of expertise areas")
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.department})"
    
    def get_expertise_list(self):
        return [e.strip() for e in self.expertise.split(',')]

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    required_expertise = models.TextField(help_text="Comma-separated list of required expertise areas")
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_required_expertise_list(self):
        return [e.strip() for e in self.required_expertise.split(',')]

class Application(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('teacher', 'subject')
    
    def __str__(self):
        return f"{self.teacher} applied for {self.subject}"

class Allocation(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=9, help_text="Format: YYYY-YYYY")
    
    class Meta:
        unique_together = ('subject', 'academic_year')
    
    def __str__(self):
        return f"{self.subject} allocated to {self.teacher} for {self.academic_year}"

class Exam(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField(help_text="When the exam begins",default= None)
    end_time = models.TimeField(help_text="When the exam ends",default= None)
    hall = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.subject.name} - {self.date} ({self.start_time.strftime('%H:%M')} to {self.end_time.strftime('%H:%M')})"
    
    def get_time_range(self):
        """Return a formatted time range string"""
        return f"{self.start_time.strftime('%H:%M')} to {self.end_time.strftime('%H:%M')}"
    
    class Meta:
        ordering = ['date', 'start_time']
class InvigilationPreference(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    rank = models.PositiveIntegerField(help_text="Lower number means higher preference")
    consecutive_slot_requested = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('teacher', 'exam')
    
    def __str__(self):
        return f"{self.teacher} prefers {self.exam} (Rank: {self.rank})"

class InvigilationAllocation(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('exam', 'teacher')
    
    def __str__(self):
        return f"{self.teacher} assigned to invigilate {self.exam}"