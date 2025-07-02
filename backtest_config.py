# TradingAgents Backtesting Configuration

# This file contains configurable parameters for the backtesting framework.
# Modify these values to test different scenarios and strategies.

BACKTEST_CONFIG = {
    # =============================================================================
    # TRADING AGENT CONFIGURATION
    # =============================================================================
    
    # LLM Provider Settings
    "llm_provider": "openai",
    "backend_url": "https://api.openai.com/v1",
    
    # Model Selection (adjust for cost vs. performance trade-off)
    "deep_think_llm": "o4-mini",        # Options: "o1-mini", "o1-preview" (more expensive)
    "quick_think_llm": "gpt-4.1-mini",   # Options: "gpt-4o-mini", "gpt-4o" (more expensive)
    
    # Research Depth (affects API costs)
    "max_debate_rounds": 2,             # 1=Shallow, 2-3=Medium, 4+=Deep
    "max_risk_discuss_rounds": 1,       # Risk management discussion rounds
    
    # Data Sources
    "online_tools": True,               # True=Real-time data, False=Cached data
    
    
    # =============================================================================
    # PORTFOLIO MANAGEMENT CONFIGURATION  
    # =============================================================================
    
    # Initial Portfolio Settings
    "initial_capital": 100000,          # Starting capital in USD
    
    # Position Sizing Rules
    "max_position_size": 0.20,          # Maximum 20% of portfolio per trade
    "min_trade_amount": 100,            # Minimum trade size in USD
    "max_sell_ratio": 0.50,             # Maximum 50% of holdings sold per trade
    
    # Risk Management
    "use_stop_loss": False,             # Enable stop-loss orders
    "stop_loss_percent": 0.10,          # 10% stop-loss
    "use_position_sizing": True,        # Use confidence-based position sizing
    
    
    # =============================================================================
    # BACKTESTING PARAMETERS
    # =============================================================================
    
    # Analysis Frequency
    "analysis_frequency": "weekly",     # Options: "weekly", "daily", "monthly"
    "analysis_day": "monday",           # For weekly: "monday", "tuesday", etc.
    
    # Cost Control
    "enable_checkpoints": True,         # Pause for user confirmation after each signal
    "checkpoint_frequency": 1,          # Checkpoint every N signals
    "auto_save_frequency": 1,           # Auto-save every N signals
    
    # Data Handling
    "cache_market_data": True,          # Cache Yahoo Finance data locally
    "validate_trading_days": True,      # Check if analysis dates are trading days
    
    
    # =============================================================================
    # COMPARISON BENCHMARKS
    # =============================================================================
    
    # Primary benchmark (what we're trying to beat)
    "primary_benchmark": "QQQ",
    
    # Additional benchmarks for comparison
    "additional_benchmarks": [
        "SPY",                          # S&P 500
        "VTI",                          # Total Stock Market
        "TQQQ",                         # 3x QQQ (for risk comparison)
    ],
    
    
    # =============================================================================
    # OUTPUT AND REPORTING
    # =============================================================================
    
    # File Paths
    "signals_filename": "trading_signals.json",
    "progress_filename": "progress.json", 
    "results_filename": "backtest_results.json",
    
    # Reporting Options
    "generate_charts": True,            # Auto-generate performance charts
    "export_csv": True,                 # Auto-export results to CSV
    "detailed_logging": True,           # Verbose logging
    
    # Chart Settings
    "chart_style": "seaborn",           # Chart style: "seaborn", "ggplot", "classic"
    "chart_dpi": 300,                   # Chart resolution
    "chart_size": (12, 8),              # Chart size in inches
    
    
    # =============================================================================
    # ADVANCED SETTINGS
    # =============================================================================
    
    # Transaction Costs (for more realistic simulation)
    "include_transaction_costs": False,  # Include brokerage fees
    "commission_per_trade": 0.0,        # Commission per trade in USD
    "bid_ask_spread": 0.001,            # Bid-ask spread as decimal (0.1%)
    
    # Market Impact (for large trades)
    "include_market_impact": False,     # Model market impact of trades
    "impact_coefficient": 0.1,          # Market impact coefficient
    
    # Slippage (execution vs. signal price)
    "include_slippage": False,          # Include slippage
    "slippage_bps": 5,                  # Slippage in basis points
    
    
    # =============================================================================
    # EXPERIMENTAL FEATURES
    # =============================================================================
    
    # Multi-timeframe analysis
    "enable_multi_timeframe": False,    # Analyze multiple timeframes
    "timeframes": ["1d", "1w", "1m"],   # Daily, weekly, monthly
    
    # Ensemble strategies
    "enable_ensemble": False,           # Use multiple agent configurations
    "ensemble_configs": [               # Different agent setups to combine
        {"deep_think_llm": "o1-mini", "max_debate_rounds": 1},
        {"deep_think_llm": "o1-mini", "max_debate_rounds": 2},
    ],
    
    # Dynamic position sizing
    "dynamic_position_sizing": False,   # Adjust position size based on volatility
    "volatility_lookback": 20,          # Days to look back for volatility calculation
}


# =============================================================================
# PRESET CONFIGURATIONS
# =============================================================================

# Cost-efficient configuration for testing
COST_EFFICIENT_CONFIG = BACKTEST_CONFIG.copy()
COST_EFFICIENT_CONFIG.update({
    "deep_think_llm": "gpt-4o-mini",    # Cheaper model
    "quick_think_llm": "gpt-4o-mini",   # Cheaper model
    "max_debate_rounds": 1,             # Minimal rounds
    "online_tools": False,              # Use cached data
})

# High-performance configuration for final testing
HIGH_PERFORMANCE_CONFIG = BACKTEST_CONFIG.copy() 
HIGH_PERFORMANCE_CONFIG.update({
    "deep_think_llm": "o1-preview",     # Most capable model
    "quick_think_llm": "gpt-4o",        # High-performance model
    "max_debate_rounds": 3,             # More thorough analysis
    "max_risk_discuss_rounds": 2,       # More risk analysis
    "online_tools": True,               # Real-time data
})

# Realistic trading configuration (includes costs)
REALISTIC_CONFIG = BACKTEST_CONFIG.copy()
REALISTIC_CONFIG.update({
    "include_transaction_costs": True,
    "commission_per_trade": 1.0,        # $1 per trade
    "bid_ask_spread": 0.001,            # 0.1% spread
    "include_slippage": True,
    "slippage_bps": 2,                  # 2 basis points slippage
})


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
To use these configurations in your backtesting:

1. Import the configuration:
   from backtest_config import COST_EFFICIENT_CONFIG, HIGH_PERFORMANCE_CONFIG

2. Modify the BacktestingEngine to accept custom config:
   engine = BacktestingEngine(start_date, end_date, config=COST_EFFICIENT_CONFIG)

3. Or create your own custom configuration:
   my_config = BACKTEST_CONFIG.copy()
   my_config["initial_capital"] = 50000
   my_config["max_debate_rounds"] = 2
   
4. Run different scenarios:
   # Quick test
   engine1 = BacktestingEngine("2024-05-01", "2024-06-01", config=COST_EFFICIENT_CONFIG)
   
   # Full performance test  
   engine2 = BacktestingEngine("2024-05-01", "2025-05-01", config=HIGH_PERFORMANCE_CONFIG)
   
   # Realistic simulation
   engine3 = BacktestingEngine("2024-05-01", "2025-05-01", config=REALISTIC_CONFIG)
"""
