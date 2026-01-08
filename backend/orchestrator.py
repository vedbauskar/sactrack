# orchestrator.py
"""
Main orchestrator script that scrapes courses and uploads to Supabase.
Supports multiple terms and automatic term detection.
"""
import json
import sys
import requests
from datetime import datetime
from supabase import create_client
from secrets import SUPABASE_URL, SUPABASE_SERVICE_KEY
from scraper import scrape_all_courses, get_subjects

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def get_available_terms():
    """
    Get list of available terms from Mt. SAC.
    Returns list of term dictionaries with code and description.
    """
    base_url = "https://prodrg.mtsac.edu/StudentRegistrationSsb/ssb"
    try:
        session = requests.Session()
        session.get(f"{base_url}/term/termSelection?mode=search")
        
        # Get terms endpoint
        terms_url = f"{base_url}/term/search?mode=search"
        response = session.get(terms_url)
        
        # Try to parse terms from the response
        # This might need adjustment based on actual API response
        # For now, we'll use a helper function to generate future terms
        return generate_future_terms()
    except Exception as e:
        print(f"⚠️  Could not fetch terms from API, using generated terms: {e}")
        return generate_future_terms()

def generate_future_terms(years_ahead=2):
    """
    Generate term codes for past, current and future terms.
    Mt. SAC term codes: YYYYTT where TT is:
    - 10 = Winter
    - 30 = Fall
    - 40 = Spring
    - 50 = Summer
    """
    current_year = datetime.now().year
    
    terms = []
    
    # Start from previous year to catch Fall 2025 etc.
    start_year = current_year - 1
    
    for year_offset in range(years_ahead + 2): # +2 to cover previous year and current year + years_ahead
        year = start_year + year_offset
        
        # Add all terms for the year
        # Order: Winter, Spring, Summer, Fall
        # But we sort at the end anyway
        for season_code, season_name in [(10, 'Winter'), (30, 'Fall'), (40, 'Spring'), (50, 'Summer')]:
            term_code = f"{year}{season_code}"
            
            # Filter out terms that are too old (e.g., typically we don't want Winter/Spring of previous year)
            # User specifically asked for Fall 2025 (202530)
            # So if year == current_year - 1, we only want Fall (30) and maybe Summer (50) or Winter (10)?
            # The prompt implies missing "winter classes for 2026 or even fall 2025".
            # Winter 2026 is 202610. Fall 2025 is 202530.
            
            # Simple rule: Include everything from Fall of previous year onwards.
            if year == current_year - 1 and season_code < 30:
                continue
                
            terms.append({
                'code': term_code,
                'description': f'{season_name} {year}',
                'year': year,
                'season': season_name
            })
    
    # Sort by term code
    terms.sort(key=lambda x: x['code'])
    return terms

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

def upload_courses_to_supabase(courses, term_code):
    """Upload transformed courses to Supabase"""
    if not courses:
        print(f"  ⚠️  No courses to upload for term {term_code}")
        return 0, 0
    
    print(f"  🔄 Transforming {len(courses)} courses...")
    transformed = []
    transform_errors = 0
    
    for course in courses:
        try:
            transformed.append(transform_course(course))
        except Exception as e:
            transform_errors += 1
            print(f"    ⚠️  Error transforming course CRN {course.get('courseReferenceNumber', 'unknown')}: {e}")
    
    if transform_errors > 0:
        print(f"  ⚠️  {transform_errors} courses failed to transform")
    
    if not transformed:
        print(f"  ⚠️  No valid courses to upload after transformation")
        return 0, transform_errors
    
    print(f"  💾 Uploading {len(transformed)} courses to Supabase...")
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
            print(f"    ✓ Uploaded batch {batch_num}/{total_batches} ({len(batch)} courses)")
        except Exception as e:
            error_count += len(batch)
            print(f"    ✗ Error in batch {batch_num}: {e}")
            # Try to continue with next batch
            import traceback
            traceback.print_exc()
    
    return success_count, error_count + transform_errors

def process_term(term_code, term_desc=None, save_json=False):
    """
    Process a single term: scrape and upload to Supabase.
    
    Args:
        term_code: Term code (e.g., "202540")
        term_desc: Optional term description
        save_json: Whether to save scraped data to JSON file
    """
    print(f"\n{'='*60}")
    print(f"📚 Processing Term: {term_code} ({term_desc or 'N/A'})")
    print(f"{'='*60}\n")
    
    try:
        # Scrape courses
        courses = scrape_all_courses(term_code, max_workers=5)
        
        if not courses:
            print(f"  ⚠️  No courses found for term {term_code}")
            return 0, 0
        
        # Save to JSON if requested
        if save_json:
            filename = f"mtsac_{term_code}.json"
            with open(filename, 'w') as f:
                json.dump(courses, f, indent=2)
            print(f"  💾 Saved to {filename}")
        
        # Upload to Supabase
        success_count, error_count = upload_courses_to_supabase(courses, term_code)
        
        print(f"\n  ✅ Term {term_code} complete!")
        print(f"     Successfully uploaded: {success_count} courses")
        if error_count > 0:
            print(f"     ❌ Errors: {error_count} courses")
        
        return success_count, error_count
        
    except Exception as e:
        print(f"  ❌ Error processing term {term_code}: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0

def main():
    """Main function to process terms"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape and upload Mt. SAC courses to Supabase')
    parser.add_argument('--terms', nargs='+', help='Specific term codes to process (e.g., 202540 202630)')
    parser.add_argument('--all-future', action='store_true', help='Process all future terms')
    parser.add_argument('--years', type=int, default=2, help='Number of years ahead to process (default: 2)')
    parser.add_argument('--save-json', action='store_true', help='Save scraped data to JSON files')
    parser.add_argument('--update-only', help='Update only this specific term code')
    
    args = parser.parse_args()
    
    print("🚀 Mt. SAC Course Scraper & Uploader")
    print("=" * 60)
    print(f"✓ Connected to Supabase")
    print(f"  URL: {SUPABASE_URL}\n")
    
    total_success = 0
    total_errors = 0
    
    if args.update_only:
        # Update single term
        success, errors = process_term(args.update_only, save_json=args.save_json)
        total_success += success
        total_errors += errors
    elif args.terms:
        # Process specific terms
        for term_code in args.terms:
            success, errors = process_term(term_code, save_json=args.save_json)
            total_success += success
            total_errors += errors
    elif args.all_future:
        # Process all future terms
        terms = generate_future_terms(years_ahead=args.years)
        print(f"📅 Found {len(terms)} terms to process\n")
        
        for term in terms:
            success, errors = process_term(term['code'], term['description'], save_json=args.save_json)
            total_success += success
            total_errors += errors
    else:
        # Default: process current and next year
        terms = generate_future_terms(years_ahead=1)
        print(f"📅 Processing {len(terms)} terms (current + next year)\n")
        
        for term in terms:
            success, errors = process_term(term['code'], term['description'], save_json=args.save_json)
            total_success += success
            total_errors += errors
    
    # Summary
    print(f"\n{'='*60}")
    print(f"🎉 ALL DONE!")
    print(f"   Total successfully uploaded: {total_success} courses")
    if total_errors > 0:
        print(f"   Total errors: {total_errors} courses")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

