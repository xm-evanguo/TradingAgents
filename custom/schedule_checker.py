#!/usr/bin/env python3
"""
Schedule Determination Script for TradingAgents

This script determines whether trading analysis should run based on:
1. Current day is a weekday (Monday-Friday)
2. Current day is not a US market holiday
3. Optional time window restrictions

The script can be used in cron jobs to conditionally run analysis only when markets are open.

Usage:
    python schedule_checker.py [--config config.json] [--run-analysis] [--check-only]
"""

import datetime
import sys
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import argparse
import subprocess

# US Market holidays for 2024-2026 (extend as needed)
US_MARKET_HOLIDAYS = {
    # 2024
    "2024-01-01": "New Year's Day",
    "2024-01-15": "Martin Luther King Jr. Day", 
    "2024-02-19": "Presidents Day",
    "2024-03-29": "Good Friday",
    "2024-05-27": "Memorial Day",
    "2024-06-19": "Juneteenth",
    "2024-07-04": "Independence Day",
    "2024-09-02": "Labor Day",
    "2024-11-28": "Thanksgiving Day",
    "2024-11-29": "Day after Thanksgiving",
    "2024-12-25": "Christmas Day",
    
    # 2025
    "2025-01-01": "New Year's Day",
    "2025-01-20": "Martin Luther King Jr. Day",
    "2025-02-17": "Presidents Day", 
    "2025-04-18": "Good Friday",
    "2025-05-26": "Memorial Day",
    "2025-06-19": "Juneteenth",
    "2025-07-04": "Independence Day",
    "2025-09-01": "Labor Day",
    "2025-11-27": "Thanksgiving Day",
    "2025-11-28": "Day after Thanksgiving",
    "2025-12-25": "Christmas Day",
    
    # 2026
    "2026-01-01": "New Year's Day",
    "2026-01-19": "Martin Luther King Jr. Day",
    "2026-02-16": "Presidents Day",
    "2026-04-03": "Good Friday", 
    "2026-05-25": "Memorial Day",
    "2026-06-19": "Juneteenth",
    "2026-07-03": "Independence Day (observed)",
    "2026-09-07": "Labor Day",
    "2026-11-26": "Thanksgiving Day", 
    "2026-11-27": "Day after Thanksgiving",
    "2026-12-25": "Christmas Day"
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScheduleChecker:
    """Check if trading analysis should run based on market schedule."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize schedule checker.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config = self.load_config(config_path) if config_path else {}
        self.holidays = US_MARKET_HOLIDAYS.copy()
        
        # Add custom holidays from config
        custom_holidays = self.config.get('custom_holidays', {})
        self.holidays.update(custom_holidays)
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {config_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            return {}
    
    def is_weekday(self, date: datetime.date = None) -> bool:
        """
        Check if the given date is a weekday (Monday-Friday).
        
        Args:
            date: Date to check (default: today)
            
        Returns:
            True if weekday, False if weekend
        """
        if date is None:
            date = datetime.date.today()
        
        # Monday = 0, Sunday = 6
        return date.weekday() < 5
    
    def is_market_holiday(self, date: datetime.date = None) -> bool:
        """
        Check if the given date is a US market holiday.
        
        Args:
            date: Date to check (default: today)
            
        Returns:
            True if market holiday, False otherwise
        """
        if date is None:
            date = datetime.date.today()
        
        date_str = date.strftime("%Y-%m-%d")
        return date_str in self.holidays
    
    def get_holiday_name(self, date: datetime.date = None) -> Optional[str]:
        """
        Get the name of the holiday if the date is a market holiday.
        
        Args:
            date: Date to check (default: today)
            
        Returns:
            Holiday name if it's a holiday, None otherwise
        """
        if date is None:
            date = datetime.date.today()
        
        date_str = date.strftime("%Y-%m-%d")
        return self.holidays.get(date_str)
    
    def is_in_time_window(self, current_time: datetime.time = None) -> bool:
        """
        Check if current time is within allowed execution window.
        
        Args:
            current_time: Time to check (default: now)
            
        Returns:
            True if within allowed window, False otherwise
        """
        time_window = self.config.get('time_window')
        if not time_window:
            return True  # No time restrictions
        
        if current_time is None:
            current_time = datetime.datetime.now().time()
        
        start_time_str = time_window.get('start', '00:00')
        end_time_str = time_window.get('end', '23:59')
        
        try:
            start_time = datetime.time.fromisoformat(start_time_str)
            end_time = datetime.time.fromisoformat(end_time_str)
            
            if start_time <= end_time:
                # Same day window
                return start_time <= current_time <= end_time
            else:
                # Overnight window (e.g., 22:00 to 06:00)
                return current_time >= start_time or current_time <= end_time
                
        except ValueError as e:
            logger.error(f"Invalid time format in config: {e}")
            return True  # Default to allowing execution
    
    def should_run_analysis(
        self,
        date: datetime.date = None,
        time: datetime.time = None,
        check_time_window: bool = True
    ) -> Dict[str, Any]:
        """
        Determine if analysis should run based on all criteria.
        
        Args:
            date: Date to check (default: today)
            time: Time to check (default: now)
            check_time_window: Whether to check time window restrictions
            
        Returns:
            Dictionary with decision and reasoning
        """
        if date is None:
            date = datetime.date.today()
        if time is None:
            time = datetime.datetime.now().time()
        
        result = {
            'should_run': True,
            'date': date.strftime("%Y-%m-%d"),
            'time': time.strftime("%H:%M:%S"),
            'day_of_week': date.strftime("%A"),
            'reasons': [],
            'blocking_reasons': []
        }
        
        # Check if it's a weekday
        if not self.is_weekday(date):
            result['should_run'] = False
            result['blocking_reasons'].append(f"Weekend day ({result['day_of_week']})")
        else:
            result['reasons'].append(f"Weekday ({result['day_of_week']})")
        
        # Check if it's a market holiday
        holiday_name = self.get_holiday_name(date)
        if holiday_name:
            result['should_run'] = False
            result['blocking_reasons'].append(f"Market holiday ({holiday_name})")
        else:
            result['reasons'].append("Not a market holiday")
        
        # Check time window if requested
        if check_time_window:
            if not self.is_in_time_window(time):
                result['should_run'] = False
                result['blocking_reasons'].append("Outside allowed time window")
            else:
                result['reasons'].append("Within allowed time window")
        
        return result
    
    def get_next_trading_day(self, start_date: datetime.date = None) -> datetime.date:
        """
        Get the next trading day (weekday that's not a holiday).
        
        Args:
            start_date: Starting date (default: today)
            
        Returns:
            Next trading day
        """
        if start_date is None:
            start_date = datetime.date.today()
        
        current_date = start_date
        max_days = 10  # Prevent infinite loop
        
        for _ in range(max_days):
            current_date += datetime.timedelta(days=1)
            
            if self.is_weekday(current_date) and not self.is_market_holiday(current_date):
                return current_date
        
        # Fallback - just return next weekday
        while current_date.weekday() >= 5:
            current_date += datetime.timedelta(days=1)
        
        return current_date
    
    def get_previous_trading_day(self, start_date: datetime.date = None) -> datetime.date:
        """
        Get the previous trading day (weekday that's not a holiday).
        
        Args:
            start_date: Starting date (default: today)
            
        Returns:
            Previous trading day
        """
        if start_date is None:
            start_date = datetime.date.today()
        
        current_date = start_date
        max_days = 10  # Prevent infinite loop
        
        for _ in range(max_days):
            current_date -= datetime.timedelta(days=1)
            
            if self.is_weekday(current_date) and not self.is_market_holiday(current_date):
                return current_date
        
        # Fallback - just return previous weekday
        while current_date.weekday() >= 5:
            current_date -= datetime.timedelta(days=1)
        
        return current_date


def run_batch_analysis(config_path: str = "analysis_config.json") -> int:
    """
    Run the batch analysis script.
    
    Args:
        config_path: Path to analysis configuration file
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        logger.info("Starting batch analysis...")
        
        # Check if batch analysis script exists
        script_dir = Path(__file__).parent
        batch_script = script_dir / "batch_analysis.py"
        if not batch_script.exists():
            logger.error("batch_analysis.py not found in custom directory")
            return 1
        
        # Run batch analysis
        cmd = [sys.executable, str(batch_script), "--config", config_path, "--email"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Batch analysis completed successfully")
            if result.stdout:
                logger.info(f"Output: {result.stdout}")
        else:
            logger.error(f"Batch analysis failed with exit code {result.returncode}")
            if result.stderr:
                logger.error(f"Error: {result.stderr}")
        
        return result.returncode
        
    except Exception as e:
        logger.error(f"Error running batch analysis: {e}")
        return 1


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(description="TradingAgents Schedule Checker")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--analysis-config", default="analysis_config.json", help="Analysis configuration file")
    parser.add_argument("--check-only", action="store_true", help="Only check schedule, don't run analysis")
    parser.add_argument("--run-analysis", action="store_true", help="Run analysis if schedule allows")
    parser.add_argument("--force", action="store_true", help="Force run analysis regardless of schedule")
    parser.add_argument("--date", help="Check specific date (YYYY-MM-DD)")
    parser.add_argument("--time", help="Check specific time (HH:MM)")
    parser.add_argument("--next-trading-day", action="store_true", help="Show next trading day")
    parser.add_argument("--previous-trading-day", action="store_true", help="Show previous trading day")
    
    args = parser.parse_args()
    
    try:
        # Create schedule checker
        checker = ScheduleChecker(args.config)
        
        # Parse date and time if provided
        check_date = None
        check_time = None
        
        if args.date:
            try:
                check_date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
            except ValueError:
                logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
                return 1
        
        if args.time:
            try:
                check_time = datetime.time.fromisoformat(args.time)
            except ValueError:
                logger.error(f"Invalid time format: {args.time}. Use HH:MM")
                return 1
        
        # Handle special commands
        if args.next_trading_day:
            next_day = checker.get_next_trading_day(check_date)
            print(f"Next trading day: {next_day.strftime('%Y-%m-%d (%A)')}")
            return 0
        
        if args.previous_trading_day:
            prev_day = checker.get_previous_trading_day(check_date)
            print(f"Previous trading day: {prev_day.strftime('%Y-%m-%d (%A)')}")
            return 0
        
        # Check schedule
        decision = checker.should_run_analysis(check_date, check_time)
        
        # Print results
        logger.info(f"Schedule check for {decision['date']} {decision['time']}")
        logger.info(f"Day: {decision['day_of_week']}")
        
        if decision['should_run']:
            logger.info("✅ Analysis SHOULD run")
            for reason in decision['reasons']:
                logger.info(f"  ✓ {reason}")
        else:
            logger.info("❌ Analysis should NOT run")
            for reason in decision['blocking_reasons']:
                logger.info(f"  ✗ {reason}")
        
        # Run analysis if requested and allowed (or forced)
        if args.run_analysis or args.force:
            if decision['should_run'] or args.force:
                if args.force and not decision['should_run']:
                    logger.warning("Forcing analysis run despite schedule restrictions")
                
                exit_code = run_batch_analysis(args.analysis_config)
                return exit_code
            else:
                logger.info("Skipping analysis due to schedule restrictions")
                return 0
        
        # For check-only mode, return appropriate exit code
        if args.check_only:
            return 0 if decision['should_run'] else 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Schedule checker failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
