# Backend Updates - New Course Fields

This update adds three new fields to the course data:

1. **Prerequisites** - Course prerequisites or advisories
2. **Course Description** - Full course description from the catalog
3. **UC Credit Limitation** - Boolean flag indicating if the course has UC transfer limitations

## Changes Made

### 1. Updated Files

#### `scraper.py`
- Added `fetch_course_description()` function that retrieves prerequisites and course descriptions from the Mt. SAC API
- Uses the endpoint: `/StudentRegistrationSsb/ssb/searchResults/getCourseDescription`
- Parses HTML response to extract prerequisites (Advisory/Prerequisite/Corequisite) and description text

#### `orchestrator.py`
- Updated `transform_course()` to:
  - Check for UC Credit Limitation (UCCL) in sectionAttributes
  - Add placeholders for prerequisites and course_description fields
- Updated `upload_courses_to_supabase()` to:
  - Fetch course descriptions and prerequisites for each course
  - Add rate limiting (0.5s delay every 20 courses) to avoid overwhelming the API
  - New parameter `fetch_descriptions=True` to control whether to fetch descriptions

### 2. Database Schema Changes

Run the SQL migration in `add_new_columns.sql` in your Supabase SQL Editor to add the new columns:

```sql
-- Add three new columns
ALTER TABLE courses ADD COLUMN IF NOT EXISTS prerequisites TEXT;
ALTER TABLE courses ADD COLUMN IF NOT EXISTS course_description TEXT;
ALTER TABLE courses ADD COLUMN IF NOT EXISTS has_uc_credit_limitation BOOLEAN DEFAULT FALSE;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_courses_uc_credit_limitation 
ON courses(has_uc_credit_limitation) 
WHERE has_uc_credit_limitation = TRUE;
```

## How to Update Existing Data

### Step 1: Run the SQL Migration

1. Go to your Supabase dashboard
2. Open the SQL Editor
3. Copy and paste the contents of `add_new_columns.sql`
4. Click "Run"

### Step 2: Re-run the Orchestrator

To update all your existing course data with the new fields:

```bash
# Update a specific term
python3 orchestrator.py --update-only 202540

# Or update all future terms
python3 orchestrator.py --all-future --years 2
```

**Note**: Fetching descriptions will take longer than before because each course requires an additional API call. For example:
- ~2000 courses will take approximately 5-10 minutes
- Progress updates will be shown every 20 courses

### Step 3: Verify the Update

You can verify the update worked by checking a few courses in Supabase:

```sql
-- Check courses with UC Credit Limitation
SELECT subject, course_number, title, has_uc_credit_limitation 
FROM courses 
WHERE has_uc_credit_limitation = TRUE 
LIMIT 10;

-- Check courses with prerequisites
SELECT subject, course_number, title, prerequisites 
FROM courses 
WHERE prerequisites IS NOT NULL 
LIMIT 10;

-- Check courses with descriptions
SELECT subject, course_number, title, LEFT(course_description, 100) as description_preview
FROM courses 
WHERE course_description IS NOT NULL 
LIMIT 10;
```

## API Details

### UC Credit Limitation Detection
- Automatically detected from the `sectionAttributes` array in the course data
- Looks for attribute code `UCCL` or description containing "UC Credit Limitation"
- No additional API calls needed

### Prerequisites & Description Fetching
- **Endpoint**: `GET /StudentRegistrationSsb/ssb/searchResults/getCourseDescription?term={term}&courseReferenceNumber={crn}`
- **Response**: HTML containing prerequisites and description
- **Parsing Logic**:
  - Prerequisites: Extracted from `<b>Advisory/Prerequisite/Corequisite:</b><i>...</i>` sections
  - Description: Remaining text after removing HTML tags and prerequisite sections

## Testing

Test scripts are provided to verify the functionality:

```bash
# Test the transformation with new fields
python3 test_new_fields.py

# Test the description fetching API
python3 test_description_api.py
```

## Performance Considerations

- **Description Fetching**: Adds ~1-2 seconds per 20 courses (with rate limiting)
- **Recommended**: Run updates during off-peak hours for large datasets
- **Option**: You can disable description fetching by setting `fetch_descriptions=False` if you only want to update the UC Credit Limitation flags

## Example Output

When running the orchestrator with the new fields:

```
🔄 Transforming 2000 courses...
📖 Fetching course descriptions and prerequisites...
  Fetched 20/2000 descriptions...
  Fetched 40/2000 descriptions...
  ...
  ✓ Fetched descriptions for 1998 courses
  ⚠️  2 courses failed to fetch descriptions
💾 Uploading 2000 courses to Supabase...
  ✓ Uploaded batch 1/20 (100 courses)
  ...
```

## Frontend Integration

You'll need to update your frontend TypeScript interfaces to include the new fields:

```typescript
interface Course {
  // ... existing fields ...
  prerequisites?: string | null;
  course_description?: string | null;
  has_uc_credit_limitation: boolean;
}
```

Then you can display these in your course cards/details pages!
