#!/bin/bash

# TradingAgents Cron Job Setup Script
# 
# This script sets up a daily cron job to run TradingAgents analysis
# at 8:00 PM PST every day. The schedule checker will determine if
# analysis should actually run based on market days and holidays.
#
# Usage:
#   bash setup_cronjob.sh [--remove] [--time "0 20 * * *"] [--timezone PST]

set -e  # Exit on any error

# Default configuration
DEFAULT_CRON_TIME="0 20 * * *"  # 8:00 PM daily
DEFAULT_TIMEZONE="America/Los_Angeles"  # PST/PDT
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_COMMENT="# TradingAgents Daily Analysis"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() { echo -e "${BLUE}INFO:${NC} $1"; }
print_success() { echo -e "${GREEN}SUCCESS:${NC} $1"; }
print_warning() { echo -e "${YELLOW}WARNING:${NC} $1"; }
print_error() { echo -e "${RED}ERROR:${NC} $1"; }

# Function to show usage
show_usage() {
    echo "TradingAgents Cron Job Setup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --remove                Remove existing TradingAgents cron job"
    echo "  --time SCHEDULE         Cron time schedule (default: '$DEFAULT_CRON_TIME')"
    echo "  --timezone TIMEZONE     Timezone (default: '$DEFAULT_TIMEZONE')"
    echo "  --config CONFIG         Analysis config file (default: 'analysis_config.json')"
    echo "  --dry-run              Show what would be done without making changes"
    echo "  --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Setup with defaults (8:00 PM PST daily)"
    echo "  $0 --time '30 19 * * *'              # Setup for 7:30 PM daily"
    echo "  $0 --timezone 'America/New_York'     # Use EST/EDT timezone"
    echo "  $0 --remove                          # Remove existing cron job"
    echo ""
    echo "The cron job will run the schedule checker which determines if analysis"
    echo "should actually execute based on market hours and holidays."
}

# Function to check if required files exist
check_dependencies() {
    print_info "Checking dependencies..."
    
    local missing_files=()
    
    if [[ ! -f "$SCRIPT_DIR/schedule_checker.py" ]]; then
        missing_files+=("schedule_checker.py")
    fi
    
    if [[ ! -f "$SCRIPT_DIR/batch_analysis.py" ]]; then
        missing_files+=("batch_analysis.py")
    fi
    
    if [[ ! -f "$SCRIPT_DIR/interface.py" ]]; then
        missing_files+=("interface.py")
    fi
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        print_error "Missing required files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        echo ""
        echo "Please ensure all TradingAgents scripts are in the same directory."
        exit 1
    fi
    
    print_success "All required files found"
}

# Function to check if Python and required packages are available
check_python() {
    print_info "Checking Python environment..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed or not in PATH"
        exit 1
    fi
    
    local python_path=$(which python3)
    print_info "Using Python: $python_path"
    
    # Check if we can import required modules
    if ! python3 -c "import datetime, json, subprocess" 2>/dev/null; then
        print_error "Required Python modules not available"
        exit 1
    fi
    
    print_success "Python environment OK"
}

# Function to get current cron jobs for TradingAgents
get_existing_cronjob() {
    crontab -l 2>/dev/null | grep -E "(TradingAgents|schedule_checker\.py)" || true
}

# Function to remove existing TradingAgents cron jobs
remove_cronjob() {
    print_info "Removing existing TradingAgents cron jobs..."
    
    local existing_jobs=$(get_existing_cronjob)
    
    if [[ -z "$existing_jobs" ]]; then
        print_warning "No existing TradingAgents cron jobs found"
        return 0
    fi
    
    print_info "Found existing jobs:"
    echo "$existing_jobs"
    echo ""
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_info "[DRY RUN] Would remove the above cron jobs"
        return 0
    fi
    
    # Remove lines containing TradingAgents or schedule_checker.py
    (crontab -l 2>/dev/null | grep -vE "(TradingAgents|schedule_checker\.py)") | crontab -
    
    print_success "Removed existing TradingAgents cron jobs"
}

# Function to create the cron job
create_cronjob() {
    local cron_time="$1"
    local config_file="$2"
    
    print_info "Creating new cron job..."
    print_info "Schedule: $cron_time"
    print_info "Script directory: $SCRIPT_DIR"
    print_info "Config file: $config_file"
    
    # Ensure log directory exists
    mkdir -p "$SCRIPT_DIR/../log"
    
    # Create the cron command
    local cron_command="cd '$SCRIPT_DIR/..' && PYTHONPATH='$SCRIPT_DIR/..:$PYTHONPATH' /usr/bin/python3 custom/schedule_checker.py --run-analysis --analysis-config '$config_file' >> log/cron.log 2>&1"
    local cron_entry="$cron_time $cron_command"
    
    print_info "Cron entry:"
    echo "  $CRON_COMMENT"
    echo "  $cron_entry"
    echo ""
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_info "[DRY RUN] Would add the above cron job"
        return 0
    fi
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_COMMENT"; echo "$cron_entry") | crontab -
    
    print_success "Cron job created successfully"
}

