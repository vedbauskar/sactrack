# Mt. SAC Course Scraper & Database Updater

Automated system for scraping Mt. SAC course data and uploading to Supabase.

## Features

- ✅ Scrape courses from Mt. SAC registration system
- ✅ Upload to Supabase with automatic upserts
- ✅ Support for multiple terms (current + future)
- ✅ Automatic term detection
- ✅ Scheduled updates
- ✅ Batch processing for efficiency

## Setup

1. Install dependencies:
```bash
pip install -r req.txt
```

2. Configure Supabase credentials in `secrets.py`

## Usage

### Manual Updates

**Update specific term:**
```bash
python orchestrator.py --terms 202540 202630
```

**Update current and next year:**
```bash
python orchestrator.py
```

**Update all future terms (2 years ahead):**
```bash
python orchestrator.py --all-future --years 2
```

**Update single term only:**
```bash
python orchestrator.py --update-only 202540
```

**Save JSON files while processing:**
```bash
python orchestrator.py --all-future --save-json
```

### Automated Scheduling

The scheduler automatically processes **all future terms** (2 years ahead by default) to catch new terms as they become available. It uses **dynamic scheduling** that adjusts scraping frequency based on academic periods. No manual configuration needed!

#### Dynamic Academic Period-Based Scheduling

The scheduler automatically detects the current academic period and adjusts scraping frequency:

- **Registration Period** (2-3 weeks before semester): Scrape every **15-30 minutes**
- **Add/Drop Period** (1-2 weeks after semester start): Scrape every **1-2 hours**
- **Normal Times** (rest of semester): Scrape **once daily**
- **Summer/Winter Break**: Scrape **once weekly**

#### Start the Service

**Using the helper script (easiest):**
```bash
./start_service.sh
```

**Or manually:**
```bash
python3 scheduler.py --service
```

**With custom settings:**
```bash
# Process 3 years ahead instead of 2
python3 scheduler.py --service --years 3
```

**Stop the service:**
```bash
./stop_service.sh
```

**Check if running:**
```bash
ps aux | grep scheduler.py
```

**Manual test run:**
```bash
python3 scheduler.py --once
```

The service will:
- Automatically detect the current academic period
- Adjust scraping frequency based on the period
- Automatically process all available terms (current + future)
- Catch new terms as they become available
- Log all activity to `logs/scheduler_YYYYMMDD.log`

## Term Codes

Mt. SAC uses term codes in format `YYYYTT`:
- `10` = Winter
- `30` = Fall  
- `40` = Spring
- `50` = Summer

Example: `202540` = Spring 2025

## Files

- `orchestrator.py` - Main script that combines scraping and uploading
- `scraper.py` - Course scraping logic with fallback direct search
- `scheduler.py` - Automated scheduler with dynamic academic period-based scheduling
- `start_service.sh` - Helper script to start background service
- `stop_service.sh` - Helper script to stop background service
- `main.py` - Original upload script (legacy)
- `secrets.py` - Supabase credentials

## Frontend

Frontend files (HTML, JS, CSS) are located in the `frontend/` directory. See `frontend/README_FRONTEND.md` for details.

## Logs

- Scheduled runs: `logs/scheduler_YYYYMMDD.log`
- Service output: `logs/service.log` (when running as background service)

## Automatic Future Term Handling

The scheduler is configured to automatically:
- ✅ Process all available terms (current + future)
- ✅ Catch new terms as they become available (no manual updates needed)
- ✅ Skip unavailable terms gracefully
- ✅ Update existing courses and add new ones via upsert

By default, it processes **2 years ahead**, which covers:
- Current semester
- Next semester
- All future semesters for the next 2 years

This means you never need to manually add new terms - they'll be automatically detected and processed!

