# Scheduling Guide

Quick reference for setting up automated course updates with dynamic academic period-based scheduling.

## Quick Start (Recommended)

**Start background service:**
```bash
./start_service.sh
```

That's it! The service will:
- Automatically adjust scraping frequency based on academic periods:
  - **Registration Period** (2-3 weeks before semester): Scrape every 15-30 minutes
  - **Add/Drop Period** (1-2 weeks after semester start): Scrape every 1-2 hours
  - **Normal Times** (rest of semester): Scrape once daily
  - **Summer/Winter Break**: Scrape once weekly
- Automatically process all future terms (2 years ahead)
- Catch new terms as they become available
- No manual configuration needed

**Stop service:**
```bash
./stop_service.sh
```

## All Options

### 1. Background Service (Dynamic Scheduling)

**Start:**
```bash
python3 scheduler.py --service
```

**More years ahead:**
```bash
python3 scheduler.py --service --years 3
```

The service automatically detects the current academic period and adjusts scraping frequency accordingly.

### 2. Manual Test Run

**Test the scheduler:**
```bash
python3 scheduler.py --once
```

This runs once and exits (useful for testing).

## How It Works

The scheduler automatically:
1. Detects the current academic period (Registration, Add/Drop, Normal, or Break)
2. Adjusts scraping frequency based on the period:
   - **Registration Period**: Every 15-30 minutes (high frequency for course availability changes)
   - **Add/Drop Period**: Every 1-2 hours (moderate frequency during active enrollment)
   - **Normal Times**: Once daily (standard maintenance updates)
   - **Summer/Winter Break**: Once weekly (minimal updates during breaks)
3. Generates all term codes for current + future years
4. Checks which terms are available
5. Scrapes and uploads all available courses
6. Skips unavailable terms (like future terms not yet published)

**No manual term configuration needed!** As new terms become available (e.g., Fall 2027), they'll be automatically detected and processed.

## Academic Period Detection

The scheduler estimates academic periods based on typical semester start dates:
- **Spring**: Late January
- **Summer**: Late May
- **Fall**: Late August
- **Winter**: Mid-December

Periods are calculated as:
- **Registration**: 2-3 weeks before semester start
- **Add/Drop**: First 1-2 weeks of semester
- **Normal**: Rest of the semester
- **Break**: After semester ends until registration begins

*Note: You may need to adjust the semester start dates in `scheduler.py` if Mt. SAC's calendar differs significantly.*

## Troubleshooting

**Check if service is running:**
```bash
ps aux | grep scheduler.py
```

**View logs:**
```bash
tail -f logs/scheduler_$(date +%Y%m%d).log
```

**Check service output:**
```bash
tail -f logs/service.log
```

**Test manually:**
```bash
python3 orchestrator.py --all-future --years 2
```

**Check current period detection:**
The scheduler logs the current period and scraping frequency when it starts or when the period changes. Look for messages like:
```
📅 Period changed: Registration Period
   Scraping frequency: every 15-30 minutes
   Next update in: 20 minutes
```
