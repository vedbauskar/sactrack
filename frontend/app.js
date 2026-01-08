// Initialize Supabase client
import { createClient } from 'https://cdn.skypack.dev/@supabase/supabase-js@2';
import { SUPABASE_CONFIG } from './config.js';

// Initialize Supabase client
const supabase = createClient(
    SUPABASE_CONFIG.url,
    SUPABASE_CONFIG.anonKey
);

console.log('✅ Supabase initialized');
console.log('Testing connection...');

// Test connection
supabase.from('courses').select('*', { count: 'exact' }).limit(1).then(({ data, error, count }) => {
    if (error) {
        console.error('❌ Connection error:', error);
        alert('Cannot connect to database: ' + error.message);
    } else {
        console.log('✅ Successfully connected!');
        console.log('Total courses in database:', count);
        console.log('Sample:', data);
    }
});

// ... rest of your existing app.js code below (don't change anything else)

// State
let allCourses = [];
let filteredCourses = [];
let selectedCourse = null;
let uniqueTerms = new Set();
let uniqueSubjects = new Set();

// DOM elements
const searchInput = document.getElementById('searchInput');
const termFilter = document.getElementById('termFilter');
const subjectFilter = document.getElementById('subjectFilter');
const clearFiltersBtn = document.getElementById('clearFilters');
const coursesList = document.getElementById('coursesList');
const courseDetails = document.getElementById('courseDetails');
const courseCount = document.getElementById('courseCount');
const loadingIndicator = document.getElementById('loadingIndicator');
const detailsPanel = document.getElementById('detailsPanel');
const closeDetailsBtn = document.getElementById('closeDetails');

// Format time from HHMM to HH:MM AM/PM
function formatTime(timeStr) {
    if (!timeStr) return 'N/A';
    const time = timeStr.toString().padStart(4, '0');
    const hours = parseInt(time.substring(0, 2));
    const minutes = time.substring(2, 4);
    const period = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours > 12 ? hours - 12 : (hours === 0 ? 12 : hours);
    return `${displayHours}:${minutes} ${period}`;
}

// Format date from YYYYMMDD to readable format
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    try {
        const year = dateStr.substring(0, 4);
        const month = dateStr.substring(4, 6);
        const day = dateStr.substring(6, 8);
        const date = new Date(year, month - 1, day);
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    } catch (e) {
        return dateStr;
    }
}

// Get credit value - use credits_high if available, otherwise credits_low
function getCredits(course) {
    let val = null;
    if (course.credits_high !== null && course.credits_high !== undefined) {
        val = course.credits_high;
    } else if (course.credits_low !== null && course.credits_low !== undefined) {
        val = course.credits_low;
    }

    if (val === 0) return "not publicly displayed";
    return val;
}

// Group courses by subject + course_number
function groupCoursesBySubjectAndNumber(courses) {
    const grouped = {};

    courses.forEach(course => {
        const key = `${course.subject || ''}_${course.course_number || ''}`;
        if (!grouped[key]) {
            grouped[key] = {
                subject: course.subject,
                course_number: course.course_number,
                title: course.title,
                term_desc: course.term_desc,
                sections: []
            };
        }
        grouped[key].sections.push(course);
    });

    // Sort sections within each group
    Object.keys(grouped).forEach(key => {
        grouped[key].sections.sort((a, b) => {
            const sectionA = a.section || '';
            const sectionB = b.section || '';
            return sectionA.localeCompare(sectionB);
        });
    });

    return Object.values(grouped);
}

// Load courses from Supabase
async function loadCourses() {
    try {
        loadingIndicator.style.display = 'block';
        coursesList.innerHTML = '';

        // Fetch data in chunks to handle large datasets (Supabase max limit is often 1000)
        let allFetchedData = [];
        let from = 0;
        const step = 1000;
        let hasMore = true;

        while (hasMore) {
            // Update loading text
            if (allFetchedData.length > 0) {
                loadingIndicator.textContent = `Loading courses... (${allFetchedData.length} loaded)`;
            }

            const { data, error } = await supabase
                .from('courses')
                .select('*')
                .order('term', { ascending: false })
                .order('subject', { ascending: true })
                .order('course_number', { ascending: true })
                .range(from, from + step - 1);

            if (error) throw error;

            if (data && data.length > 0) {
                allFetchedData = [...allFetchedData, ...data];
                from += step;
                if (data.length < step) hasMore = false;
            } else {
                hasMore = false;
            }
        }

        allCourses = allFetchedData;
        filteredCourses = [...allCourses];

        // Extract unique terms and subjects
        allCourses.forEach(course => {
            if (course.term_desc) uniqueTerms.add(course.term_desc);
            if (course.subject) uniqueSubjects.add(course.subject);
        });

        // Populate filters
        populateFilters();
        renderCourses();
        updateCourseCount();

        loadingIndicator.style.display = 'none';
    } catch (error) {
        console.error('Error loading courses:', error);
        loadingIndicator.innerHTML = `<p style="color: var(--danger);">Error loading courses: ${error.message}</p>`;
    }
}

