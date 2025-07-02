#!/usr/bin/env python3
"""
Example script showing how to use the TradingAgents backtesting framework.
"""

import os
import sys
from datetime import datetime


def check_environment():
    """Check if required environment variables are set."""
    required_vars = ['OPENAI_API_KEY', 'FINNHUB_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   export {var}=your_api_key_here")
        return False
    
    print("✅ Environment variables configured")
    return True


def run_example_backtest():
    """Run an example backtest for a short period."""
    print("🚀 Running Example TradingAgents Backtest")
    print("=" * 50)
    
    if not check_environment():
        return
    
    # Import here to avoid issues if dependencies aren't installed
    try:
        from backtest import BacktestingEngine
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you've installed all requirements: pip install -r requirements.txt")
        return
    
    # Run a short backtest for demonstration (1 month)
    start_date = "2024-05-01"
    end_date = "2024-06-01"
    output_dir = "example_backtest"
    
    print(f"📅 Testing period: {start_date} to {end_date}")
    print(f"📁 Output directory: {output_dir}")
    print(f"⚠️ This is a short demo - only ~4 trading signals will be generated")
    print(f"💡 For full backtesting, use the main backtest.py script with longer periods")
    
    try:
        engine = BacktestingEngine(start_date, end_date, output_dir)
        results = engine.run_full_backtest()
        
        if results:
            print(f"\n🎉 Example backtest completed successfully!")
            print(f"📊 Check the '{output_dir}' directory for detailed results")
            print(f"📈 Use 'python backtest_analyzer.py analyze --results-dir {output_dir}' for analysis")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Example backtest interrupted by user")
    except Exception as e:
        print(f"❌ Error during example backtest: {e}")


def show_usage_examples():
    """Show usage examples for the backtesting framework."""
    print("📚 TradingAgents Backtesting Usage Examples")
    print("=" * 50)
    
    print("\n1. 📊 BASIC BACKTESTING:")
    print("   # Run full year backtest (as specified)")
    print("   python backtest.py --start-date 2024-05-01 --end-date 2025-05-01")
    
    print("\n2. 🔄 RESUMING INTERRUPTED BACKTEST:")
    print("   # Use the same command - it will resume automatically")
    print("   python backtest.py --start-date 2024-05-01 --end-date 2025-05-01")
    
    print("\n3. 📁 CUSTOM OUTPUT DIRECTORY:")
    print("   python backtest.py --start-date 2024-05-01 --end-date 2025-05-01 --output-dir my_test")
    
    print("\n4. 📈 ANALYZING RESULTS:")
    print("   # Basic analysis")
    print("   python backtest_analyzer.py analyze --results-dir backtest_results")
    print("   ")
    print("   # Generate performance charts")
    print("   python backtest_analyzer.py chart --results-dir backtest_results")
    print("   ")
    print("   # Export to CSV")
    print("   python backtest_analyzer.py export --results-dir backtest_results")
    
    print("\n5. 🔄 COMPARING MULTIPLE STRATEGIES:")
    print("   python backtest_analyzer.py compare --compare-dirs strategy1/ strategy2/ strategy3/")
    
    print("\n6. ⚙️ ENVIRONMENT SETUP:")
    print("   export OPENAI_API_KEY=your_openai_api_key")
    print("   export FINNHUB_API_KEY=your_finnhub_api_key")
    
    print("\n7. 💡 COST CONTROL:")
    print("   • The script pauses after each signal for user confirmation")
    print("   • Press Enter to continue, 'q' to quit and save progress")
    print("   • Resume with the same command later")
    
    print("\n8. 📋 FILE STRUCTURE:")
    print("   backtest_results/")
    print("   ├── trading_signals.json    # All generated signals")
    print("   ├── progress.json          # Resume state")
    print("   ├── backtest_results.json  # Final results")
    print("   ├── portfolio_history.csv  # Exported data")
    print("   └── performance_chart.png  # Visualization")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "examples":
        show_usage_examples()
    elif len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_example_backtest()
    else:
        print("🤖 TradingAgents Backtesting Framework")
        print("=" * 40)
        print("This framework tests whether following TradingAgents")
        print("recommendations would beat buy-and-hold QQQ strategy.")
        print()
        print("Usage:")
        print(f"  python {sys.argv[0]} examples  # Show detailed usage examples")
        print(f"  python {sys.argv[0]} demo     # Run short demonstration backtest")
        print()
        print("Quick start:")
        print("  1. Set environment variables: OPENAI_API_KEY, FINNHUB_API_KEY")
        print("  2. Run: python backtest.py --start-date 2024-05-01 --end-date 2025-05-01")
        print("  3. Analyze: python backtest_analyzer.py analyze")
        print()
        print("⚠️ The full backtest will make many API calls - use cost control features!")


if __name__ == "__main__":
    main()
