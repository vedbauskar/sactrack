# scraper.py
import requests
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def setup_session(term_code, base_url):
    """Set up session with Mt. SAC and return session + headers"""
    session = requests.Session()
    session.get(f"{base_url}/term/termSelection?mode=search")
    session.post(f"{base_url}/term/search?mode=search", data={"term": term_code})
    response = session.get(f"{base_url}/classSearch/classSearch")
    
    token_match = re.search(r'<meta name="synchronizerToken" content="([^"]+)"', response.text)
    sync_token = token_match.group(1)
    
    headers = {
        'X-Synchronizer-Token': sync_token,
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': f'{base_url}/classSearch/classSearch'
    }
    
    return session, headers

def search_subject(subject, term_code):
    """Search a single subject with fresh session"""
    try:
        base_url = "https://prodrg.mtsac.edu/StudentRegistrationSsb/ssb"
        session, headers = setup_session(term_code, base_url)
        
        # Search
        search_url = f"{base_url}/searchResults/searchResults"
        form_data = {
            "txt_term": term_code,
            "txt_subject": subject['code'],
            "pageOffset": "0",
            "pageMaxSize": "500",
            "sortColumn": "subjectDescription",
            "sortDirection": "asc"
        }
        
        response = session.post(search_url, data=form_data, headers=headers)
        data = response.json()
        
        return {
            'subject': subject,
            'count': data['totalCount'],
            'courses': data.get('data', [])
        }
    except Exception as e:
        return {
            'subject': subject,
            'count': 0,
            'courses': [],
            'error': str(e)
        }

def get_subjects(term_code):
    """Get list of all subjects for a term"""
    base_url = "https://prodrg.mtsac.edu/StudentRegistrationSsb/ssb"
    session, headers = setup_session(term_code, base_url)
    
    subjects_url = f"{base_url}/classSearch/get_subject"
    response = session.get(subjects_url, params={"term": term_code, "offset": 1, "max": 500}, headers=headers)
    
    return response.json()

def search_all_courses_direct(term_code):
    """
    Search for all courses directly without needing subjects list.
    This is a fallback when get_subjects() returns empty.
    """
    try:
        base_url = "https://prodrg.mtsac.edu/StudentRegistrationSsb/ssb"
        session, headers = setup_session(term_code, base_url)
        
        # Try searching with empty subject (all courses)
        search_url = f"{base_url}/searchResults/searchResults"
        form_data = {
            "txt_term": term_code,
            "txt_subject": "",  # Empty subject to get all courses
            "pageOffset": "0",
            "pageMaxSize": "5000",  # Large page size to get all courses
            "sortColumn": "subjectDescription",
            "sortDirection": "asc"
        }
        
        response = session.post(search_url, data=form_data, headers=headers)
        data = response.json()
        
        courses = data.get('data') or []
        total_count = data.get('totalCount', 0)
        
        # If there are more courses than page size, we need to paginate
        all_courses = list(courses)
        if total_count > len(courses):
            print(f"  ⚠️  Found {total_count} total courses, but only retrieved {len(courses)} (pagination needed)")
        
        return all_courses
    except Exception as e:
        print(f"  ⚠️  Direct search failed: {e}")
        return []

def fetch_course_description(term_code, crn, session=None, headers=None):
    """
    Fetch course description and prerequisites for a specific course.
    Returns a dictionary with 'description' and 'prerequisites' keys.
    """
    base_url = "https://prodrg.mtsac.edu/StudentRegistrationSsb/ssb"
    
    # Create session if not provided
    if session is None or headers is None:
        session, headers = setup_session(term_code, base_url)
    
    desc_url = f"{base_url}/searchResults/getCourseDescription"
    params = {
        'term': term_code,
        'courseReferenceNumber': crn
    }
    
    try:
        response = session.get(desc_url, params=params, headers=headers)
        html = response.text
        
        # Parse the HTML to extract description and prerequisites
        # The format is: <b>Advisory/Prerequisite:</b><i>prereq text</i>description text
        import re
        
        description = ""
        prerequisites = None
        
        # Remove HTML tags but keep the text
        # Look for Advisory or Prerequisite sections
        prereq_match = re.search(r'&lt;b&gt;(Advisory|Prerequisite|Corequisite):?\s*&lt;/b&gt;&lt;i&gt;(.*?)&lt;/i&gt;', html, re.IGNORECASE | re.DOTALL)
        
        if prereq_match:
            prerequisites = prereq_match.group(2).strip()
            # Remove the prerequisite section from the html to get clean description
            html = html.replace(prereq_match.group(0), '')
        
        # Extract the description (remove all HTML tags)
        desc_clean = re.sub(r'&lt;.*?&gt;', '', html)
        desc_clean = re.sub(r'<.*?>', '', desc_clean)
        desc_clean = re.sub(r'\s+', ' ', desc_clean).strip()
        
        # Remove common phrases that aren't part of the actual description
        desc_clean = re.sub(r'(display course description|if there is a section description.*?|when there is no course.*?)', '', desc_clean, flags=re.IGNORECASE)
        desc_clean = desc_clean.strip()
        
        if desc_clean and desc_clean not in ['', 'None', 'N/A']:
            description = desc_clean
        
        return {
            'description': description if description else None,
            'prerequisites': prerequisites
        }
    except Exception as e:
        print(f"  ⚠️  Error fetching description for CRN {crn}: {e}")
        return {
            'description': None,
            'prerequisites': None
        }

def scrape_all_courses(term_code, max_workers=5):
    """
    Scrape all courses for a term
    Returns list of course dictionaries
    """
    print(f"🔍 Starting scrape for term {term_code}...")
    
    # Get subjects
    print("Getting subjects...")
    subjects = get_subjects(term_code)
    print(f"Found {len(subjects)} subjects\n")
    
    # If no subjects found, try direct search as fallback
    if not subjects or len(subjects) == 0:
        print("  ⚠️  No subjects found, trying direct course search...")
        all_courses = search_all_courses_direct(term_code)
        if all_courses:
            crns = set([c['courseReferenceNumber'] for c in all_courses])
            print(f"\n✅ Done! Scraped {len(all_courses)} courses ({len(crns)} unique CRNs) via direct search")
            return all_courses
        else:
            print("  ⚠️  Direct search also returned no courses")
            return []
    
    # Scrape with parallel threads
    all_courses = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(search_subject, subject, term_code): subject for subject in subjects}
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            subject = result['subject']
            
            print(f"[{i}/{len(subjects)}] {subject['code']} - {subject['description']}... ", end="")
            
            if result['count'] > 0:
                print(f"✓ {result['count']} courses")
                all_courses.extend(result['courses'])
            else:
                print("(no courses)")
    
    crns = set([c['courseReferenceNumber'] for c in all_courses])
    print(f"\n✅ Done! Scraped {len(all_courses)} courses ({len(crns)} unique CRNs)")
    
    return all_courses

# If running this file directly (for testing)
if __name__ == "__main__":
    term_code = "202540"
    courses = scrape_all_courses(term_code)
    
    # Save to JSON
    with open('mtsac_spring2026_final.json', 'w') as f:
        json.dump(courses, f, indent=2)
    
    print(f"✅ Saved to mtsac_spring2026_final.json")