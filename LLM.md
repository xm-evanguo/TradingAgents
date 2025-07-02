# TradingAgents Backtesting Implementation

This document describes the implementation of a comprehensive backtesting framework for the TradingAgents multi-agent trading system.

## Overview

The backtesting script (`backtest.py`) is designed to test whether following the TradingAgents' recommendations would beat a simple buy-and-hold strategy on QQQ over a specified time period. The implementation addresses the key requirements:

1. **Weekly Analysis**: Performs analysis every Monday (or next trading day if Monday is not a trading day)
2. **Cost Control**: Implements user confirmation checkpoints to control API token usage
3. **Persistence**: Saves progress locally and can resume from where it left off
4. **Performance Comparison**: Compares agent strategy against buy-and-hold QQQ
5. **Realistic Simulation**: Uses actual market data from Yahoo Finance

## Architecture

### Core Components

#### 1. BacktestingEngine Class
The main orchestrator that handles:
- Configuration management
- Progress tracking and resumption
- Signal generation coordination
- Trading simulation
- Results analysis

#### 2. Signal Generation Phase
- Identifies all Mondays in the specified date range
- Converts non-trading Mondays to next available trading day
- Runs TradingAgents analysis with optimized configuration
- Saves each signal to persistent storage
- Implements user checkpoints for cost control

#### 3. Trading Simulation Phase
- Loads QQQ market data from Yahoo Finance
- Simulates portfolio management based on agent signals
- Implements position sizing based on confidence levels
- Tracks performance against buy-and-hold strategy

#### 4. Results Analysis
- Calculates absolute and relative returns
- Computes outperformance metrics
- Generates detailed transaction logs
- Provides comprehensive performance summary

## Configuration

### TradingAgents Configuration
The script uses an optimized configuration for cost-efficient backtesting:

```python
config = {
    "llm_provider": "openai",
    "deep_think_llm": "o4-mini",        # Deep-Thinking LLM Engine
    "quick_think_llm": "gpt-4.1-mini",   # Quick thinking LLM engine
    "max_debate_rounds": 1,             # Shallow research depth
    "max_risk_discuss_rounds": 1,
    "online_tools": True                # Use real-time data
}
```

This configuration mirrors the CLI requirements:
- **Ticker Symbol**: Always QQQ
- **Analysis Date**: Mondays (or next trading day)
- **Analysts Team**: All analysts selected (default)
- **Research Depth**: Shallow - Quick research, few debate rounds
- **OpenAI Backend**: OpenAI as the LLM provider
- **Thinking Agents**: GPT-4o-mini for quick thinking, o1-mini for deep thinking

### Trading Parameters
- **Initial Capital**: $100,000
- **Maximum Position Size**: 20% of portfolio value per trade
- **Minimum Trade Size**: $100
- **Maximum Sell Ratio**: 50% of holdings per trade
- **Position Sizing**: Based on agent confidence levels

## Data Persistence

### File Structure
The backtesting framework consists of several key files:

#### Core Framework Files
- **`backtest.py`** - Main backtesting engine and script
- **`backtest_analyzer.py`** - Analysis and visualization tools  
- **`backtest_config.py`** - Configuration options and presets
- **`example_usage.py`** - Usage examples and demonstration script

#### Generated Output Directory
```
backtest_results/
├── trading_signals.json    # All generated trading signals with metadata
├── progress.json          # Current progress state for resumption
├── backtest_results.json  # Complete simulation results
├── portfolio_history.csv  # Day-by-day portfolio tracking (exported)
├── transactions.csv       # Detailed transaction log (exported)
├── summary.csv           # Performance summary (exported)
└── performance_chart.png # Visualization charts (generated)
```

### Signal Format
Each trading signal is stored with complete metadata:
```json
{
    "2024-05-06": {
        "date": "2024-05-06",
        "ticker": "QQQ",
        "analysis_date": "2024-12-29T10:30:00",
        "decision": "Agent decision text...",
        "config_used": {
            "deep_think_llm": "o1-mini",
            "quick_think_llm": "gpt-4o-mini",
            "max_debate_rounds": 1
        }
    }
}
```

### Progress Tracking
The progress file enables resumption:
```json
{
    "last_processed_date": "2024-05-06T00:00:00",
    "total_signals": 15
}
```

## Cost Control Mechanisms

### 1. User Checkpoints
After each signal generation, the script pauses and prompts:
```
⏸️ Processed 15/52 signals
💰 Token usage checkpoint - Press Enter to continue, 'q' to quit:
```

### 2. Efficient Model Selection
- Uses `gpt-4o-mini` for quick thinking (cost-effective)
- Uses `o1-mini` for deep thinking (instead of more expensive o1-preview)
- Limits debate rounds to 1 for shallow research

### 3. Resumable Design
- All progress is saved after each signal
- Can restart from exact stopping point
- No duplicate API calls for already processed dates

## Trading Logic

### Decision Parsing
The script parses agent decisions using keyword detection:
- **Buy/Long signals**: Triggers purchase based on confidence
- **Sell/Short signals**: Triggers sale based on confidence  
- **Hold/Neutral**: No action taken

### Position Sizing
Position sizes are determined by agent confidence:
- **High confidence (0.8)**: Up to 16% of portfolio (20% × 0.8)
- **Moderate confidence (0.6)**: Up to 12% of portfolio
- **Low confidence (0.4)**: Up to 8% of portfolio

### Risk Management
- Maximum 20% of portfolio per single trade
- Minimum $100 trade size to avoid excessive transaction costs
- Maximum 50% of holdings can be sold in single transaction

## Usage

