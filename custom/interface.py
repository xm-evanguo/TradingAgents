#!/usr/bin/env python3
"""
TradingAgents Interface Script

This module provides a programmatic interface to the TradingAgents CLI tool,
allowing other scripts to run financial analysis without manual interaction.

Usage:
    from interface import TradingAgentsInterface
    
    # Using defaults
    interface = TradingAgentsInterface()
    result = interface.run_analysis()
    
    # Custom parameters
    interface = TradingAgentsInterface(
        ticker="AAPL",
        analysis_date="2024-12-20",
        analysts=["market", "news"],
        research_depth="medium",
        llm_provider="openai"
    )
    result = interface.run_analysis()
"""

import datetime
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum
import yfinance as yf

# Add parent directory to Python path for TradingAgents imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from cli.models import AnalystType


class ResearchDepth(str, Enum):
    """Research depth options for analysis."""
    SHALLOW = "shallow"
    MEDIUM = "medium"
    DEEP = "deep"


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"


@dataclass
class AnalysisResult:
    """Result of trading analysis."""
    ticker: str
    analysis_date: str
    decision: Dict[str, Any]
    final_state: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None


class TradingAgentsInterface:
    """
    Programmatic interface to TradingAgents CLI tool.
    
    This class allows other scripts to run financial analysis without manual interaction.
    Provides sensible defaults and validates input parameters.
    """
    
    # Default model configurations for each provider
    DEFAULT_MODELS = {
        LLMProvider.OPENAI: {
            "shallow": "o4-mini",
            "deep": "o3",
            "url": "https://api.openai.com/v1"
        },
        LLMProvider.GOOGLE: {
            "shallow": "gemini-2.5-flash",
            "deep": "gemini-2.5-pro", 
            "url": "https://generativelanguage.googleapis.com/v1"
        },
        LLMProvider.DEEPSEEK: {
            "shallow": "deepseek-chat",
            "deep": "deepseek-reasoner",
            "url": "https://api.deepseek.com/v1"
        }
    }
    
    # Research depth to rounds mapping
    DEPTH_ROUNDS = {
        ResearchDepth.SHALLOW: 1,
        ResearchDepth.MEDIUM: 3,
        ResearchDepth.DEEP: 5
    }
    
    def __init__(
        self,
        ticker: str = "SPY",
        analysis_date: Optional[str] = None,
        analysts: Optional[List[Union[str, AnalystType]]] = None,
        research_depth: Union[str, ResearchDepth] = ResearchDepth.SHALLOW,
        llm_provider: Union[str, LLMProvider] = LLMProvider.OPENAI,
        shallow_model: Optional[str] = None,
        deep_model: Optional[str] = None,
        backend_url: Optional[str] = None,
        debug: bool = False,
        results_dir: Optional[str] = None
    ):
        """
        Initialize TradingAgents interface.
        
        Args:
            ticker: Stock ticker symbol (default: "SPY")
            analysis_date: Analysis date in YYYY-MM-DD format (default: today)
            analysts: List of analysts to use (default: all available)
            research_depth: Research depth level (default: "shallow")
            llm_provider: LLM provider to use (default: "openai")
            shallow_model: Model for quick thinking (default: provider default)
            deep_model: Model for deep thinking (default: provider default) 
            backend_url: Custom backend URL (default: provider default)
            debug: Enable debug mode (default: False)
            results_dir: Custom results directory (default: None)
        """
        self.ticker = ticker.upper()
        
        # Validate ticker
        if not self.ticker or self.ticker.strip() == "":
            raise ValueError("Ticker symbol cannot be empty")
        
        # Validate ticker exists using Yahoo Finance
        self._validate_ticker()
        
        self.analysis_date = analysis_date or datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Validate and set analysts
        if analysts is None:
            self.analysts = [AnalystType.MARKET, AnalystType.NEWS, AnalystType.FUNDAMENTALS]
        else:
            self.analysts = self._validate_analysts(analysts)
        
        # Validate and set research depth
        if isinstance(research_depth, str):
            try:
                self.research_depth = ResearchDepth(research_depth.lower())
            except ValueError:
                raise ValueError(f"Invalid research depth: {research_depth}. Must be one of: {list(ResearchDepth)}")
        else:
            self.research_depth = research_depth
            
        # Validate and set LLM provider
        if isinstance(llm_provider, str):
            try:
                self.llm_provider = LLMProvider(llm_provider.lower())
            except ValueError:
                raise ValueError(f"Invalid LLM provider: {llm_provider}. Must be one of: {list(LLMProvider)}")
        else:
            self.llm_provider = llm_provider
        
        # Set models and backend URL
        provider_defaults = self.DEFAULT_MODELS[self.llm_provider]
        self.shallow_model = shallow_model or provider_defaults["shallow"]
        self.deep_model = deep_model or provider_defaults["deep"]
        self.backend_url = backend_url or provider_defaults["url"]
        
        self.debug = debug
        self.results_dir = results_dir
        
        # Validate date
        self._validate_date()
    
    def _validate_ticker(self):
        """Validate ticker exists using Yahoo Finance."""
        try:
            # Try to fetch basic info for the ticker
            ticker_obj = yf.Ticker(self.ticker)
            info = ticker_obj.info
            
            # Check if the ticker is valid by looking for basic info
            if not info or 'symbol' not in info or info.get('regularMarketPrice') is None:
                # Try to get recent data as another validation
                hist = ticker_obj.history(period="5d")
                if hist.empty:
                    raise ValueError(f"Invalid ticker symbol: {self.ticker}. Ticker not found on Yahoo Finance.")
        except Exception as e:
            if "Invalid ticker symbol" in str(e):
                raise e
            raise ValueError(f"Unable to validate ticker {self.ticker}: {str(e)}. Please check if the ticker symbol is correct.")
    
    def _validate_analysts(self, analysts: List[Union[str, AnalystType]]) -> List[AnalystType]:
        """Validate and convert analyst specifications."""
        validated = []
        for analyst in analysts:
            if isinstance(analyst, str):
                try:
                    validated.append(AnalystType(analyst.lower()))
                except ValueError:
                    raise ValueError(f"Invalid analyst type: {analyst}. Must be one of: {list(AnalystType)}")
            elif isinstance(analyst, AnalystType):
                validated.append(analyst)
            else:
                raise ValueError(f"Invalid analyst specification: {analyst}")
        
        if not validated:
            raise ValueError("At least one analyst must be specified")
        
        return validated
    
    def _validate_date(self):
        """Validate the analysis date format and constraints."""
        try:
            analysis_date = datetime.datetime.strptime(self.analysis_date, "%Y-%m-%d")
            if analysis_date.date() > datetime.datetime.now().date():
                raise ValueError("Analysis date cannot be in the future")
        except ValueError as e:
            if "time data" in str(e):
                raise ValueError(f"Invalid date format: {self.analysis_date}. Use YYYY-MM-DD format")
            raise
    
    def get_config(self) -> Dict[str, Any]:
        """Get the configuration dictionary for TradingAgents."""
        config = DEFAULT_CONFIG.copy()
        
        # Set research depth (number of debate rounds)
        rounds = self.DEPTH_ROUNDS[self.research_depth]
        config["max_debate_rounds"] = rounds
        config["max_risk_discuss_rounds"] = rounds
        
        # Set LLM models and provider
        config["quick_think_llm"] = self.shallow_model
        config["deep_think_llm"] = self.deep_model
        config["backend_url"] = self.backend_url
        config["llm_provider"] = self.llm_provider.value
        
        # Set results directory if specified
        if self.results_dir:
            config["results_dir"] = self.results_dir
            
        return config
    
    def run_analysis(self, silent: bool = False) -> AnalysisResult:
        """
        Run the trading analysis with the configured parameters.
        
        Args:
            silent: If True, suppress console output (default: False)
            
        Returns:
            AnalysisResult containing the analysis results and metadata
        """
        try:
            if not silent:
                print(f"Starting TradingAgents analysis...")
                print(f"Ticker: {self.ticker}")
                print(f"Date: {self.analysis_date}")
                print(f"Analysts: {[a.value for a in self.analysts]}")
                print(f"Research Depth: {self.research_depth.value}")
                print(f"LLM Provider: {self.llm_provider.value}")
                print(f"Models: {self.shallow_model} (shallow), {self.deep_model} (deep)")
                print("-" * 50)
            
            # Create configuration
            config = self.get_config()
            
            # Initialize TradingAgents graph
            graph = TradingAgentsGraph(
                [analyst.value for analyst in self.analysts],
                config=config,
                debug=self.debug
            )
            
            # Run the analysis
            final_state, decision = graph.propagate(self.ticker, self.analysis_date)
            
            if not silent:
                print("Analysis completed successfully!")
            
            return AnalysisResult(
                ticker=self.ticker,
                analysis_date=self.analysis_date,
                decision=decision,
                final_state=final_state,
                success=True
            )
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            if not silent:
                print(f"Error: {error_msg}")
            
            return AnalysisResult(
                ticker=self.ticker,
                analysis_date=self.analysis_date,
                decision={},
                final_state={},
                success=False,
                error_message=error_msg
            )
    
    def run_analysis_quiet(self) -> AnalysisResult:
        """Run analysis with minimal output."""
        return self.run_analysis(silent=True)
    
    @classmethod
    def quick_analysis(
        cls,
        ticker: str,
        analysis_date: Optional[str] = None,
        **kwargs
    ) -> AnalysisResult:
        """
        Convenience method for quick analysis with minimal configuration.
        
        Args:
            ticker: Stock ticker symbol
            analysis_date: Analysis date (default: today)
            **kwargs: Additional configuration options
            
        Returns:
            AnalysisResult
        """
        interface = cls(
            ticker=ticker,
            analysis_date=analysis_date,
            **kwargs
        )
        return interface.run_analysis_quiet()

    @classmethod
    def quick_test(
        cls,
        ticker: str,
        analysis_date: Optional[str] = None,
        **kwargs
    ) -> AnalysisResult:
        """
        Convenience method for quick testing with fast models.
        Uses gpt-4.1-nano for both shallow and deep thinking to speed up testing.
        
        Args:
            ticker: Stock ticker symbol
            analysis_date: Analysis date (default: today)
            **kwargs: Additional configuration options
            
        Returns:
            AnalysisResult
        """
        # Use OpenAI provider with fast models for testing
        kwargs['llm_provider'] = LLMProvider.OPENAI
        kwargs['shallow_model'] = "gpt-4.1-nano"
        kwargs['deep_model'] = "gpt-4.1-nano"
        kwargs['research_depth'] = kwargs.get('research_depth', ResearchDepth.SHALLOW)
        
        interface = cls(
            ticker=ticker,
            analysis_date=analysis_date,
            **kwargs
        )
        return interface.run_analysis_quiet()


