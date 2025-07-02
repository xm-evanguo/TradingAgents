#!/usr/bin/env python3
"""
TradingAgents Backtesting Helper Script

This script provides utilities for managing and analyzing TradingAgents backtesting results.
"""

import json
import pandas as pd
from pathlib import Path
import argparse
from datetime import datetime
import sys

# Optional imports for visualization
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False


def load_results(results_dir: str) -> dict:
    """Load backtesting results from directory."""
    results_path = Path(results_dir) / "backtest_results.json"
    
    if not results_path.exists():
        print(f"❌ No results found in {results_dir}")
        return None
    
    with open(results_path, 'r') as f:
        return json.load(f)


def analyze_signals(results_dir: str):
    """Analyze trading signals from backtesting."""
    signals_path = Path(results_dir) / "trading_signals.json"
    
    if not signals_path.exists():
        print(f"❌ No signals found in {results_dir}")
        return
    
    with open(signals_path, 'r') as f:
        signals = json.load(f)
    
    print(f"\n📊 SIGNAL ANALYSIS")
    print(f"=" * 40)
    print(f"Total signals: {len(signals)}")
    
    # Analyze decision types
    decision_types = {'buy': 0, 'sell': 0, 'hold': 0}
    confidence_levels = {'high': 0, 'moderate': 0, 'low': 0}
    
    for date, signal in signals.items():
        decision = signal['decision'].lower()
        
        if 'buy' in decision or 'long' in decision:
            decision_types['buy'] += 1
        elif 'sell' in decision or 'short' in decision:
            decision_types['sell'] += 1
        else:
            decision_types['hold'] += 1
        
        if 'strong' in decision or 'high confidence' in decision:
            confidence_levels['high'] += 1
        elif 'moderate' in decision:
            confidence_levels['moderate'] += 1
        else:
            confidence_levels['low'] += 1
    
    print(f"\nDecision Distribution:")
    for decision_type, count in decision_types.items():
        percentage = (count / len(signals)) * 100
        print(f"  {decision_type.title()}: {count} ({percentage:.1f}%)")
    
    print(f"\nConfidence Distribution:")
    for confidence, count in confidence_levels.items():
        percentage = (count / len(signals)) * 100
        print(f"  {confidence.title()}: {count} ({percentage:.1f}%)")


