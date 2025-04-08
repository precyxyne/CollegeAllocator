from django.contrib import admin
from .models import (
    Department, Teacher, Subject, Application, Allocation,
    Exam, InvigilationPreference, InvigilationAllocation
)

admin.site.register(Department)
admin.site.register(Teacher)
admin.site.register(Subject)
admin.site.register(Application)
admin.site.register(Allocation)
admin.site.register(Exam)
admin.site.register(InvigilationPreference)
admin.site.register(InvigilationAllocation)