### Prerequisites
Set required environment variables:
```bash
export OPENAI_API_KEY=your_openai_api_key
export FINNHUB_API_KEY=your_finnhub_api_key
```

### Running the Backtest
```bash
# Start new backtest
python backtest.py --start-date 2024-05-01 --end-date 2025-05-01

# Resume existing backtest (same command)
python backtest.py --start-date 2024-05-01 --end-date 2025-05-01

# Custom output directory
python backtest.py --start-date 2024-05-01 --end-date 2025-05-01 --output-dir my_backtest
```

### Example Session
```
🤖 TradingAgents Backtesting Engine Initialized
📅 Period: 2024-05-01 to 2025-05-01
📁 Output Directory: backtest_results

🚀 Starting Signal Generation Phase
📊 Total Mondays to analyze: 52

🔍 Analyzing QQQ for 2024-05-06...
🎯 Configuration:
   • Ticker: QQQ
   • Analysts Team: All analysts selected
   • Research Depth: Shallow - Quick research
   • LLM Provider: OpenAI
   • Quick Thinking: GPT-4o-mini
   • Deep Thinking: o1-mini

✅ Analysis completed for 2024-05-06
📊 Decision: Strong buy recommendation based on positive momentum...
💾 Signal saved for 2024-05-06

⏸️ Processed 1/52 signals
💰 Token usage checkpoint - Press Enter to continue, 'q' to quit:
```

## Output and Results

### Performance Metrics
The script generates comprehensive performance analysis:

```
🏆 BACKTESTING RESULTS
==========================================
📅 Period: 2024-05-01 to 2025-05-01
⏱️ Trading Days: 52
💰 Initial Capital: $100,000.00

📊 FINAL RESULTS:
🤖 Agent Strategy: $125,430.00
📈 Buy & Hold QQQ: $118,750.00

📈 RETURNS:
🤖 Agent Strategy: +25.43%
📈 Buy & Hold QQQ: +18.75%

🎯 OUTPERFORMANCE:
💵 Absolute: +$6,680.00
📊 Relative: +5.63%

📋 TRADING SUMMARY:
🛒 Buy Trades: 23
💰 Sell Trades: 18
📊 Total Transactions: 41
```

### Detailed Transaction Log
Complete record of all trades with timestamps, prices, and confidence levels.

### Portfolio History
Day-by-day tracking of portfolio value, cash position, and share holdings.

## Implementation Notes

### Market Data Handling
- Uses Yahoo Finance for reliable, free market data
- Handles market holidays and non-trading days automatically
- Includes data validation and error handling

### Error Recovery
- Comprehensive exception handling
- Graceful degradation for missing data
- Detailed error logging with stack traces

### Extensibility
- Modular design allows easy addition of new strategies
- Configurable parameters for different testing scenarios
- Support for different time periods and tickers

## Limitations and Considerations

### 1. Transaction Costs
Current implementation doesn't include:
- Brokerage fees
- Bid-ask spreads
- Slippage
- Market impact

### 2. Decision Parsing
The decision parsing is simplified and may need refinement based on actual agent output format.

### 3. Market Conditions
Backtesting assumes perfect execution at closing prices, which may not reflect real-world trading conditions.

### 4. API Rate Limits
The script includes user checkpoints but doesn't implement automatic rate limiting for API calls.

## Future Enhancements

### 1. Advanced Analytics
- Sharpe ratio calculation
- Maximum drawdown analysis
- Win/loss ratio statistics
- Risk-adjusted returns

### 2. Multiple Strategies
- Support for different agent configurations
- A/B testing between strategies
- Portfolio optimization

### 3. Enhanced Visualization
- Portfolio performance charts
- Trade timing analysis
- Risk metrics dashboard

### 4. Real-time Integration
- Live trading simulation
- Paper trading integration
- Real-time performance monitoring

## Quick Start Guide

### 1. Environment Setup
Before running the backtesting framework, ensure you have the required API keys:

```bash
# Set required API keys
export OPENAI_API_KEY=your_openai_api_key
export FINNHUB_API_KEY=your_finnhub_api_key

# Install additional dependencies for visualization
pip install matplotlib seaborn
```

### 2. Run Example Demo
For a quick demonstration of the framework:

```bash
# Quick demonstration (1 month period)
python example_usage.py demo

# Show all usage examples and commands
python example_usage.py examples
```

### 3. Full Backtesting Process
Run the complete backtesting as specified in the requirements:

```bash
# Run the main backtest for the specified period
python backtest.py --start-date 2024-05-01 --end-date 2025-05-01

# The script will pause after each signal generation:
# - Press Enter to continue to next signal
# - Type 'q' and press Enter to quit and save progress
# - Resume later with the same command (it will continue from where you left off)
```

### 4. Analysis and Visualization
After generating signals and running simulation:

```bash
# Analyze trading signals and performance
python backtest_analyzer.py analyze --results-dir backtest_results

# Generate performance charts and visualizations
python backtest_analyzer.py chart --results-dir backtest_results

# Export all results to CSV format
python backtest_analyzer.py export --results-dir backtest_results

# Compare multiple backtesting runs
python backtest_analyzer.py compare --compare-dirs run1/ run2/ run3/
```

### 5. Custom Configuration
Use the configuration file for different testing scenarios:

```python
from backtest_config import COST_EFFICIENT_CONFIG, HIGH_PERFORMANCE_CONFIG

# For testing/development (cheaper API costs)
engine = BacktestingEngine(start_date, end_date, config=COST_EFFICIENT_CONFIG)

# For final analysis (higher quality but more expensive)
engine = BacktestingEngine(start_date, end_date, config=HIGH_PERFORMANCE_CONFIG)
```
