# TradingAgents Custom Scripts & Automation

This directory contains custom automation scripts and interfaces for TradingAgents, including enhanced batch processing with comprehensive reasoning capture.

## Enhanced Batch Analysis Features

The batch analysis system now captures **comprehensive reasoning** behind every trading decision, including:

- **Technical Analysis Details** - RSI, MACD, moving averages, trend analysis
- **Investment Debate** - Bull vs Bear arguments with judge decisions  
- **Risk Analysis** - Risk/reward ratios and position sizing recommendations
- **Trade Recommendations** - Specific entry/exit points with stop-losses
- **Market Reports** - Multi-indicator technical reviews
- **Final Decision Reasoning** - Complete justification for BUY/SELL/HOLD signals

### Result Files Structure
```
batch_results/
├── TICKER_DATE_result.json      # Standard result with reasoning summary
├── TICKER_DATE_detailed.json    # Full analysis state with all reasoning
└── batch_summary_TIMESTAMP.json # Enhanced summary with reasoning insights
```

## Files

- **`interface.py`** - Enhanced programmatic interface with detailed result objects
- **`batch_analysis.py`** - **Enhanced** batch processing with rich reasoning capture
- **`email_service.py`** - Email notification service for sending analysis results
- **`schedule_checker.py`** - Smart scheduler that only runs on market days (weekdays, non-holidays)
- **`setup_cronjob.sh`** - Bash script to setup automated cron jobs
- **`analysis_config.json.example`** - Example configuration file for batch analysis

## Log Files

All log files are stored in `../log/` directory:
- **`../log/batch_analysis.log`** - Enhanced batch analysis execution logs with reasoning insights
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
# Run enhanced batch analysis with reasoning capture
python custom/batch_analysis.py

# Check if today is a trading day
python custom/schedule_checker.py --check-only

# Test email service
python custom/email_service.py --config analysis_config.json --test

# Use the interface directly
python custom/interface.py --ticker AAPL
```

## Enhanced Result Format

### Standard Result File Example
```json
{
  "ticker": "CADJPY=X",
  "decision": "SELL",
  "reasoning": {
    "final_decision": "Recommendation: SELL - Long-term trend and momentum point down...",
    "market_analysis": "Technical indicators show bearish momentum with MACD negative...",
    "trader_reasoning": "Risk/reward favors short position with 3:1 ratio...",
    "risk_analysis": "Stop-loss at 106.80, targets at 104.00 and 102.00..."
  }
}
```

### Reasoning Fields Captured
- **`final_decision`** - Complete recommendation with detailed justification
- **`market_analysis`** - Technical analysis with multiple indicators
- **`investment_reasoning`** - Bull vs Bear debate summary
- **`trader_reasoning`** - Specific trade setup with entry/exit points  
- **`judge_decision`** - Investment committee decision rationale
- **`risk_analysis`** - Risk management and position sizing logic

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ticker` | "SPY" | Stock ticker symbol |
| `analysis_date` | today | Analysis date (YYYY-MM-DD) |
| `analysts` | all | "market", "social", "news", "fundamentals" |
| `research_depth` | "shallow" | "shallow", "medium", "deep" |
| `llm_provider` | "openai" | "openai", "google", "deepseek" |

## Enhanced Batch Configuration

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
  },
  "output_settings": {
    "save_individual_results": true,
    "save_summary": true,
    "results_directory": "batch_results"
  }
}
```

## Usage Examples

### Basic Interface Usage
```python
from custom.interface import TradingAgentsInterface

interface = TradingAgentsInterface()
result = interface.run_analysis()

if result.success:
    print(f"Decision: {result.decision}")
    print(f"Reasoning available: {bool(result.final_state)}")
else:
    print(f"Error: {result.error_message}")
```

### Enhanced Batch Processing  
```python
from custom.batch_analysis import BatchAnalyzer

analyzer = BatchAnalyzer('analysis_config.json')
results = analyzer.run_batch_analysis()

for result in results:
    if result.success:
        print(f"✅ {result.ticker}: {result.decision}")
        # Access rich reasoning data
        if hasattr(result, 'final_state') and result.final_state:
            print(f"   📊 Market analysis available")
            print(f"   🎯 Trade recommendations available")
    else:
        print(f"❌ {result.ticker}: {result.error_message}")
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

## Automation System

### Quick Automation Setup

```bash
# 1. Copy example configuration
cp custom/analysis_config.json.example analysis_config.json

# 2. Edit configuration with your settings
# 3. Setup automated scheduling (8:00 PM PST daily)
./custom/setup_cronjob.sh
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

Enhanced email notifications now include:
- **Summary statistics** (success rate, total analyzed)
- **Trading signals** (BUY/SELL/HOLD grouped)
- **Reasoning summaries** for each decision
- **Detailed results** with confidence levels
- **Failed analysis list**
- **HTML formatting** for better readability

For Gmail, use an App Password:
1. Enable 2-factor authentication
2. Go to Google Account settings → Security → App passwords
3. Generate an app password for "Mail"
4. Use that password in the config

## Enhanced Result Object

```python
@dataclass
class AnalysisResult:
    ticker: str                    # Stock ticker analyzed
    analysis_date: str            # Date of analysis  
    decision: Dict[str, Any]      # Trading decision and reasoning
    final_state: Dict[str, Any]   # Complete analysis state with rich data
    success: bool                 # Whether analysis succeeded
    error_message: Optional[str]  # Error message if failed
```

The `final_state` now contains comprehensive data including:
- `market_report` - Detailed technical analysis
- `investment_debate_state` - Bull vs Bear arguments
- `trader_investment_plan` - Specific trade recommendations
- `risk_debate_state` - Risk management analysis
- `final_trade_decision` - Complete decision rationale

## Monitoring

```bash
# Check recent batch analysis logs with reasoning
tail -f log/batch_analysis.log

# Check cron job execution logs  
tail -f log/cron.log

# View current cron jobs
crontab -l

# Monitor enhanced results
ls -la batch_results/

# View latest detailed analysis
cat batch_results/*_detailed.json | jq '.reasoning'
```

## Enhanced Log Output

The batch analysis now logs enhanced information:
```
2025-07-08 22:56:16 - INFO - ✅ CADJPY=X: Analysis completed successfully
2025-07-08 22:56:16 - INFO -    Decision: SELL
2025-07-08 22:56:16 - INFO -    Key Insight: Long-term trend and momentum still point down
2025-07-08 22:56:16 - INFO - Results saved with comprehensive reasoning data
```

## Troubleshooting

### Common Issues
1. **Empty reasoning data**: Ensure latest batch_analysis.py is being used with enhanced extraction
2. **JSON serialization errors**: Fixed in latest version with proper AddableValuesDict handling  
3. **Missing detailed files**: Check that save_individual_results is enabled in config

### Debug Commands
```bash
# Check reasoning extraction capability
python -c "from custom.batch_analysis import BatchAnalyzer; print('Enhanced reasoning: Available')"

# Verify detailed file creation
ls -la batch_results/*_detailed.json

# Test email notifications
python custom/email_service.py --test
```
