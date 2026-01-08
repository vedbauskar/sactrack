# scheduler.py
"""
Scheduler script for automated course updates with dynamic scheduling based on academic periods.
Supports continuous background service with adaptive scraping intervals.
"""
import subprocess
import sys
import logging
import time
import signal
from datetime import datetime, timedelta
import os

# Set up logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"scheduler_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a'),  # Append mode for daily logs
        logging.StreamHandler(sys.stdout)
    ]
)

# Global flag for graceful shutdown
running = True

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    global running
    logging.info("Received shutdown signal, stopping scheduler...")
    running = False

def get_academic_period():
    """
    Determine the current academic period based on the date.
    Returns tuple: (period_name, interval_minutes)
    
    Periods:
    - 'registration': 2-3 weeks before semester start (scrape every 15-30 minutes)
    - 'add_drop': 1-2 weeks after semester start (scrape every 1-2 hours)
    - 'normal': rest of the semester (scrape once daily)
    - 'break': summer/winter break (scrape once weekly or pause)
    """
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    current_day = now.day
    
    # Define typical semester start dates (adjust these based on actual Mt. SAC calendar)
    # Format: (month, day, season_name)
    semester_starts = [
        (1, 20, 'Spring'),    # Spring typically starts late January
        (5, 25, 'Summer'),    # Summer typically starts late May
        (8, 25, 'Fall'),      # Fall typically starts late August
        (12, 20, 'Winter'),   # Winter typically starts mid-December (for next year)
    ]
    
    # Find the current and next semester
    current_date = datetime(current_year, current_month, current_day)
    
    # Create list of semester start dates for current and next year
    semester_dates = []
    for month, day, season in semester_starts:
        # Current year
        try:
            sem_date = datetime(current_year, month, day)
            semester_dates.append((sem_date, season, current_year))
        except ValueError:
            # Handle leap year edge cases
            sem_date = datetime(current_year, month, min(day, 28))
            semester_dates.append((sem_date, season, current_year))
        
        # Next year (for winter that might be in next year)
        try:
            sem_date = datetime(current_year + 1, month, day)
            semester_dates.append((sem_date, season, current_year + 1))
        except ValueError:
            sem_date = datetime(current_year + 1, month, min(day, 28))
            semester_dates.append((sem_date, season, current_year + 1))
    
    # Sort by date
    semester_dates.sort(key=lambda x: x[0])
    
    # Find the current semester and next semester
    current_semester = None
    next_semester = None
    
    for i, (sem_date, season, year) in enumerate(semester_dates):
        if current_date < sem_date:
            if i > 0:
                current_semester = semester_dates[i - 1]
            next_semester = (sem_date, season, year)
            break
    
    # If we're past all semesters, wrap to next year
    if current_semester is None:
        current_semester = semester_dates[-1]
        next_semester = semester_dates[0]
    
    # Calculate periods
    current_sem_start, current_season, current_sem_year = current_semester
    next_sem_start, next_season, next_sem_year = next_semester
    
    # Registration period: 2-3 weeks before next semester start
    registration_start = next_sem_start - timedelta(weeks=3)
    registration_end = next_sem_start - timedelta(weeks=2)
    
    # Add/Drop period: First 1-2 weeks of current semester
    add_drop_start = current_sem_start
    add_drop_end = current_sem_start + timedelta(weeks=2)
    
    # Semester end (approximate): ~16 weeks after start
    semester_end = current_sem_start + timedelta(weeks=16)
    
    # Break period: After semester ends and before registration starts
    break_start = semester_end
    break_end = registration_start
    
    # Determine current period (check in priority order)
    if registration_start <= current_date <= registration_end:
        # Registration period: scrape every 15-30 minutes (use 20 minutes as average)
        return ('registration', 20)
    elif add_drop_start <= current_date <= add_drop_end:
        # Add/Drop period: scrape every 1-2 hours (use 90 minutes as average)
        return ('add_drop', 90)
    elif break_start <= break_end:
        # Normal break period (doesn't span year boundary)
        if break_start <= current_date <= break_end:
            return ('break', 7 * 24 * 60)  # 7 days in minutes
    else:
        # Break spans year boundary (break_start > break_end)
        if current_date >= break_start or current_date <= break_end:
            return ('break', 7 * 24 * 60)  # 7 days in minutes
    
    # Normal period: scrape once daily
    return ('normal', 24 * 60)  # 24 hours in minutes

