

def allocate_invigilation_duties():
    
    from .models import InvigilationPreference, InvigilationAllocation
    from .models import Exam
    from .models import Teacher
    from django.db.models import Count
    
    # Clear existing allocations
    InvigilationAllocation.objects.all().delete()
    
    # Get all exams that need invigilators
    exams = Exam.objects.all().order_by('date', 'start_time')
    
    # Get all teachers
    teachers = Teacher.objects.all()
    
    # Dictionary to track teacher allocations
    teacher_allocations = {teacher.id: 0 for teacher in teachers}
    
    # Process exams by date
    exam_dates = exams.values_list('date', flat=True).distinct()
    
    for exam_date in exam_dates:
        # Get exams for this date, ordered by start time
        day_exams = exams.filter(date=exam_date).order_by('start_time')
        
        # Track allocated teachers for this day to avoid conflicts
        day_allocated_teachers = {}
        
        for exam in day_exams:
            # Get preferences for this exam, ordered by rank (1 is highest preference)
            preferences = InvigilationPreference.objects.filter(exam=exam).order_by('rank')
            
            # Create a list of candidate teachers based on preferences
            candidates = []
            
            # First, add teachers with preferences for this exam
            for pref in preferences:
                # Skip if teacher already allocated to an overlapping exam on this day
                if pref.teacher.id in day_allocated_teachers:
                    allocated_exams = day_allocated_teachers[pref.teacher.id]
                    conflict = False
                    
                    for allocated_exam in allocated_exams:
                        # Check for time overlap
                        if (exam.start_time <= allocated_exam.end_time and 
                            exam.end_time >= allocated_exam.start_time):
                            conflict = True
                            break
                    
                    if conflict:
                        continue
                
                # Add to candidates with a score based on preference and current allocation count
                score = pref.rank * 10 - teacher_allocations[pref.teacher.id]
                candidates.append((pref.teacher, score, pref))
            
            # If we don't have enough candidates with preferences, add other teachers
            if len(candidates) < 2:  # Assuming we need at least 2 invigilators per exam
                for teacher in teachers:
                    # Skip if already a candidate or has a conflict
                    if teacher.id in [c[0].id for c in candidates]:
                        continue
                        
                    if teacher.id in day_allocated_teachers:
                        allocated_exams = day_allocated_teachers[teacher.id]
                        conflict = False
                        
                        for allocated_exam in allocated_exams:
                            # Check for time overlap
                            if (exam.start_time <= allocated_exam.end_time and 
                                exam.end_time >= allocated_exam.start_time):
                                conflict = True
                                break
                        
                        if conflict:
                            continue
                    
                    # Add to candidates with a score based only on current allocation count
                    score = 100 - teacher_allocations[teacher.id]  # Lower score for teachers without preferences
                    candidates.append((teacher, score, None))
            
            # Sort candidates by score (lower is better)
            candidates.sort(key=lambda x: x[1])
            
            # Allocate the top 2 candidates (or however many are needed)
            num_invigilators_needed = 2  # This could be based on exam size or other factors
            
            for i in range(min(num_invigilators_needed, len(candidates))):
                teacher, _, preference = candidates[i]
                
                # Create allocation
                allocation = InvigilationAllocation(
                    exam=exam,
                    teacher=teacher,
                    preference=preference
                )
                allocation.save()
                
                # Update tracking
                teacher_allocations[teacher.id] += 1
                
                if teacher.id not in day_allocated_teachers:
                    day_allocated_teachers[teacher.id] = []
                
                day_allocated_teachers[teacher.id].append(exam)
                
                # Check for consecutive slot requests
                if preference and preference.consecutive_slot_requested:
                    # Find next exam on the same day
                    next_exams = day_exams.filter(start_time__gt=exam.end_time)
                    
                    if next_exams.exists():
                        next_exam = next_exams.first()
                        
                        # Check if teacher is not already allocated to this exam
                        if not InvigilationAllocation.objects.filter(exam=next_exam, teacher=teacher).exists():
                            # Check if this exam already has enough invigilators
                            existing_allocations = InvigilationAllocation.objects.filter(exam=next_exam).count()
                            
                            if existing_allocations < num_invigilators_needed:
                                # Create allocation for consecutive exam
                                next_allocation = InvigilationAllocation(
                                    exam=next_exam,
                                    teacher=teacher,
                                    preference=None  # No direct preference for this one
                                )
                                next_allocation.save()
                                
                                # Update tracking
                                teacher_allocations[teacher.id] += 1
                                day_allocated_teachers[teacher.id].append(next_exam)
    
    return True