// Populate filter dropdowns
function populateFilters() {
    // Populate terms
    termFilter.innerHTML = '<option value="">All Terms</option>';
    Array.from(uniqueTerms).sort().forEach(term => {
        const option = document.createElement('option');
        option.value = term;
        option.textContent = term;
        termFilter.appendChild(option);
    });

    // Populate subjects
    subjectFilter.innerHTML = '<option value="">All Subjects</option>';
    Array.from(uniqueSubjects).sort().forEach(subject => {
        const option = document.createElement('option');
        option.value = subject;
        option.textContent = subject;
        subjectFilter.appendChild(option);
    });
}

// Filter courses based on search and filters
function filterCourses() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    const selectedTerm = termFilter.value;
    const selectedSubject = subjectFilter.value;

    filteredCourses = allCourses.filter(course => {
        // Search filter
        const matchesSearch = !searchTerm ||
            (course.title && course.title.toLowerCase().includes(searchTerm)) ||
            (course.subject && course.subject.toLowerCase().includes(searchTerm)) ||
            (course.course_number && course.course_number.toString().includes(searchTerm)) ||
            (course.instructor_name && course.instructor_name.toLowerCase().includes(searchTerm)) ||
            (course.crn && course.crn.toString().includes(searchTerm));

        // Term filter
        const matchesTerm = !selectedTerm || course.term_desc === selectedTerm;

        // Subject filter
        const matchesSubject = !selectedSubject || course.subject === selectedSubject;

        return matchesSearch && matchesTerm && matchesSubject;
    });

    renderCourses();
    updateCourseCount();
}