def main():
    """Command line interface for the interface script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="TradingAgents Interface - Programmatic access to financial analysis"
    )
    parser.add_argument("--ticker", default="SPY", help="Stock ticker symbol")
    parser.add_argument("--date", help="Analysis date (YYYY-MM-DD)")
    parser.add_argument(
        "--analysts", 
        nargs="+", 
        choices=["market", "social", "news", "fundamentals"],
        help="Analysts to use"
    )
    parser.add_argument(
        "--depth",
        choices=["shallow", "medium", "deep"],
        default="shallow",
        help="Research depth"
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "google", "deepseek"],
        default="openai",
        help="LLM provider"
    )
    parser.add_argument("--shallow-model", help="Model for quick thinking")
    parser.add_argument("--deep-model", help="Model for deep thinking")
    parser.add_argument("--backend-url", help="Custom backend URL")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--silent", action="store_true", help="Suppress output")
    parser.add_argument("--fast", action="store_true", help="Use fast models for testing (gpt-4.1-nano for both shallow and deep)")
    
    args = parser.parse_args()
    
    # Override models for fast testing
    if args.fast:
        args.shallow_model = "gpt-4.1-nano"
        args.deep_model = "gpt-4.1-nano"
        args.provider = "openai"
    
    # Create interface
    interface = TradingAgentsInterface(
        ticker=args.ticker,
        analysis_date=args.date,
        analysts=args.analysts,
        research_depth=args.depth,
        llm_provider=args.provider,
        shallow_model=args.shallow_model,
        deep_model=args.deep_model,
        backend_url=args.backend_url,
        debug=args.debug
    )
    
    # Run analysis
    result = interface.run_analysis(silent=args.silent)
    
    if result.success:
        if not args.silent:
            print("\nAnalysis Summary:")
            print(f"Decision: {result.decision}")
        sys.exit(0)
    else:
        print(f"Analysis failed: {result.error_message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
