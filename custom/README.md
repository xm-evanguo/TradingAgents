# TradingAgents Custom Scripts

This directory contains custom automation scripts and interfaces for TradingAgents.

## Files

- **`interface.py`** - Programmatic interface for TradingAgents (moved from root)
- **`llm.md`** - Complete documentation for LLM interface and automation (moved from root)
- **`batch_analysis.py`** - Main batch processing script that runs analysis for multiple stocks
- **`email_service.py`** - Email notification service for sending analysis results
- **`schedule_checker.py`** - Smart scheduler that only runs on market days (weekdays, non-holidays)
- **`setup_cronjob.sh`** - Bash script to setup automated cron jobs
- **`analysis_config.json.example`** - Example configuration file for batch analysis

## Log Files

All log files are stored in `../log/` directory:
- **`../log/batch_analysis.log`** - Batch analysis execution logs
- **`../log/cron.log`** - Cron job execution logs

## Quick Start

1. Copy the example configuration:
   ```bash
   cp custom/analysis_config.json.example analysis_config.json
   ```

2. Edit `analysis_config.json` with your settings (API keys, stock symbols, email config)

3. Setup automated scheduling:
   ```bash
   ./custom/setup_cronjob.sh
   ```

## Manual Usage

```bash
# Run batch analysis manually
python custom/batch_analysis.py

# Check if today is a trading day
python custom/schedule_checker.py --check-only

# Test email service
python custom/email_service.py --config analysis_config.json --test

# Use the interface directly
python custom/interface.py --ticker AAPL
```

## Documentation

See `llm.md` in this directory for complete documentation of the interface and automation system.

## Monitoring

```bash
# Check recent batch analysis logs
tail -f log/batch_analysis.log

# Check cron job execution logs  
tail -f log/cron.log

# View current cron jobs
crontab -l
```
