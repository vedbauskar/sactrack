-- Create courses table
CREATE TABLE IF NOT EXISTS courses (
    crn TEXT PRIMARY KEY,
    term TEXT NOT NULL,
    term_desc TEXT,
    subject TEXT,
    course_number TEXT,
    section TEXT,
    title TEXT,
    credits_low REAL,
    credits_high REAL,
    instructor_name TEXT,
    instructor_email TEXT,
    max_enrollment INTEGER,
    current_enrollment INTEGER,
    seats_available INTEGER,
    waitlist_capacity INTEGER,
    waitlist_count INTEGER,
    open_section BOOLEAN,
    schedule_type TEXT,
    instructional_method TEXT,
    campus TEXT,
    meeting_days TEXT,
    meeting_time_start TEXT,
    meeting_time_end TEXT,
    meeting_building TEXT,
    meeting_room TEXT,
    start_date TEXT,
    end_date TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_term ON courses(term);
CREATE INDEX IF NOT EXISTS idx_subject ON courses(subject);
CREATE INDEX IF NOT EXISTS idx_open ON courses(open_section);
CREATE INDEX IF NOT EXISTS idx_subject_course ON courses(subject, course_number);

ALTER TABLE courses DISABLE ROW LEVEL SECURITY;