// Render courses list
function renderCourses() {
    if (filteredCourses.length === 0) {
        coursesList.innerHTML = '<p style="text-align: center; padding: 2rem; color: var(--text-secondary);">No courses found</p>';
        return;
    }

    // Group courses by subject + course_number
    const groupedCourses = groupCoursesBySubjectAndNumber(filteredCourses);

    coursesList.innerHTML = groupedCourses.map(group => {
        const credits = getCredits(group.sections[0]);
        const openSections = group.sections.filter(s => s.open_section);
        const totalSections = group.sections.length;
        const hasOpenSections = openSections.length > 0;

        // Get unique instructors
        const instructors = [...new Set(group.sections.map(s => s.instructor_name || 'TBA'))];
        const instructorDisplay = instructors.length <= 2
            ? instructors.join(', ')
            : `${instructors[0]} and ${instructors.length - 1} others`;

        return `
            <div class="course-group" data-key="${group.subject}_${group.course_number}">
                <div class="course-item-header">
                    <div style="flex: 1;">
                        <div class="course-title">${group.title || 'N/A'}</div>
                        <div class="course-code">${group.subject || ''} ${group.course_number || ''}</div>
                        ${credits !== null ? `<div style="margin-top: 0.5rem; color: var(--text-secondary); font-size: 0.9rem;">📚 ${credits === "not publicly displayed" ? credits : `${credits} ${credits === 1 ? 'credit' : 'credits'}`}</div>` : ''}
                    </div>
                    <div style="text-align: right;">
                        <span class="status-badge ${hasOpenSections ? 'status-open' : 'status-closed'}">
                            ${openSections.length}/${totalSections} Open
                        </span>
                    </div>
                </div>
                <div class="course-meta">
                    <span>📅 ${group.term_desc || 'N/A'}</span>
                    <span>👤 ${instructorDisplay}</span>
                    <span>📋 ${totalSections} ${totalSections === 1 ? 'section' : 'sections'}</span>
                </div>
                <div class="sections-list" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border);">
                    ${group.sections.map(section => {
            const isSelected = selectedCourse && selectedCourse.crn === section.crn;
            const sectionStatusClass = section.open_section ? 'status-open' : 'status-closed';
            const sectionStatusText = section.open_section ? 'Open' : 'Closed';
            const sectionCredits = getCredits(section);

            return `
                            <div class="section-item ${isSelected ? 'selected' : ''}" data-crn="${section.crn}" style="padding: 0.75rem; margin-bottom: 0.5rem; border: 1px solid var(--border); border-radius: 8px; cursor: pointer; transition: all 0.2s ease; background: ${isSelected ? 'rgba(99, 102, 241, 0.05)' : 'var(--background)'};">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                    <div>
                                        <strong>Section ${section.section || 'N/A'}</strong>
                                        <span style="color: var(--text-secondary); margin-left: 0.5rem;">CRN: ${section.crn || 'N/A'}</span>
                                    </div>
                                    <span class="status-badge ${sectionStatusClass}" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">${sectionStatusText}</span>
                                </div>
                                <div style="display: flex; gap: 1rem; flex-wrap: wrap; font-size: 0.85rem; color: var(--text-secondary);">
                                    <span>👤 ${section.instructor_name || 'TBA'}</span>
                                    ${section.meeting_days ? `<span>📆 ${section.meeting_days}</span>` : ''}
                                    ${section.meeting_time_start ? `<span>⏰ ${formatTime(section.meeting_time_start)}</span>` : ''}
                                    ${section.campus ? `<span>📍 ${section.campus}</span>` : ''}
                                    ${section.seats_available !== null ? `<span>🪑 ${section.seats_available} available</span>` : ''}
                                    ${(section.seats_available >= 9000 || section.max_enrollment >= 9000) ? '<span style="color: var(--text-secondary); font-style: italic;">⚠️ For disability students</span>' : ''}
                                </div>
                            </div>
                        `;
        }).join('')}
                </div>
            </div>
        `;
    }).join('');

    // Add click listeners for sections
    document.querySelectorAll('.section-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const crn = item.dataset.crn;
            const course = filteredCourses.find(c => c.crn.toString() === crn);
            if (course) {
                selectCourse(course);
            }
        });
    });
}

// Update course count
function updateCourseCount() {
    const groupedCourses = groupCoursesBySubjectAndNumber(filteredCourses);
    const count = groupedCourses.length;
    const totalSections = filteredCourses.length;
    courseCount.textContent = `${count} ${count === 1 ? 'course' : 'courses'} (${totalSections} ${totalSections === 1 ? 'section' : 'sections'})`;
}

// Select and display course details
function selectCourse(course) {
    selectedCourse = course;
    renderCourses(); // Re-render to show selected state
    displayCourseDetails(course);

    // Show details panel on mobile
    if (window.innerWidth <= 1024) {
        detailsPanel.classList.add('active');
    }
}

