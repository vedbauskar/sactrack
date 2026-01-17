# sactrack <br><br>
Sactrak is a course discovery and scheduling website built for a local community college. The goal is to make finding classes faster clearer and more intuitive for students.

Inspired by tools like Berkeleytime and the UC Davis catalog Sactrak focuses on simplicity usability and real time data.

## What Sactrak Does

Sactrak provides a searchable course catalog powered by live academic data. Students can explore classes using filters and sorting tools that reduce friction when planning schedules.

### Features

- Search by course title course number or instructor  
- Filter by academic term department and number of credits  
- Filter by meeting days time ranges and grading option  
- Sort results by relevance open seats or units  
- Clean readable course cards with essential class information  

## How It Works

The backend collects and normalizes thousands of course listings and stores them in a structured database. This data is kept up to date automatically.

The frontend reads directly from the database and presents the information through a modern responsive interface built for discovery rather than administration.

### Architecture

Backend responsibilities  
- Data scraping  
- Data transformation  
- Automated updates  

Frontend responsibilities  
- Search and filtering  
- Sorting and browsing  
- User focused design  

Supabase acts as the shared data layer between backend and frontend.

## Tech Stack

### Backend
- Python  
- Supabase  

### Frontend
- Next.js  
- Supabase client  

## Project Status

Sactrak is actively developed as a portfolio and learning project focused on full stack architecture data pipelines and user experience design.

## Motivation

College course catalogs are often slow cluttered and difficult to navigate. Sactrak explores how better data organization and interface design can significantly improve the student experience.
