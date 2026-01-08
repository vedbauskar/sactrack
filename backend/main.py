# main.py
import json
from supabase import create_client
from datetime import datetime
from supabase import create_client
from secrets import SUPABASE_URL, SUPABASE_SERVICE_KEY

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
print("✓ Connected to Supabase\n")

def transform_course(course):
    """Transform course data to match database schema"""
    instructor_name = 'TBA'
    instructor_email = None
    if course.get('faculty'):
        instructor_name = course['faculty'][0].get('displayName', 'TBA')
        instructor_email = course['faculty'][0].get('emailAddress')
    
    meeting = {}
    if course.get('meetingsFaculty') and len(course['meetingsFaculty']) > 0:
        meeting = course['meetingsFaculty'][0].get('meetingTime', {})
    
    meeting_days = []
    if meeting.get('monday'): meeting_days.append('M')
    if meeting.get('tuesday'): meeting_days.append('T')
    if meeting.get('wednesday'): meeting_days.append('W')
    if meeting.get('thursday'): meeting_days.append('R')
    if meeting.get('friday'): meeting_days.append('F')
    
    return {
        'crn': course.get('courseReferenceNumber'),
        'term': course.get('term'),
        'term_desc': course.get('termDesc'),
        'subject': course.get('subject'),
        'course_number': course.get('courseNumber'),
        'section': course.get('sequenceNumber'),
        'title': course.get('courseTitle'),
        'credits_low': course.get('creditHourLow'),
        'credits_high': course.get('creditHourHigh'),
        'instructor_name': instructor_name,
        'instructor_email': instructor_email,
        'max_enrollment': course.get('maximumEnrollment'),
        'current_enrollment': course.get('enrollment'),
        'seats_available': course.get('seatsAvailable'),
        'waitlist_capacity': course.get('waitCapacity'),
        'waitlist_count': course.get('waitCount'),
        'open_section': course.get('openSection'),
        'schedule_type': course.get('scheduleTypeDescription'),
        'instructional_method': course.get('instructionalMethodDescription'),
        'campus': course.get('campusDescription'),
        'meeting_days': ','.join(meeting_days) if meeting_days else None,
        'meeting_time_start': meeting.get('beginTime'),
        'meeting_time_end': meeting.get('endTime'),
        'meeting_building': meeting.get('building'),
        'meeting_room': meeting.get('room'),
        'start_date': meeting.get('startDate'),
        'end_date': meeting.get('endDate'),
        'updated_at': datetime.now().isoformat()
    }

# Load JSON file
json_file = 'mtsac_spring2026_final.json'
print(f"📁 Loading courses from {json_file}...")

with open(json_file, 'r') as f:
    courses = json.load(f)

print(f"✓ Loaded {len(courses)} courses")

# Transform courses
print("🔄 Transforming data...")
transformed = [transform_course(c) for c in courses]
print(f"✓ Transformed {len(transformed)} courses")

# Upload to Supabase in batches
print(f"\n💾 Uploading to Supabase...")
batch_size = 100
total_batches = (len(transformed) + batch_size - 1) // batch_size
success_count = 0
error_count = 0

for i in range(0, len(transformed), batch_size):
    batch = transformed[i:i + batch_size]
    batch_num = i // batch_size + 1
    
    try:
        response = supabase.table('courses').upsert(batch).execute()
        success_count += len(batch)
        print(f"  ✓ Uploaded batch {batch_num}/{total_batches} ({len(batch)} courses)")
    except Exception as e:
        error_count += len(batch)
        print(f"  ✗ Error in batch {batch_num}: {e}")

print(f"\n{'='*50}")
print(f"✅ DONE!")
print(f"   Successfully uploaded: {success_count} courses")
if error_count > 0:
    print(f"   ❌ Errors: {error_count} courses")
print(f"{'='*50}")
