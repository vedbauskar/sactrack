-- SQL script to add new columns to the courses table in Supabase
-- This adds support for prerequisites, course description, and UC Credit Limitation flag

-- Add prerequisites column (text field for prerequisites/advisories)
ALTER TABLE courses 
ADD COLUMN IF NOT EXISTS prerequisites TEXT;

-- Add course_description column (text field for course description)
ALTER TABLE courses 
ADD COLUMN IF NOT EXISTS course_description TEXT;

-- Add has_uc_credit_limitation column (boolean flag for UC Credit Limitation)
ALTER TABLE courses 
ADD COLUMN IF NOT EXISTS has_uc_credit_limitation BOOLEAN DEFAULT FALSE;

-- Add comments to document the new columns
COMMENT ON COLUMN courses.prerequisites IS 'Course prerequisites or advisories as displayed in the course catalog';
COMMENT ON COLUMN courses.course_description IS 'Full course description from the catalog';
COMMENT ON COLUMN courses.has_uc_credit_limitation IS 'Flag indicating if course has UC Credit Limitation (UCCL) attribute';

-- Create indexes for better query performance (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_courses_uc_credit_limitation 
ON courses(has_uc_credit_limitation) 
WHERE has_uc_credit_limitation = TRUE;

-- Note: Run this SQL in the Supabase SQL Editor
-- After running, all existing courses will have NULL for prerequisites and course_description,
-- and FALSE for has_uc_credit_limitation until you re-run the orchestrator to update them.