def run_update(years_ahead=2):
    """
    Run the orchestrator to update courses.
    
    Args:
        years_ahead: Number of years ahead to process (default: 2 to catch all future terms)
    """
    try:
        logging.info("=" * 60)
        logging.info(f"Starting scheduled course update (processing {years_ahead} years ahead)")
        logging.info("=" * 60)
        
        # Run orchestrator with all future terms to automatically catch new terms
        result = subprocess.run(
            [sys.executable, "orchestrator.py", "--all-future", "--years", str(years_ahead)],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            logging.info("✅ Course update completed successfully")
            # Log summary (last few lines usually contain the summary)
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines[-10:]:  # Last 10 lines usually have summary
                if line.strip():
                    logging.info(line)
        else:
            logging.error("❌ Course update failed")
            logging.error(result.stderr)
            logging.error(result.stdout)
            return False
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Error running update: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return False

def run_as_service(years_ahead=2):
    """
    Run as a background service with dynamic scheduling based on academic periods.
    
    Args:
        years_ahead: Number of years ahead to process
    """
    try:
        import schedule
    except ImportError:
        logging.error("❌ 'schedule' library not installed. Install with: pip install schedule")
        return False
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logging.info("=" * 60)
    logging.info("🚀 Starting Mt. SAC Course Updater Service")
    logging.info("   Dynamic scheduling based on academic periods")
    logging.info(f"   Processing {years_ahead} years ahead")
    logging.info("   Press Ctrl+C to stop")
    logging.info("=" * 60)
    
    # Run immediately on startup
    logging.info("Running initial update...")
    run_update(years_ahead=years_ahead)
    
    # Track last scheduled time to detect period changes
    last_period = None
    last_scheduled_time = None
    
    # Main loop
    global running
    while running:
        # Check current period and update schedule if needed
        period, interval_minutes = get_academic_period()
        
        # If period changed or first run, reschedule
        if period != last_period or last_scheduled_time is None:
            # Clear existing schedule
            schedule.clear()
            
            # Log period change
            period_names = {
                'registration': 'Registration Period',
                'add_drop': 'Add/Drop Period',
                'normal': 'Normal Times',
                'break': 'Summer/Winter Break'
            }
            interval_desc = {
                'registration': 'every 15-30 minutes',
                'add_drop': 'every 1-2 hours',
                'normal': 'once daily',
                'break': 'once weekly'
            }
            
            logging.info("=" * 60)
            logging.info(f"📅 Period changed: {period_names.get(period, period)}")
            logging.info(f"   Scraping frequency: {interval_desc.get(period, 'unknown')}")
            logging.info(f"   Next update in: {interval_minutes} minutes")
            logging.info("=" * 60)
            
            # Schedule next update based on interval
            if interval_minutes < 60:
                # For intervals less than an hour, use minutes
                schedule.every(interval_minutes).minutes.do(run_update, years_ahead=years_ahead)
            elif interval_minutes < 24 * 60:
                # For intervals less than a day, use hours
                schedule.every(interval_minutes // 60).hours.do(run_update, years_ahead=years_ahead)
            elif interval_minutes == 24 * 60:
                # For daily, schedule at specific time (2 AM)
                schedule.every().day.at("02:00").do(run_update, years_ahead=years_ahead)
            else:
                # For weekly or longer, schedule weekly at 2 AM
                schedule.every().week.at("02:00").do(run_update, years_ahead=years_ahead)
            
            last_period = period
            last_scheduled_time = datetime.now()
        
        # Run pending scheduled tasks
        schedule.run_pending()
        
        # Check for period changes every hour
        time.sleep(60)  # Check every minute
    
    logging.info("Service stopped.")
    return True

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Schedule automated course updates with dynamic academic period-based scheduling',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run as background service (dynamic scheduling):
  python scheduler.py --service
  
  # Run as service processing 3 years ahead:
  python scheduler.py --service --years 3
  
  # Run once manually:
  python scheduler.py --once
        """
    )
    parser.add_argument('--once', action='store_true', 
                       help='Run once and exit (for manual testing)')
    parser.add_argument('--service', action='store_true',
                       help='Run as background service with dynamic scheduling')
    parser.add_argument('--years', type=int, default=2,
                       help='Number of years ahead to process (default: 2)')
    
    args = parser.parse_args()
    
    if args.service:
        # Run as background service
        run_as_service(years_ahead=args.years)
    else:
        # Run once (for manual testing)
        success = run_update(years_ahead=args.years)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
