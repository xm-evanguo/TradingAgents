# TradingAgents LLM Interface & Automation

Programmatic interface for running financial analysis using Large Language Models. Ideal for automation, batch processing, and integration.

## Custom Directory Structure

This `custom/` directory contains enhanced interfaces and automation tools:

### Files in `custom/`
- **`interface.py`** - Enhanced programmatic interface (moved from root)
- **`batch_analysis.py`** - Multi-stock batch processing with email notifications
- **`email_service.py`** - Email notification service with HTML formatting
- **`schedule_checker.py`** - Market-aware scheduler (weekdays, holidays)
- **`setup_cronjob.sh`** - Automated cron job setup script
- **`analysis_config.json.example`** - Configuration template
- **`llm.md`** - This comprehensive documentation file

### Project Structure
```
TradingAgents/
├── custom/           # Enhanced automation tools
│   ├── interface.py
│   ├── batch_analysis.py
│   ├── email_service.py
│   ├── schedule_checker.py
│   └── setup_cronjob.sh
├── log/             # All log files
│   ├── batch_analysis.log
│   └── cron.log
├── batch_results/   # Analysis results
└── analysis_config.json  # Main configuration
```

## Quick Start

```python
# Import from custom directory
from custom.interface import TradingAgentsInterface

# Basic usage with defaults
interface = TradingAgentsInterface()
result = interface.run_analysis()

if result.success:
    print(f"Decision: {result.decision}")
else:
    print(f"Error: {result.error_message}")

# Fast testing
result = TradingAgentsInterface.quick_test("GOOG")
```

### Automation Quick Start

```bash
# 1. Copy example configuration
cp custom/analysis_config.json.example analysis_config.json

# 2. Edit configuration with your settings
# 3. Setup automated scheduling (8:00 PM PST daily)
./custom/setup_cronjob.sh
```

## Setup

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your-openai-api-key"
export FINNHUB_API_KEY="your-finnhub-api-key"
```

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ticker` | "SPY" | Stock ticker symbol |
| `analysis_date` | today | Analysis date (YYYY-MM-DD) |
| `analysts` | all | "market", "social", "news", "fundamentals" |
| `research_depth` | "shallow" | "shallow", "medium", "deep" |
| `llm_provider` | "openai" | "openai", "google", "deepseek" |

## Usage Examples

### Basic Usage
```python
from custom.interface import TradingAgentsInterface

interface = TradingAgentsInterface()
result = interface.run_analysis()

if result.success:
    print(f"Decision: {result.decision}")
else:
    print(f"Error: {result.error_message}")
```

### Custom Analysis
```python
from custom.interface import TradingAgentsInterface

interface = TradingAgentsInterface(
    ticker="GOOG",
    analysis_date="2024-12-20",
    analysts=["market", "news"],
    research_depth="medium",
    llm_provider="openai"
)
result = interface.run_analysis()
```

### Batch Processing
```python
from custom.interface import TradingAgentsInterface

tickers = ["SPY", "QQQ", "GOOG", "TSLA", "NVDA"]
results = []

for ticker in tickers:
    result = TradingAgentsInterface.quick_test(ticker=ticker)
    results.append(result)
    
    if result.success:
        print(f"✅ {ticker}: {result.decision}")
    else:
        print(f"❌ {ticker}: {result.error_message}")
```

### Command Line Usage
```bash
# Basic usage
python custom/interface.py --ticker GOOG

# Custom parameters
python custom/interface.py --ticker GOOG --date 2024-12-20 --depth medium

# Fast testing mode
python custom/interface.py --ticker GOOG --fast
```

## LLM Providers

### OpenAI (Default)
- **Models**: `o4-mini`, `o3`, `gpt-4.1-nano` (fast)
- **Requires**: `OPENAI_API_KEY`

### Google
- **Models**: `gemini-2.5-flash`, `gemini-2.5-pro`  
- **Requires**: `GOOGLE_API_KEY`

### DeepSeek
- **Models**: `deepseek-chat`, `deepseek-reasoner`
- **Requires**: `DEEPSEEK_API_KEY`

## Result Object

```python
@dataclass
class AnalysisResult:
    ticker: str                    # Stock ticker analyzed
    analysis_date: str            # Date of analysis  
    decision: Dict[str, Any]      # Trading decision and reasoning
    final_state: Dict[str, Any]   # Complete analysis state
    success: bool                 # Whether analysis succeeded
    error_message: Optional[str]  # Error message if failed
```

## Error Handling

```python
# Input validation
try:
    interface = TradingAgentsInterface(ticker="INVALID123")
except ValueError as e:
    print(f"Error: {e}")

# Runtime error handling
result = interface.run_analysis()
if not result.success:
    print(f"Analysis failed: {result.error_message}")
```

## Command Line Options

```bash
python custom/interface.py --help

# Key options:
--ticker TICKER         Stock ticker symbol (default: SPY)
--date DATE             Analysis date YYYY-MM-DD (default: today)  
--depth {shallow,medium,deep}  Research depth (default: shallow)
--provider {openai,google,deepseek}  LLM provider
--fast                  Use fast models for testing
--debug                 Enable debug mode
```