// Display course details
function displayCourseDetails(course) {
    const enrollmentPercent = course.max_enrollment
        ? Math.round((course.current_enrollment / course.max_enrollment) * 100)
        : 0;

    courseDetails.innerHTML = `
        <div class="detail-section">
            <h3>${course.title || 'N/A'}</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">Course Code</div>
                    <div class="detail-value">${course.subject || 'N/A'} ${course.course_number || 'N/A'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Section</div>
                    <div class="detail-value">${course.section || 'N/A'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">CRN</div>
                    <div class="detail-value">${course.crn || 'N/A'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Term</div>
                    <div class="detail-value">${course.term_desc || 'N/A'}</div>
                </div>
            </div>
        </div>

        <div class="detail-section">
            <h3>Enrollment Statistics</h3>
            ${(course.seats_available >= 9000 || course.max_enrollment >= 9000) ? `
                <div style="background: rgba(245, 158, 11, 0.1); color: #d97706; padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; font-size: 0.9rem;">
                    ⚠️ This course may be restricted for disability students or special programs.
                </div>
            ` : ''}
            <div class="enrollment-stats">
                <div class="stat-card">
                    <div class="stat-value">${course.current_enrollment || 0}</div>
                    <div class="stat-label">Enrolled</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${course.seats_available || 0}</div>
                    <div class="stat-label">Available</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${course.max_enrollment || 0}</div>
                    <div class="stat-label">Capacity</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${enrollmentPercent}%</div>
                    <div class="stat-label">Full</div>
                </div>
            </div>
            ${course.waitlist_capacity ? `
                <div class="detail-grid" style="margin-top: 1rem;">
                    <div class="detail-item">
                        <div class="detail-label">Waitlist Capacity</div>
                        <div class="detail-value">${course.waitlist_capacity}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Waitlist Count</div>
                        <div class="detail-value">${course.waitlist_count || 0}</div>
                    </div>
                </div>
            ` : ''}
        </div>

        <div class="detail-section">
            <h3>Instructor Information</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">Instructor Name</div>
                    <div class="detail-value">${course.instructor_name || 'TBA'}</div>
                </div>
                ${course.instructor_email ? `
                    <div class="detail-item">
                        <div class="detail-label">Email</div>
                        <div class="detail-value">
                            <a href="mailto:${course.instructor_email}" style="color: var(--primary-color);">
                                ${course.instructor_email}
                            </a>
                        </div>
                    </div>
                ` : ''}
            </div>
        </div>

        <div class="detail-section">
            <h3>Course Details</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">Credits</div>
                    <div class="detail-value">${getCredits(course) !== null ? getCredits(course) : 'N/A'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Schedule Type</div>
                    <div class="detail-value">${course.schedule_type || 'N/A'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Instructional Method</div>
                    <div class="detail-value">${course.instructional_method || 'N/A'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Campus</div>
                    <div class="detail-value">${course.campus || 'N/A'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Status</div>
                    <div class="detail-value">
                        <span class="status-badge ${course.open_section ? 'status-open' : 'status-closed'}">
                            ${course.open_section ? 'Open' : 'Closed'}
                        </span>
                    </div>
                </div>
            </div>
        </div>

        ${course.meeting_days || course.meeting_time_start ? `
            <div class="detail-section">
                <h3>Meeting Information</h3>
                <div class="detail-grid">
                    ${course.meeting_days ? `
                        <div class="detail-item">
                            <div class="detail-label">Days</div>
                            <div class="detail-value">${course.meeting_days}</div>
                        </div>
                    ` : ''}
                    ${course.meeting_time_start ? `
                        <div class="detail-item">
                            <div class="detail-label">Start Time</div>
                            <div class="detail-value">${formatTime(course.meeting_time_start)}</div>
                        </div>
                    ` : ''}
                    ${course.meeting_time_end ? `
                        <div class="detail-item">
                            <div class="detail-label">End Time</div>
                            <div class="detail-value">${formatTime(course.meeting_time_end)}</div>
                        </div>
                    ` : ''}
                    ${course.meeting_building ? `
                        <div class="detail-item">
                            <div class="detail-label">Building</div>
                            <div class="detail-value">${course.meeting_building}</div>
                        </div>
                    ` : ''}
                    ${course.meeting_room ? `
                        <div class="detail-item">
                            <div class="detail-label">Room</div>
                            <div class="detail-value">${course.meeting_room}</div>
                        </div>
                    ` : ''}
                </div>
            </div>
        ` : ''}

        ${course.start_date || course.end_date ? `
            <div class="detail-section">
                <h3>Dates</h3>
                <div class="detail-grid">
                    ${course.start_date ? `
                        <div class="detail-item">
                            <div class="detail-label">Start Date</div>
                            <div class="detail-value">${formatDate(course.start_date)}</div>
                        </div>
                    ` : ''}
                    ${course.end_date ? `
                        <div class="detail-item">
                            <div class="detail-label">End Date</div>
                            <div class="detail-value">${formatDate(course.end_date)}</div>
                        </div>
                    ` : ''}
                </div>
            </div>
        ` : ''}

        ${course.updated_at ? `
            <div class="detail-section">
                <div class="detail-item">
                    <div class="detail-label">Last Updated</div>
                    <div class="detail-value">${new Date(course.updated_at).toLocaleString()}</div>
                </div>
            </div>
        ` : ''}
    `;
}

// Event listeners
searchInput.addEventListener('input', filterCourses);
termFilter.addEventListener('change', filterCourses);
subjectFilter.addEventListener('change', filterCourses);

clearFiltersBtn.addEventListener('click', () => {
    searchInput.value = '';
    termFilter.value = '';
    subjectFilter.value = '';
    filterCourses();
});

closeDetailsBtn.addEventListener('click', () => {
    detailsPanel.classList.remove('active');
});

// Initialize
loadCourses();

