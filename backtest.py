#!/usr/bin/env python3
"""
TradingAgents Backtesting Script

This script performs backtesting of the TradingAgents framework by:
1. Running weekly analysis on QQQ every Monday (or next trading day)
2. Saving agent suggestions locally
3. Simulating trades based on agent recommendations
4. Comparing performance against buy-and-hold QQQ strategy

Usage:
    python backtest.py --start-date 2024-05-01 --end-date 2025-05-01
    
The script saves progress locally and can be resumed from where it left off.
"""

import os
import sys
import json
import argparse
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import traceback

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG


class BacktestingEngine:
    """Main backtesting engine for TradingAgents framework."""
    
    def __init__(self, start_date: str, end_date: str, output_dir: str = "backtest_results"):
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize paths for saving data
        self.signals_file = self.output_dir / "trading_signals.json"
        self.progress_file = self.output_dir / "progress.json"
        self.backtest_results_file = self.output_dir / "backtest_results.json"
        
        # Initialize TradingAgents with optimized config for backtesting
        self.config = self._setup_config()
        # Remove Social Media Analyst from the team
        selected_analysts = ["market", "news", "fundamentals"]
        self.trading_agent = TradingAgentsGraph(selected_analysts=selected_analysts, debug=True, config=self.config)
        
        # Initialize data structures
        self.trading_signals = self._load_trading_signals()
        self.progress = self._load_progress()
        self.market_data = None
        
        print(f"🤖 TradingAgents Backtesting Engine Initialized")
        print(f"📅 Period: {start_date} to {end_date}")
        print(f"📁 Output Directory: {self.output_dir}")

    def _setup_config(self) -> Dict:
        """Setup TradingAgents configuration for backtesting."""
        config = DEFAULT_CONFIG.copy()
        
        # Use cost-efficient models as specified
        config["llm_provider"] = "openai"
        config["backend_url"] = "https://api.openai.com/v1"
        config["deep_think_llm"] = "o4-mini"        # Deep-Thinking LLM Engine
        config["quick_think_llm"] = "gpt-4.1-mini"   # Quick thinking LLM engine
        
        # Use shallow research settings for cost efficiency
        config["max_debate_rounds"] = 1  # Shallow research depth
        config["max_risk_discuss_rounds"] = 1
        config["online_tools"] = True  # Use real-time data
        
        print("⚙️  Using optimized config for backtesting")
        return config
    
    def _load_trading_signals(self) -> Dict:
        """Load existing trading signals from file."""
        if self.signals_file.exists():
            with open(self.signals_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_trading_signals(self):
        """Save trading signals to file."""
        with open(self.signals_file, 'w') as f:
            json.dump(self.trading_signals, f, indent=2, default=str)
    
    def _load_progress(self) -> Dict:
        """Load progress from file."""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                progress = json.load(f)
                # Convert string dates back to datetime
                if 'last_processed_date' in progress:
                    progress['last_processed_date'] = datetime.fromisoformat(progress['last_processed_date'])
                return progress
        return {'last_processed_date': None, 'total_signals': 0}
    
    def _save_progress(self):
        """Save progress to file."""
        progress = self.progress.copy()
        # Convert datetime to string for JSON serialization
        if progress['last_processed_date']:
            progress['last_processed_date'] = progress['last_processed_date'].isoformat()
        
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def get_trading_mondays(self) -> List[datetime]:
        """Generate list of Mondays in the date range for weekly analysis."""
        mondays = []
        current_date = self.start_date
        
        # Find the first Monday
        while current_date.weekday() != 0:  # 0 = Monday
            current_date += timedelta(days=1)
        
        while current_date <= self.end_date:
            mondays.append(current_date)
            current_date += timedelta(days=7)  # Next Monday
        
        return mondays
    
    def is_trading_day(self, date: datetime) -> bool:
        """Check if a given date is a trading day using QQQ data."""
        try:
            # Download QQQ data for the specific date and a few days around it
            start_check = date - timedelta(days=5)
            end_check = date + timedelta(days=5)
            
            ticker = yf.Ticker("QQQ")
            data = ticker.history(start=start_check, end=end_check)
            
            # Check if there's data for the specific date
            date_str = date.strftime('%Y-%m-%d')
            return date_str in data.index.strftime('%Y-%m-%d')
        except Exception as e:
            print(f"⚠️ Error checking trading day for {date}: {e}")
            return True  # Assume it's a trading day if we can't check
    
    def get_next_trading_day(self, date: datetime) -> datetime:
        """Get the next trading day if the given date is not a trading day."""
        current_date = date
        max_attempts = 10  # Prevent infinite loop
        attempts = 0
        
        while not self.is_trading_day(current_date) and attempts < max_attempts:
            current_date += timedelta(days=1)
            attempts += 1
        
        return current_date
    
    def get_agent_signal(self, date: datetime) -> Optional[Dict]:
        """Get trading signal from TradingAgents for a specific date."""
        date_str = date.strftime('%Y-%m-%d')
        
        print(f"\n🔍 Analyzing QQQ for {date_str}...")
        print("🎯 Configuration:")
        print("   • Ticker: QQQ")
        print("   • Analysts Team: Market, News, Fundamentals (Social Media Analyst excluded)")
        print("   • Research Depth: Shallow - Quick research")
        print("   • LLM Provider: OpenAI")
        print("   • Quick Thinking: gpt-4o-mini")
        print("   • Deep Thinking: o1-mini")
        
        try:
            # Run TradingAgents analysis
            _, decision = self.trading_agent.propagate("QQQ", date_str)
            
            signal = {
                'date': date_str,
                'ticker': 'QQQ',
                'analysis_date': datetime.now().isoformat(),
                'decision': decision,
                'config_used': {
                    'deep_think_llm': self.config['deep_think_llm'],
                    'quick_think_llm': self.config['quick_think_llm'],
                    'max_debate_rounds': self.config['max_debate_rounds']
                }
            }
            
            print(f"✅ Analysis completed for {date_str}")
            print(f"📊 Decision: {decision}")
            
            return signal
            
        except Exception as e:
            print(f"❌ Error analyzing {date_str}: {e}")
            print(f"📝 Traceback: {traceback.format_exc()}")
            return None
    
    def run_signal_generation(self):
        """Run the signal generation phase of backtesting."""
        print(f"\n🚀 Starting Signal Generation Phase")
        print(f"📅 Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        
        trading_mondays = self.get_trading_mondays()
        print(f"📊 Total Mondays to analyze: {len(trading_mondays)}")
        
        # Resume from last processed date if available
        start_index = 0
        if self.progress['last_processed_date']:
            print(f"🔄 Resuming from {self.progress['last_processed_date'].strftime('%Y-%m-%d')}")
            start_index = next(
                (i for i, date in enumerate(trading_mondays) 
                 if date > self.progress['last_processed_date']), 
                len(trading_mondays)
            )
        
        for i, monday in enumerate(trading_mondays[start_index:], start_index):
            # Check if this date was already processed
            date_str = monday.strftime('%Y-%m-%d')
            if date_str in self.trading_signals:
                print(f"⏭️ Skipping {date_str} (already processed)")
                continue
            
            # Get the actual trading day (Monday or next trading day)
            trading_day = self.get_next_trading_day(monday)
            trading_day_str = trading_day.strftime('%Y-%m-%d')
            
            if trading_day_str != date_str:
                print(f"📅 {date_str} (Monday) -> {trading_day_str} (next trading day)")
            
            # Get signal from TradingAgents
            signal = self.get_agent_signal(trading_day)
            
            if signal:
                self.trading_signals[trading_day_str] = signal
                self._save_trading_signals()
                
                # Update progress
                self.progress['last_processed_date'] = trading_day
                self.progress['total_signals'] = len(self.trading_signals)
                self._save_progress()
                
                print(f"💾 Signal saved for {trading_day_str}")
            
            # Pause for user confirmation to control costs
            print(f"\n⏸️ Processed {i+1}/{len(trading_mondays)} signals")
            print(f"💰 Token usage checkpoint - Press Enter to continue, 'q' to quit: ", end='')
            
            user_input = input().strip().lower()
            if user_input == 'q':
                print("⏹️ Stopping signal generation at user request")
                print(f"💾 Progress saved. You can resume later with the same command.")
                return False
        
        print(f"\n✅ Signal generation completed!")
        print(f"📊 Total signals generated: {len(self.trading_signals)}")
        return True
    
    def load_market_data(self):
        """Load QQQ market data for the backtesting period."""
        print(f"\n📈 Loading QQQ market data...")
        
        # Add some buffer to ensure we have data
        start_buffer = self.start_date - timedelta(days=30)
        end_buffer = self.end_date + timedelta(days=30)
        
        try:
            ticker = yf.Ticker("QQQ")
            self.market_data = ticker.history(
                start=start_buffer.strftime('%Y-%m-%d'),
                end=end_buffer.strftime('%Y-%m-%d')
            )
            
            print(f"✅ Loaded {len(self.market_data)} days of QQQ data")
            print(f"📅 Data range: {self.market_data.index[0].strftime('%Y-%m-%d')} to {self.market_data.index[-1].strftime('%Y-%m-%d')}")
            
        except Exception as e:
            print(f"❌ Error loading market data: {e}")
            raise
    
    def simulate_trading(self) -> Dict:
        """Simulate trading based on agent signals and compare with buy-and-hold."""
        print(f"\n💹 Starting Trading Simulation...")
        
        if not self.market_data is not None:
            self.load_market_data()
        
        # Initialize portfolios
        initial_capital = 100000  # $100,000
        agent_portfolio = {
            'cash': initial_capital,
            'shares': 0,
            'total_value': initial_capital,
            'transactions': []
        }
        
        # Buy-and-hold strategy: buy at start date
        start_price = self.market_data.loc[self.market_data.index >= self.start_date.strftime('%Y-%m-%d')].iloc[0]['Close']
        buy_hold_shares = initial_capital / start_price
        
        # Track portfolio values over time
        portfolio_history = []
        
        # Sort signals by date
        sorted_signals = sorted(self.trading_signals.items(), key=lambda x: x[0])
        
        print(f"📊 Simulating {len(sorted_signals)} trading signals...")
        print(f"💰 Initial capital: ${initial_capital:,.2f}")
        print(f"📈 Buy-and-hold: {buy_hold_shares:.2f} shares at ${start_price:.2f}")
        
        for date_str, signal in sorted_signals:
            signal_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Get market data for this date
            try:
                market_row = self.market_data.loc[date_str]
                current_price = market_row['Close']
            except KeyError:
                # Try to find the nearest trading day
                nearest_date = self.market_data.index[self.market_data.index >= date_str][0]
                market_row = self.market_data.loc[nearest_date]
                current_price = market_row['Close']
                print(f"⚠️ Using {nearest_date.strftime('%Y-%m-%d')} data for signal date {date_str}")
            
            # Parse agent decision and execute trade
            decision = signal['decision']
            action = self.parse_agent_decision(decision)
            
            if action['action'] in ['buy', 'sell']:
                transaction = self.execute_trade(
                    agent_portfolio, 
                    action, 
                    current_price, 
                    signal_date
                )
                if transaction:
                    print(f"📅 {date_str}: {transaction['action'].upper()} {transaction['shares']:.2f} shares at ${current_price:.2f}")
            
            # Update portfolio value
            agent_portfolio['total_value'] = agent_portfolio['cash'] + (agent_portfolio['shares'] * current_price)
            
            # Track performance
            buy_hold_value = buy_hold_shares * current_price
            
            portfolio_history.append({
                'date': date_str,
                'agent_value': agent_portfolio['total_value'],
                'buy_hold_value': buy_hold_value,
                'price': current_price,
                'agent_cash': agent_portfolio['cash'],
                'agent_shares': agent_portfolio['shares']
            })
        
        # Calculate final results
        final_date = self.end_date.strftime('%Y-%m-%d')
        try:
            final_price = self.market_data.loc[final_date]['Close']
        except KeyError:
            final_price = self.market_data.iloc[-1]['Close']
            final_date = self.market_data.index[-1].strftime('%Y-%m-%d')
        
        final_agent_value = agent_portfolio['cash'] + (agent_portfolio['shares'] * final_price)
        final_buy_hold_value = buy_hold_shares * final_price
        
        results = {
            'period': {
                'start_date': self.start_date.strftime('%Y-%m-%d'),
                'end_date': final_date,
                'days': len(portfolio_history)
            },
            'initial_capital': initial_capital,
            'final_values': {
                'agent_strategy': final_agent_value,
                'buy_hold_strategy': final_buy_hold_value
            },
            'returns': {
                'agent_strategy': (final_agent_value - initial_capital) / initial_capital,
                'buy_hold_strategy': (final_buy_hold_value - initial_capital) / initial_capital
            },
            'outperformance': {
                'absolute': final_agent_value - final_buy_hold_value,
                'relative': (final_agent_value - final_buy_hold_value) / final_buy_hold_value
            },
            'transactions': agent_portfolio['transactions'],
            'portfolio_history': portfolio_history,
            'final_portfolio': {
                'cash': agent_portfolio['cash'],
                'shares': agent_portfolio['shares'],
                'total_value': final_agent_value
            }
        }
        
        return results
    
    def parse_agent_decision(self, decision: str) -> Dict:
        """Parse agent decision to extract trading action and parameters."""
        # This is a simplified parser - you may need to adjust based on actual decision format
        decision_lower = decision.lower()
        
        if 'buy' in decision_lower or 'long' in decision_lower:
            return {'action': 'buy', 'confidence': self.extract_confidence(decision)}
        elif 'sell' in decision_lower or 'short' in decision_lower:
            return {'action': 'sell', 'confidence': self.extract_confidence(decision)}
        else:
            return {'action': 'hold', 'confidence': 0.5}
    
    def extract_confidence(self, decision: str) -> float:
        """Extract confidence level from decision text."""
        # Simple confidence extraction - you may want to make this more sophisticated
        if 'strong' in decision.lower() or 'high confidence' in decision.lower():
            return 0.8
        elif 'moderate' in decision.lower():
            return 0.6
        elif 'weak' in decision.lower() or 'low confidence' in decision.lower():
            return 0.4
        else:
            return 0.5
    
    def execute_trade(self, portfolio: Dict, action: Dict, price: float, date: datetime) -> Optional[Dict]:
        """Execute a trade based on the action and update portfolio."""
        if action['action'] == 'buy':
            # Use confidence to determine position size (max 20% of portfolio per trade)
            max_trade_size = portfolio['total_value'] * 0.2 * action['confidence']
            trade_amount = min(max_trade_size, portfolio['cash'])
            
            if trade_amount >= 100:  # Minimum trade size
                shares_to_buy = trade_amount / price
                cost = shares_to_buy * price
                
                portfolio['cash'] -= cost
                portfolio['shares'] += shares_to_buy
                
                transaction = {
                    'date': date.strftime('%Y-%m-%d'),
                    'action': 'buy',
                    'shares': shares_to_buy,
                    'price': price,
                    'amount': cost,
                    'confidence': action['confidence']
                }
                portfolio['transactions'].append(transaction)
                return transaction
        
        elif action['action'] == 'sell' and portfolio['shares'] > 0:
            # Sell based on confidence (max 50% of holdings per trade)
            max_sell_ratio = 0.5 * action['confidence']
            shares_to_sell = portfolio['shares'] * max_sell_ratio
            
            if shares_to_sell >= 0.01:  # Minimum sell size
                proceeds = shares_to_sell * price
                
                portfolio['cash'] += proceeds
                portfolio['shares'] -= shares_to_sell
                
                transaction = {
                    'date': date.strftime('%Y-%m-%d'),
                    'action': 'sell',
                    'shares': shares_to_sell,
                    'price': price,
                    'amount': proceeds,
                    'confidence': action['confidence']
                }
                portfolio['transactions'].append(transaction)
                return transaction
        
        return None
    
    def save_results(self, results: Dict):
        """Save backtesting results to file."""
        with open(self.backtest_results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Results saved to {self.backtest_results_file}")
    
    def print_results(self, results: Dict):
        """Print backtesting results in a formatted way."""
        print(f"\n" + "="*60)
        print(f"🏆 BACKTESTING RESULTS")
        print(f"="*60)
        
        print(f"📅 Period: {results['period']['start_date']} to {results['period']['end_date']}")
        print(f"⏱️ Trading Days: {results['period']['days']}")
        print(f"💰 Initial Capital: ${results['initial_capital']:,.2f}")
        
        print(f"\n📊 FINAL RESULTS:")
        print(f"🤖 Agent Strategy: ${results['final_values']['agent_strategy']:,.2f}")
        print(f"📈 Buy & Hold QQQ: ${results['final_values']['buy_hold_strategy']:,.2f}")
        
        print(f"\n📈 RETURNS:")
        agent_return = results['returns']['agent_strategy'] * 100
        buy_hold_return = results['returns']['buy_hold_strategy'] * 100
        print(f"🤖 Agent Strategy: {agent_return:+.2f}%")
        print(f"📈 Buy & Hold QQQ: {buy_hold_return:+.2f}%")
        
        print(f"\n🎯 OUTPERFORMANCE:")
        abs_outperf = results['outperformance']['absolute']
        rel_outperf = results['outperformance']['relative'] * 100
        print(f"💵 Absolute: ${abs_outperf:+,.2f}")
        print(f"📊 Relative: {rel_outperf:+.2f}%")
        
        print(f"\n📋 TRADING SUMMARY:")
        transactions = results['transactions']
        buy_trades = [t for t in transactions if t['action'] == 'buy']
        sell_trades = [t for t in transactions if t['action'] == 'sell']
        print(f"🛒 Buy Trades: {len(buy_trades)}")
        print(f"💰 Sell Trades: {len(sell_trades)}")
        print(f"📊 Total Transactions: {len(transactions)}")
        
        if abs_outperf > 0:
            print(f"\n🎉 The TradingAgents strategy BEAT buy-and-hold by ${abs_outperf:,.2f}!")
        else:
            print(f"\n📉 The TradingAgents strategy underperformed buy-and-hold by ${abs(-abs_outperf):,.2f}")
    
    def run_full_backtest(self):
        """Run the complete backtesting process."""
        print(f"🚀 Starting TradingAgents Backtesting Process")
        
        # Phase 1: Generate trading signals
        if not self.run_signal_generation():
            print(f"⏹️ Backtesting stopped during signal generation")
            return
        
        # Phase 2: Load market data
        self.load_market_data()
        
        # Phase 3: Simulate trading
        results = self.simulate_trading()
        
        # Phase 4: Save and display results
        self.save_results(results)
        self.print_results(results)
        
        return results


def main():
    parser = argparse.ArgumentParser(description='TradingAgents Backtesting Script')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output-dir', default='backtest_results', help='Output directory')
    
    args = parser.parse_args()
    
    # Validate date format
    try:
        datetime.strptime(args.start_date, '%Y-%m-%d')
        datetime.strptime(args.end_date, '%Y-%m-%d')
    except ValueError:
        print("❌ Error: Invalid date format. Use YYYY-MM-DD")
        sys.exit(1)
    
    # Check for required environment variables
    required_env_vars = ['OPENAI_API_KEY', 'FINNHUB_API_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them before running the backtest:")
        for var in missing_vars:
            print(f"  export {var}=your_api_key_here")
        sys.exit(1)
    
    # Initialize and run backtesting engine
    try:
        engine = BacktestingEngine(
            start_date=args.start_date, 
            end_date=args.end_date, 
            output_dir=args.output_dir,
            
        )
        engine.run_full_backtest()
    except KeyboardInterrupt:
        print(f"\n⏹️ Backtesting interrupted by user")
    except Exception as e:
        print(f"❌ Error during backtesting: {e}")
        print(f"📝 Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