## Automation System

For production use, TradingAgents includes a complete automation system for scheduled analysis with email notifications.

### Components

1. **`custom/batch_analysis.py`** - Runs analysis for multiple stocks from a config file
2. **`custom/email_service.py`** - Sends email notifications with analysis results  
3. **`custom/schedule_checker.py`** - Determines if analysis should run based on market days/holidays
4. **`custom/setup_cronjob.sh`** - Bash script to setup cron job for automated execution

### Quick Automation Setup

```bash
# 1. Copy example configuration
cp custom/analysis_config.json.example analysis_config.json

# 2. Edit configuration with your settings
# 3. Setup automated scheduling (8:00 PM PST daily)
./custom/setup_cronjob.sh
```

### Batch Configuration

Create `analysis_config.json` with your settings:

```json
{
  "tickers": ["SPY", "QQQ", "AAPL", "GOOGL", "MSFT"],
  "analysis_settings": {
    "analysts": ["market", "news", "fundamentals"],
    "research_depth": "shallow",
    "llm_provider": "openai"
  },
  "email_settings": {
    "enabled": true,
    "recipients": ["your-email@example.com"],
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-sender@gmail.com",
    "sender_password": "your-app-password"
  }
}
```

### Manual Batch Processing

```bash
# Run batch analysis for configured stocks
python custom/batch_analysis.py

# Run with email notifications
python custom/batch_analysis.py --email

# Check if today is a trading day
python custom/schedule_checker.py --check-only

# Force run analysis regardless of schedule
python custom/schedule_checker.py --run-analysis --force
```

### Automated Scheduling

The system automatically skips:
- Weekends (Saturday/Sunday)
- US market holidays (New Year's Day, Presidents Day, Good Friday, etc.)
- Custom holidays you define in config

```bash
# Setup daily cron job at 8:00 PM PST
./custom/setup_cronjob.sh

# Custom schedule (7:30 PM daily)
./custom/setup_cronjob.sh --time "30 19 * * *"

# Remove automation
./custom/setup_cronjob.sh --remove
```

### Email Notifications

For Gmail, use an App Password:
1. Enable 2-factor authentication
2. Go to Google Account settings → Security → App passwords
3. Generate an app password for "Mail"
4. Use that password in the config

Email notifications include:
- Summary statistics (success rate, total analyzed)
- Trading signals (BUY/SELL/HOLD grouped)
- Detailed results with confidence levels
- Failed analysis list
- HTML formatting for better readability

### Monitoring

```bash
# View current cron jobs
crontab -l

# Check recent executions
tail -f log/cron.log

# Check analysis logs
tail -f log/batch_analysis.log
```

## Logging and Results

### Log Files Structure
All log files are centralized in the `log/` directory:
- **`log/batch_analysis.log`** - Detailed batch processing logs
- **`log/cron.log`** - Cron job execution logs and errors

### Results Structure  
Analysis results are saved in the `batch_results/` directory:
- **Individual results**: `batch_results/TICKER_YYYY-MM-DD_result.json`
- **Summary reports**: `batch_results/batch_summary_TIMESTAMP.json`

### Log Monitoring Commands
```bash
# Monitor live batch analysis
tail -f log/batch_analysis.log

# Monitor cron job executions
tail -f log/cron.log

# Check last 50 lines of analysis log
tail -n 50 log/batch_analysis.log

# Search for errors in logs
grep -i error log/batch_analysis.log

# View all log files
ls -la log/
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# If you get import errors, ensure you're running from project root
cd /path/to/TradingAgents
python custom/interface.py --ticker AAPL
```

#### 2. Permission Errors
```bash
# Make setup script executable
chmod +x custom/setup_cronjob.sh
```

#### 3. Cron Job Not Running
```bash
# Check cron service status
sudo systemctl status cron

# View cron logs
tail -f log/cron.log

# Test schedule checker manually
python custom/schedule_checker.py --check-only
```

#### 4. Email Not Sending
```bash
# Test email configuration
python custom/email_service.py --config analysis_config.json --test

# For Gmail: Use App Password, not regular password
# Enable 2FA → Google Account → Security → App passwords
```

#### 5. Analysis Failures
```bash
# Check API keys are set
echo $OPENAI_API_KEY
echo $FINNHUB_API_KEY

# Run with debug mode
python custom/interface.py --ticker AAPL --debug

# Check detailed logs
grep -A 10 -B 10 "ERROR" log/batch_analysis.log
```

### File Permissions
```bash
# Ensure proper permissions
chmod +x custom/setup_cronjob.sh
chmod 644 custom/*.py
chmod 644 analysis_config.json
```

### Clean Start
```bash
# Remove existing cron jobs
./custom/setup_cronjob.sh --remove

# Clear old logs
rm -f log/*.log

# Reset configuration
cp custom/analysis_config.json.example analysis_config.json

# Setup fresh
./custom/setup_cronjob.sh
```
