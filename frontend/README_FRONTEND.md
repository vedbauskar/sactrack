# Mt. SAC Course Search Website

A modern, responsive web application for searching and viewing Mt. SAC course information.

## Features

- 🔍 **Real-time Search**: Search courses by name, subject, instructor, or CRN
- 📋 **Filter Options**: Filter by term and subject
- 📊 **Detailed Statistics**: View comprehensive course information including:
  - Enrollment statistics (enrolled, available, capacity, waitlist)
  - Instructor information
  - Meeting times and locations
  - Course details (credits, schedule type, instructional method)
  - Dates and status
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices
- 🎨 **Modern UI**: Beautiful, intuitive interface with smooth animations

## Setup

1. **Configure Supabase Connection**

   Edit `config.js` and add your Supabase anon key:
   ```javascript
   const SUPABASE_CONFIG = {
       url: "https://kqntltwvfygglpcwoymp.supabase.co",
       anonKey: "YOUR_ANON_KEY_HERE"  // Get this from Supabase dashboard
   };
   ```

   **Important**: For production, always use the anon/public key from your Supabase dashboard. The service key should never be used in frontend code.

   To get your anon key:
   1. Go to your Supabase project dashboard
   2. Navigate to Settings → API
   3. Copy the "anon public" key

2. **Open the Website**

   Simply open `index.html` in a web browser, or serve it using a local web server:

   ```bash
   # Using Python
   python3 -m http.server 8000

   # Using Node.js (if you have http-server installed)
   npx http-server

   # Then open http://localhost:8000 in your browser
   ```

## Usage

1. **Search Courses**: Type in the search bar to filter courses by:
   - Course title
   - Subject code
   - Course number
   - Instructor name
   - CRN

2. **Filter Options**: 
   - Select a term from the dropdown to show only courses from that term
   - Select a subject to show only courses from that subject
   - Click "Clear Filters" to reset all filters

3. **View Course Details**: 
   - Click on any course in the list to view detailed information
   - The details panel shows all available statistics and information
   - On mobile, the details panel opens as a full-screen overlay

## File Structure

```
website/
├── backend/            # Backend (Scraper, Scheduler)
└── frontend/           # Frontend (UI)
    ├── index.html      # Main HTML structure
    ├── styles.css      # Styling and layout
    ├── app.js          # Application logic and Supabase integration
    ├── config.js       # Supabase configuration
    └── README_FRONTEND.md  # This file
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Notes

- The website loads up to 10,000 courses by default. Adjust the limit in `app.js` if needed.
- Courses are sorted by term (newest first), then by subject and course number.
- The search is case-insensitive and searches across multiple fields simultaneously.