# Function to verify cron job was created
verify_cronjob() {
    print_info "Verifying cron job..."
    
    local existing_jobs=$(get_existing_cronjob)
    
    if [[ -n "$existing_jobs" ]]; then
        print_success "Cron job verified:"
        echo "$existing_jobs"
    else
        print_error "Cron job verification failed"
        exit 1
    fi
}

# Function to test the schedule checker
test_schedule_checker() {
    print_info "Testing schedule checker..."
    
    if python3 "$SCRIPT_DIR/schedule_checker.py" --check-only; then
        print_success "Schedule checker test passed"
    else
        print_warning "Schedule checker test failed (this may be normal if today is not a trading day)"
    fi
}

# Function to show cron service status
show_cron_status() {
    print_info "Checking cron service status..."
    
    if systemctl is-active --quiet cron 2>/dev/null; then
        print_success "Cron service is running"
    elif systemctl is-active --quiet crond 2>/dev/null; then
        print_success "Crond service is running"
    elif service cron status >/dev/null 2>&1; then
        print_success "Cron service is running"
    else
        print_warning "Unable to verify cron service status"
        print_warning "Please ensure cron service is running:"
        echo "  sudo systemctl start cron    # or crond on some systems"
        echo "  sudo systemctl enable cron   # to start on boot"
    fi
}

# Function to create a sample config if it doesn't exist
create_sample_config() {
    local config_file="$1"
    
    if [[ ! -f "$config_file" ]]; then
        print_warning "Analysis config file not found: $config_file"
        print_info "Creating sample configuration..."
        
        if [[ "$DRY_RUN" == "true" ]]; then
            print_info "[DRY RUN] Would create sample config file"
            return 0
        fi
        
        # Run batch_analysis.py to create default config
        if python3 "$SCRIPT_DIR/batch_analysis.py" --config "$config_file" --no-save >/dev/null 2>&1 || true; then
            print_success "Sample configuration created at $config_file"
            print_warning "Please edit $config_file with your settings before the cron job runs"
        else
            print_error "Failed to create sample configuration"
            exit 1
        fi
    else
        print_success "Configuration file exists: $config_file"
    fi
}

# Parse command line arguments
REMOVE_ONLY=false
CRON_TIME="$DEFAULT_CRON_TIME"
TIMEZONE="$DEFAULT_TIMEZONE"
CONFIG_FILE="analysis_config.json"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --remove)
            REMOVE_ONLY=true
            shift
            ;;
        --time)
            CRON_TIME="$2"
            shift 2
            ;;
        --timezone)
            TIMEZONE="$2"
            shift 2
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    echo "TradingAgents Cron Job Setup"
    echo "============================="
    echo ""
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_warning "DRY RUN MODE - No changes will be made"
        echo ""
    fi
    
    # Check dependencies
    check_dependencies
    check_python
    
    # Set timezone if specified
    if [[ "$TIMEZONE" != "$DEFAULT_TIMEZONE" ]]; then
        print_info "Setting timezone: $TIMEZONE"
        export TZ="$TIMEZONE"
    fi
    
    # Remove existing jobs first (if any exist or if --remove specified)
    remove_cronjob
    
    if [[ "$REMOVE_ONLY" == "true" ]]; then
        print_success "Cron job removal completed"
        exit 0
    fi
    
    # Create sample config if needed
    create_sample_config "$CONFIG_FILE"
    
    # Create new cron job
    create_cronjob "$CRON_TIME" "$CONFIG_FILE"
    
    if [[ "$DRY_RUN" != "true" ]]; then
        # Verify the job was created
        verify_cronjob
        
        # Test the schedule checker
        test_schedule_checker
        
        # Check cron service status
        show_cron_status
        
        echo ""
        print_success "Setup completed successfully!"
        echo ""
        echo "Next steps:"
        echo "1. Edit '$CONFIG_FILE' with your desired stock symbols and settings"
        echo "2. Configure environment variables (OPENAI_API_KEY, FINNHUB_API_KEY, etc.)"
        echo "3. Test manually: python3 schedule_checker.py --check-only"
        echo "4. Monitor logs: tail -f log/cron.log"
        echo "5. Check batch analysis logs: tail -f log/batch_analysis.log"
        echo ""
        echo "The cron job will run daily at $(date -d "$CRON_TIME" +"%-I:%M %p" 2>/dev/null || echo "specified time")"
        echo "and automatically check if analysis should run based on market schedule."
    fi
}

# Run main function
main
