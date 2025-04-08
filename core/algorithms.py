from .models import Teacher, Subject, Application, Allocation, Exam, InvigilationPreference, InvigilationAllocation
from django.db.models import Count

def allocate_subjects(academic_year):
    """
    Algorithm to allocate subjects to teachers based on:
    1. Seniority
    2. Expertise match
    3. Application timing
    """
    # Get all subjects that have applications
    subjects = Subject.objects.filter(application__isnull=False).distinct()
    allocations = []
    
    for subject in subjects:
        # Get all applications for this subject
        applications = Application.objects.filter(subject=subject).select_related('teacher')
        
        # Calculate scores for each application
        scored_applications = []
        for application in applications:
            teacher = application.teacher
            
            # Seniority score (0-10)
            seniority_score = min(teacher.seniority, 10)
            
            # Expertise match score (0-10)
            teacher_expertise = set(teacher.get_expertise_list())
            required_expertise = set(subject.get_required_expertise_list())
            if required_expertise:
                expertise_match = len(teacher_expertise.intersection(required_expertise)) / len(required_expertise)
                expertise_score = expertise_match * 10
            else:
                expertise_score = 5  # Neutral score if no expertise required
            
            # Application timing score (earlier = higher, max 5)
            # We'll normalize this across all applications for this subject
            timestamp = application.timestamp
            
            scored_applications.append({
                'application': application,
                'teacher': teacher,
                'seniority_score': seniority_score,
                'expertise_score': expertise_score,
                'timestamp': timestamp,
            })
        
        # Sort by timestamp to calculate timing score
        sorted_by_time = sorted(scored_applications, key=lambda x: x['timestamp'])
        for i, app in enumerate(sorted_by_time):
            # Earlier applications get higher scores
            app['timing_score'] = max(5 - i, 0)
        
        # Calculate total score and find the best match
        for app in scored_applications:
            app['total_score'] = app['seniority_score'] * 0.5 + app['expertise_score'] * 0.3 + app['timing_score'] * 0.2
        
        # Sort by total score (highest first)
        scored_applications.sort(key=lambda x: x['total_score'], reverse=True)
        
        if scored_applications:
            # Allocate to the highest scoring teacher
            best_match = scored_applications[0]
            allocation = Allocation(
                teacher=best_match['teacher'],
                subject=subject,
                academic_year=academic_year
            )
            allocations.append(allocation)
    
    # Save all allocations
    Allocation.objects.bulk_create(allocations)
    return allocations

def allocate_invigilation_duties():
    """
    Algorithm to allocate invigilation duties based on:
    1. Teacher preferences
    2. Consecutive slot requests
    3. Fair distribution of duties
    """
    # Get all exams
    exams = Exam.objects.all().order_by('date', 'time_slot')
    
    # Get all teachers with preferences
    teachers = Teacher.objects.filter(invigilationpreference__isnull=False).distinct()
    
    # Count current invigilation duties for each teacher
    teacher_duty_counts = {
        teacher.id: InvigilationAllocation.objects.filter(teacher=teacher).count()
        for teacher in teachers
    }
    
    allocations = []
    
    # Process exams chronologically
    for exam in exams:
        # Skip if already allocated
        if InvigilationAllocation.objects.filter(exam=exam).exists():
            continue
        
        # Get preferences for this exam
        preferences = InvigilationPreference.objects.filter(exam=exam).select_related('teacher')
        
        # Score each preference
        scored_preferences = []
        for preference in preferences:
            teacher = preference.teacher
            
            # Preference rank score (1-10, lower rank = higher score)
            rank_score = max(11 - preference.rank, 1)
            
            # Workload balance score (fewer duties = higher score)
            duty_count = teacher_duty_counts.get(teacher.id, 0)
            workload_score = max(10 - duty_count, 1)
            
            # Consecutive slot bonus
            consecutive_bonus = 0
            if preference.consecutive_slot_requested:
                # Check if teacher is allocated to the previous or next exam
                exam_date = exam.date
                exam_slot = exam.time_slot
                
                # Previous exam (same day, earlier slot)
                if exam_slot == 'afternoon':
                    prev_exams = Exam.objects.filter(
                        date=exam_date, 
                        time_slot='morning'
                    )
                    for prev_exam in prev_exams:
                        if InvigilationAllocation.objects.filter(
                            exam=prev_exam, 
                            teacher=teacher
                        ).exists():
                            consecutive_bonus = 5
                            break
                
                # Next exam (same day, later slot or next day, first slot)
                if exam_slot == 'morning':
                    next_exams = Exam.objects.filter(
                        date=exam_date, 
                        time_slot='afternoon'
                    )
                    for next_exam in next_exams:
                        if InvigilationAllocation.objects.filter(
                            exam=next_exam, 
                            teacher=teacher
                        ).exists():
                            consecutive_bonus = 5
                            break
            
            # Calculate total score
            total_score = rank_score * 0.4 + workload_score * 0.4 + consecutive_bonus * 0.2
            
            scored_preferences.append({
                'preference': preference,
                'teacher': teacher,
                'total_score': total_score
            })
        
        # Sort by total score (highest first)
        scored_preferences.sort(key=lambda x: x['total_score'], reverse=True)
        
        if scored_preferences:
            # Allocate to the highest scoring teacher
            best_match = scored_preferences[0]
            allocation = InvigilationAllocation(
                teacher=best_match['teacher'],
                exam=exam
            )
            allocations.append(allocation)
            
            # Update duty count for this teacher
            teacher_id = best_match['teacher'].id
            teacher_duty_counts[teacher_id] = teacher_duty_counts.get(teacher_id, 0) + 1
    
    # Save all allocations
    InvigilationAllocation.objects.bulk_create(allocations)
    return allocations