def create_performance_chart(results_dir: str):
    """Create performance visualization charts."""
    if not HAS_MATPLOTLIB:
        print("❌ matplotlib required for charts. Install with: pip install matplotlib")
        return
    
    results = load_results(results_dir)
    if not results:
        return
    
    # Create performance chart
    portfolio_history = results['portfolio_history']
    df = pd.DataFrame(portfolio_history)
    df['date'] = pd.to_datetime(df['date'])
    
    plt.figure(figsize=(12, 8))
    
    # Plot portfolio values
    plt.subplot(2, 2, 1)
    plt.plot(df['date'], df['agent_value'], label='TradingAgents Strategy', linewidth=2)
    plt.plot(df['date'], df['buy_hold_value'], label='Buy & Hold QQQ', linewidth=2)
    plt.title('Portfolio Value Over Time')
    plt.xlabel('Date')
    plt.ylabel('Portfolio Value ($)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.ticklabel_format(style='plain', axis='y')
    
    # Plot returns
    plt.subplot(2, 2, 2)
    df['agent_return'] = (df['agent_value'] / results['initial_capital'] - 1) * 100
    df['buy_hold_return'] = (df['buy_hold_value'] / results['initial_capital'] - 1) * 100
    
    plt.plot(df['date'], df['agent_return'], label='TradingAgents Strategy', linewidth=2)
    plt.plot(df['date'], df['buy_hold_return'], label='Buy & Hold QQQ', linewidth=2)
    plt.title('Cumulative Returns (%)')
    plt.xlabel('Date')
    plt.ylabel('Return (%)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot outperformance
    plt.subplot(2, 2, 3)
    df['outperformance'] = df['agent_return'] - df['buy_hold_return']
    plt.plot(df['date'], df['outperformance'], color='green', linewidth=2)
    plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    plt.title('Outperformance vs Buy & Hold (%)')
    plt.xlabel('Date')
    plt.ylabel('Outperformance (%)')
    plt.grid(True, alpha=0.3)
    
    # Plot cash vs shares allocation
    plt.subplot(2, 2, 4)
    df['cash_ratio'] = df['agent_cash'] / df['agent_value'] * 100
    df['shares_ratio'] = (df['agent_shares'] * df['price']) / df['agent_value'] * 100
    
    plt.plot(df['date'], df['cash_ratio'], label='Cash %', linewidth=2)
    plt.plot(df['date'], df['shares_ratio'], label='Shares %', linewidth=2)
    plt.title('Portfolio Allocation')
    plt.xlabel('Date')
    plt.ylabel('Allocation (%)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save chart
    chart_path = Path(results_dir) / "performance_chart.png"
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    print(f"📈 Chart saved to {chart_path}")
    
    plt.show()


def compare_strategies(results_dirs: list):
    """Compare multiple backtesting results."""
    results_list = []
    
    for results_dir in results_dirs:
        results = load_results(results_dir)
        if results:
            results['strategy_name'] = Path(results_dir).name
            results_list.append(results)
    
    if len(results_list) < 2:
        print("❌ Need at least 2 result directories for comparison")
        return
    
    print(f"\n🔄 STRATEGY COMPARISON")
    print(f"=" * 60)
    
    comparison_data = []
    for results in results_list:
        comparison_data.append({
            'Strategy': results['strategy_name'],
            'Final Value': f"${results['final_values']['agent_strategy']:,.2f}",
            'Total Return': f"{results['returns']['agent_strategy']*100:+.2f}%",
            'vs Buy&Hold': f"{results['outperformance']['relative']*100:+.2f}%",
            'Transactions': len(results['transactions'])
        })
    
    df = pd.DataFrame(comparison_data)
    print(df.to_string(index=False))


def export_to_csv(results_dir: str):
    """Export results to CSV format."""
    results = load_results(results_dir)
    if not results:
        return
    
    output_dir = Path(results_dir)
    
    # Export portfolio history
    portfolio_df = pd.DataFrame(results['portfolio_history'])
    portfolio_path = output_dir / "portfolio_history.csv"
    portfolio_df.to_csv(portfolio_path, index=False)
    print(f"📊 Portfolio history exported to {portfolio_path}")
    
    # Export transactions
    if results['transactions']:
        transactions_df = pd.DataFrame(results['transactions'])
        transactions_path = output_dir / "transactions.csv"
        transactions_df.to_csv(transactions_path, index=False)
        print(f"📋 Transactions exported to {transactions_path}")
    
    # Export summary
    summary_data = {
        'Metric': [
            'Period Start',
            'Period End',
            'Initial Capital',
            'Final Agent Value',
            'Final Buy&Hold Value',
            'Agent Return',
            'Buy&Hold Return',
            'Absolute Outperformance',
            'Relative Outperformance',
            'Total Transactions'
        ],
        'Value': [
            results['period']['start_date'],
            results['period']['end_date'],
            f"${results['initial_capital']:,.2f}",
            f"${results['final_values']['agent_strategy']:,.2f}",
            f"${results['final_values']['buy_hold_strategy']:,.2f}",
            f"{results['returns']['agent_strategy']*100:.2f}%",
            f"{results['returns']['buy_hold_strategy']*100:.2f}%",
            f"${results['outperformance']['absolute']:,.2f}",
            f"{results['outperformance']['relative']*100:.2f}%",
            len(results['transactions'])
        ]
    }
    
    summary_df = pd.DataFrame(summary_data)
    summary_path = output_dir / "summary.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"📈 Summary exported to {summary_path}")


def main():
    parser = argparse.ArgumentParser(description='TradingAgents Backtesting Analysis Tools')
    parser.add_argument('command', choices=['analyze', 'chart', 'compare', 'export'], 
                       help='Analysis command to run')
    parser.add_argument('--results-dir', default='backtest_results', 
                       help='Backtesting results directory')
    parser.add_argument('--compare-dirs', nargs='+', 
                       help='Directories to compare (for compare command)')
    
    args = parser.parse_args()
    
    if args.command == 'analyze':
        analyze_signals(args.results_dir)
        results = load_results(args.results_dir)
        if results:
            print(f"\n🏆 PERFORMANCE SUMMARY")
            print(f"=" * 40)
            agent_return = results['returns']['agent_strategy'] * 100
            buy_hold_return = results['returns']['buy_hold_strategy'] * 100
            outperformance = results['outperformance']['relative'] * 100
            print(f"Agent Return: {agent_return:+.2f}%")
            print(f"Buy&Hold Return: {buy_hold_return:+.2f}%")
            print(f"Outperformance: {outperformance:+.2f}%")
    
    elif args.command == 'chart':
        create_performance_chart(args.results_dir)
    
    elif args.command == 'compare':
        if not args.compare_dirs:
            print("❌ --compare-dirs required for compare command")
            sys.exit(1)
        compare_strategies(args.compare_dirs)
    
    elif args.command == 'export':
        export_to_csv(args.results_dir)


if __name__ == "__main__":
    main()
