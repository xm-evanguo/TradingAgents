#!/usr/bin/env python3
"""
Batch Analysis Script for TradingAgents

This script reads a configuration file containing stock symbols and analysis settings,
then performs analysis for each symbol using the TradingAgents interface.

Usage:
    python batch_analysis.py [--config config.json] [--output output.json] [--email]
"""

import json
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse

from interface import TradingAgentsInterface, AnalysisResult
from email_service import EmailService

# Ensure log directory exists
log_dir = Path(__file__).parent.parent / "log"
log_dir.mkdir(exist_ok=True)

# Configure logging
log_file_path = log_dir / "batch_analysis.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(str(log_file_path)),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BatchAnalysisConfig:
    """Configuration for batch analysis."""
    
    def __init__(self, config_path: str = "analysis_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Validate required fields
            required_fields = ['tickers', 'analysis_settings']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field '{field}' in config file")
            
            # Validate analysis settings
            settings = config['analysis_settings']
            if 'analysts' not in settings:
                settings['analysts'] = ["market", "news", "fundamentals"]
            if 'research_depth' not in settings:
                settings['research_depth'] = "shallow"
            if 'llm_provider' not in settings:
                settings['llm_provider'] = "openai"
            
            return config
            
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            self.create_default_config()
            logger.info(f"Created default configuration at {self.config_path}")
            logger.info("Please edit the configuration file and run again.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            sys.exit(1)
    
    def create_default_config(self):
        """Create a default configuration file."""
        default_config = {
            "tickers": [
                "SPY",
                "QQQ", 
                "AAPL",
                "GOOGL",
                "MSFT",
                "TSLA",
                "NVDA"
            ],
            "analysis_settings": {
                "analysts": ["market", "news", "fundamentals"],
                "research_depth": "shallow",
                "llm_provider": "openai",
                "shallow_model": None,
                "deep_model": None,
                "backend_url": None,
                "debug": False
            },
            "email_settings": {
                "enabled": False,
                "recipients": [
                    "your-email@example.com"
                ],
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "your-sender@gmail.com",
                "sender_password": "your-app-password",
                "subject_template": "TradingAgents Analysis Results - {date}"
            },
            "output_settings": {
                "save_individual_results": True,
                "save_summary": True,
                "results_directory": "batch_results"
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)


class BatchAnalyzer:
    """Batch analyzer for multiple stocks."""
    
    def __init__(self, config: BatchAnalysisConfig):
        self.config = config
        self.results: List[AnalysisResult] = []
        self.email_service = None
        
        # Initialize email service if enabled
        if self.config.config.get('email_settings', {}).get('enabled', False):
            self.email_service = EmailService(self.config.config['email_settings'])
    
    def run_batch_analysis(self, analysis_date: Optional[str] = None) -> List[AnalysisResult]:
        """
        Run analysis for all configured tickers.
        
        Args:
            analysis_date: Date for analysis (default: today)
            
        Returns:
            List of AnalysisResult objects
        """
        if analysis_date is None:
            analysis_date = datetime.now().strftime("%Y-%m-%d")
        
        tickers = self.config.config['tickers']
        settings = self.config.config['analysis_settings']
        
        logger.info(f"Starting batch analysis for {len(tickers)} tickers")
        logger.info(f"Analysis date: {analysis_date}")
        logger.info(f"Settings: {settings}")
        
        results = []
        
        for i, ticker in enumerate(tickers, 1):
            logger.info(f"Analyzing {ticker} ({i}/{len(tickers)})")
            
            try:
                # Create interface with settings from config
                interface = TradingAgentsInterface(
                    ticker=ticker,
                    analysis_date=analysis_date,
                    analysts=settings.get('analysts'),
                    research_depth=settings.get('research_depth', 'shallow'),
                    llm_provider=settings.get('llm_provider', 'openai'),
                    shallow_model=settings.get('shallow_model'),
                    deep_model=settings.get('deep_model'),
                    backend_url=settings.get('backend_url'),
                    debug=settings.get('debug', False)
                )
                
                # Run analysis
                result = interface.run_analysis(silent=True)
                results.append(result)
                
                if result.success:
                    logger.info(f"✅ {ticker}: Analysis completed successfully")
                    if result.decision:
                        # Handle both dict and string formats for decision
                        if isinstance(result.decision, dict):
                            action = result.decision.get('action', 'N/A')
                            confidence = result.decision.get('confidence', 'N/A')
                            reasoning = result.decision.get('reasoning', 'N/A')
                            logger.info(f"   Decision: {action} (Confidence: {confidence})")
                            if reasoning != 'N/A' and len(str(reasoning)) < 200:
                                logger.info(f"   Reasoning: {reasoning}")
                        else:
                            logger.info(f"   Decision: {result.decision}")
                    
                    # Log key insights from final_state if available
                    if result.final_state and isinstance(result.final_state, dict):
                        # Look for manager's final decision reasoning
                        if 'messages' in result.final_state:
                            messages = result.final_state['messages']
                            for msg in reversed(messages):  # Start from most recent
                                if isinstance(msg, dict) and msg.get('type') == 'ai':
                                    content = msg.get('content', '')
                                    if ('final recommendation' in content.lower() or 
                                        'decision:' in content.lower() or
                                        'recommendation:' in content.lower()):
                                        # Extract key reasoning (first 300 chars)
                                        lines = content.split('\n')
                                        for line in lines:
                                            if any(keyword in line.lower() for keyword in 
                                                  ['reason', 'because', 'due to', 'analysis shows']):
                                                logger.info(f"   Key Insight: {line.strip()[:200]}")
                                                break
                                        break
                else:
                    logger.error(f"❌ {ticker}: {result.error_message}")
                    
            except Exception as e:
                error_msg = f"Unexpected error analyzing {ticker}: {str(e)}"
                logger.error(error_msg)
                
                # Create failed result
                results.append(AnalysisResult(
                    ticker=ticker,
                    analysis_date=analysis_date,
                    decision={},
                    final_state={},
                    success=False,
                    error_message=error_msg
                ))
        
        self.results = results
        return results
    
    def save_results(self, output_path: Optional[str] = None):
        """Save analysis results to file."""
        if not self.results:
            logger.warning("No results to save")
            return
        
        # Create results directory relative to project root
        results_dir = self.config.config.get('output_settings', {}).get('results_directory', 'batch_results')
        # Ensure results directory is relative to project root, not custom directory
        project_root = Path(__file__).parent.parent
        results_dir_path = project_root / results_dir
        results_dir_path.mkdir(exist_ok=True)
        
        # Save individual results if enabled
        if self.config.config.get('output_settings', {}).get('save_individual_results', True):
            for result in self.results:
                filename = f"{result.ticker}_{result.analysis_date}_result.json"
                filepath = results_dir_path / filename
                
                # Extract reasoning from final_state if available
                reasoning = {}
                if result.final_state and (isinstance(result.final_state, dict) or hasattr(result.final_state, 'items')):
                    try:
                        final_state_dict = dict(result.final_state.items()) if hasattr(result.final_state, 'items') else result.final_state
                        
                        # Extract key reasoning fields
                        if 'final_trade_decision' in final_state_dict:
                            reasoning['final_decision'] = str(final_state_dict['final_trade_decision'])[:1000]
                        
                        if 'market_report' in final_state_dict:
                            reasoning['market_analysis'] = str(final_state_dict['market_report'])[:800]
                            
                        if 'investment_plan' in final_state_dict:
                            reasoning['investment_reasoning'] = str(final_state_dict['investment_plan'])[:800]
                            
                        if 'trader_investment_plan' in final_state_dict:
                            reasoning['trader_reasoning'] = str(final_state_dict['trader_investment_plan'])[:800]
                            
                        # Extract from investment_debate_state if it's a dict
                        if 'investment_debate_state' in final_state_dict:
                            debate_state = final_state_dict['investment_debate_state']
                            if isinstance(debate_state, dict) and 'judge_decision' in debate_state:
                                reasoning['judge_decision'] = str(debate_state['judge_decision'])[:1000]
                                
                        # Extract from risk_debate_state if it's a dict  
                        if 'risk_debate_state' in final_state_dict:
                            risk_state = final_state_dict['risk_debate_state']
                            if isinstance(risk_state, dict) and 'judge_decision' in risk_state:
                                reasoning['risk_analysis'] = str(risk_state['judge_decision'])[:1000]
                                
                    except Exception as e:
                        reasoning['extraction_error'] = str(e)
                
                result_data = {
                    'ticker': result.ticker,
                    'analysis_date': result.analysis_date,
                    'success': result.success,
                    'decision': result.decision,
                    'reasoning': reasoning,
                    'error_message': result.error_message,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Also save a detailed version with full final_state
                detailed_filename = f"{result.ticker}_{result.analysis_date}_detailed.json"
                detailed_filepath = results_dir_path / detailed_filename
                
                # Convert final_state to JSON-serializable format
                serializable_final_state = self._make_json_serializable(result.final_state)
                
                detailed_data = {
                    **result_data,
                    'full_final_state': serializable_final_state
                }
                
                with open(filepath, 'w') as f:
                    json.dump(result_data, f, indent=2)
                    
                with open(detailed_filepath, 'w') as f:
                    json.dump(detailed_data, f, indent=2)
        
        # Save summary
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = results_dir_path / f"batch_summary_{timestamp}.json"
        
        summary = self.create_summary()
        
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
    
    def create_summary(self) -> Dict[str, Any]:
        """Create summary of batch analysis results."""
        if not self.results:
            return {}
        
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
        # Aggregate decisions
        buy_signals = []
        sell_signals = []
        hold_signals = []
        
        for result in successful:
            if result.decision:
                # Handle both dict and string formats for decision
                if isinstance(result.decision, dict):
                    action = result.decision.get('action', '').lower()
                else:
                    action = str(result.decision).lower()
                
                if 'buy' in action:
                    buy_signals.append(result.ticker)
                elif 'sell' in action:
                    sell_signals.append(result.ticker)
                else:
                    hold_signals.append(result.ticker)
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'analysis_date': self.results[0].analysis_date if self.results else None,
            'total_analyzed': len(self.results),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(self.results) * 100 if self.results else 0,
            'signals': {
                'buy': buy_signals,
                'sell': sell_signals,
                'hold': hold_signals
            },
            'failed_tickers': [r.ticker for r in failed],
            'detailed_results': [
                {
                    'ticker': r.ticker,
                    'success': r.success,
                    'decision': r.decision if r.success else None,
                    'reasoning_summary': self._extract_reasoning_summary(r) if r.success else None,
                    'error': r.error_message if not r.success else None
                }
                for r in self.results
            ]
        }
        
        return summary
    
    def _extract_reasoning_summary(self, result: AnalysisResult) -> Optional[str]:
        """Extract a concise reasoning summary from the analysis result."""
        if not result.final_state:
            return None
        
        try:
            # Handle AddableValuesDict and regular dicts
            final_state_dict = dict(result.final_state.items()) if hasattr(result.final_state, 'items') else result.final_state
            
            # Try to get the final trade decision first (most comprehensive)
            if 'final_trade_decision' in final_state_dict:
                decision_text = str(final_state_dict['final_trade_decision'])
                # Extract the first sentence or two as summary
                sentences = decision_text.split('. ')
                if len(sentences) >= 2:
                    return f"{sentences[0]}. {sentences[1]}"[:300]
                return sentences[0][:300] if sentences else None
            
            # Fallback to investment plan
            if 'investment_plan' in final_state_dict:
                plan_text = str(final_state_dict['investment_plan'])
                sentences = plan_text.split('. ')
                if sentences:
                    return sentences[0][:300]
            
            # Fallback to trader investment plan
            if 'trader_investment_plan' in final_state_dict:
                trader_text = str(final_state_dict['trader_investment_plan'])
                sentences = trader_text.split('. ')
                if sentences:
                    return sentences[0][:300]
                    
        except Exception as e:
            return f"Error extracting reasoning: {str(e)}"
        
        return None

    def send_email_notification(self):
        """Send email notification with results."""
        if not self.email_service:
            logger.info("Email notifications not enabled")
            return
        
        if not self.results:
            logger.warning("No results to send via email")
            return
        
        try:
            summary = self.create_summary()
            self.email_service.send_analysis_results(summary)
            logger.info("Email notification sent successfully")
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def _make_json_serializable(self, obj):
        """Convert complex objects to JSON-serializable format."""
        if hasattr(obj, '__dict__'):
            # Convert objects with __dict__ to dict
            return {k: self._make_json_serializable(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, dict) or hasattr(obj, 'items'):
            # Handle both regular dicts and AddableValuesDict
            try:
                return {k: self._make_json_serializable(v) for k, v in obj.items()}
            except:
                return str(obj)
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif hasattr(obj, 'content'):
            # Handle message objects that have content
            return {'type': getattr(obj, 'type', 'unknown'), 'content': str(obj.content)}
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            # Convert everything else to string
            return str(obj)


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(description="Batch analysis for TradingAgents")
    parser.add_argument("--config", default="analysis_config.json", help="Configuration file path")
    parser.add_argument("--output", help="Output file path for results")
    parser.add_argument("--date", help="Analysis date (YYYY-MM-DD)")
    parser.add_argument("--email", action="store_true", help="Send email notification")
    parser.add_argument("--no-save", action="store_true", help="Don't save results to file")
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = BatchAnalysisConfig(args.config)
        
        # Create analyzer
        analyzer = BatchAnalyzer(config)
        
        # Run batch analysis
        results = analyzer.run_batch_analysis(args.date)
        
        # Save results
        if not args.no_save:
            analyzer.save_results(args.output)
        
        # Send email notification if requested
        if args.email:
            analyzer.send_email_notification()
        
        # Print summary
        summary = analyzer.create_summary()
        logger.info(f"Batch analysis completed!")
        logger.info(f"Total: {summary['total_analyzed']}, Successful: {summary['successful']}, Failed: {summary['failed']}")
        logger.info(f"Success rate: {summary['success_rate']:.1f}%")
        
        if summary['signals']['buy']:
            logger.info(f"Buy signals: {', '.join(summary['signals']['buy'])}")
        if summary['signals']['sell']:
            logger.info(f"Sell signals: {', '.join(summary['signals']['sell'])}")
        
        # Exit with appropriate code
        if summary['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
