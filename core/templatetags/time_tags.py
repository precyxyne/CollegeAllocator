from django import template
from datetime import datetime, timedelta

register = template.Library()

@register.filter(name='duration')
def duration(end_time, start_time):
    """
    Calculate the duration between two time objects
    """
    # Create datetime objects for today with the given times
    today = datetime.now().date()
    start_dt = datetime.combine(today, start_time)
    end_dt = datetime.combine(today, end_time)
    
    # If end time is earlier than start time, it means it's on the next day
    if end_dt < start_dt:
        end_dt = end_dt + timedelta(days=1)
    
    # Calculate duration
    duration = end_dt - start_dt
    
    # Convert to hours and minutes
    total_minutes = duration.total_seconds() / 60
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    
    if hours > 0:
        return f"{hours} hr{'' if hours == 1 else 's'} {minutes} min{'' if minutes == 1 else 's'}"
    else:
        return f"{minutes} min{'' if minutes == 1 else 's'}"