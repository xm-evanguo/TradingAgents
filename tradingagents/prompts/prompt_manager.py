"""
Prompt Manager for TradingAgents

This module provides a centralized way to load and render Jinja2 templates for prompts
used throughout the TradingAgents system.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader


class PromptManager:
    """
    Manages loading and rendering of prompt templates for TradingAgents.
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize the PromptManager.
        
        Args:
            templates_dir: Path to the templates directory. If None, uses default location.
        """
        if templates_dir is None:
            # Default to the prompts directory relative to this file
            templates_dir = Path(__file__).parent
        
        self.templates_dir = Path(templates_dir)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def render_agent_prompt(
        self, 
        agent_type: str, 
        ticker: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Render an agent prompt template.
        
        Args:
            agent_type: Type of agent (market_analyst, news_analyst, etc.)
            ticker: Stock ticker symbol
            context: Additional context variables for template rendering
            
        Returns:
            Rendered prompt string
        """
        template_path = f"agents/{agent_type}.j2"
        
        # Prepare template variables
        template_vars = {
            'instrument_type': 'stock',
            'ticker': ticker,
        }
        
        # Add any additional context
        if context:
            template_vars.update(context)
        
        # Load and render template
        template = self.env.get_template(template_path)
        return template.render(**template_vars)
    
    def render_social_media_prompt(
        self,
        prompt_type: str,
        ticker: str,
        start_date: str,
        end_date: str,
        platform: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Render a social media analysis prompt template.
        
        Args:
            prompt_type: Type of prompt (x_twitter_analysis, reddit_analysis, system_prompt)
            ticker: Stock ticker symbol
            start_date: Start date for analysis
            end_date: End date for analysis
            platform: Social media platform name (for system prompts)
            context: Additional context variables
            
        Returns:
            Rendered prompt string
        """
        template_path = f"social_media/{prompt_type}.j2"
        
        # Prepare template variables
        template_vars = {
            'instrument_type': 'stock',
            'ticker': ticker,
            'start_date': start_date,
            'end_date': end_date,
            'platform': platform,
        }
        
        # Add any additional context
        if context:
            template_vars.update(context)
        
        # Load and render template
        template = self.env.get_template(template_path)
        return template.render(**template_vars)
    
    def render_researcher_prompt(
        self,
        agent_type: str,
        ticker: str,
        market_research_report: str = "",
        sentiment_report: str = "",
        news_report: str = "",
        fundamentals_report: str = "",
        history: str = "",
        current_response: str = "",
        past_memory_str: str = "",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Render a researcher prompt template with debate context.
        
        Args:
            agent_type: Type of researcher (bull_researcher, bear_researcher)
            ticker: Stock ticker symbol
            market_research_report: Market analysis report
            sentiment_report: Social media sentiment report
            news_report: News analysis report
            fundamentals_report: Fundamentals analysis report
            history: Debate conversation history
            current_response: Most recent argument from opposing side
            past_memory_str: Past experiences and lessons learned
            context: Additional context variables
            
        Returns:
            Rendered prompt string
        """
        template_path = f"agents/{agent_type}.j2"
        
        # Prepare template variables
        template_vars = {
            'instrument_type': 'stock',
            'ticker': ticker,
            'market_research_report': market_research_report,
            'sentiment_report': sentiment_report,
            'news_report': news_report,
            'fundamentals_report': fundamentals_report,
            'history': history,
            'current_response': current_response,
            'past_memory_str': past_memory_str,
        }
        
        # Add any additional context
        if context:
            template_vars.update(context)
        
        # Load and render template
        template = self.env.get_template(template_path)
        return template.render(**template_vars)
    
    def get_available_templates(self) -> Dict[str, list]:
        """
        Get a list of all available template files.
        
        Returns:
            Dictionary with template categories and their available templates
        """
        templates = {
            'agents': [],
            'social_media': [],
            'data_flows': []
        }
        
        for category in templates.keys():
            category_path = self.templates_dir / category
            if category_path.exists():
                templates[category] = [
                    f.stem for f in category_path.glob('*.j2')
                ]
        
        return templates
    
    def validate_template(self, template_path: str) -> bool:
        """
        Validate that a template exists and can be loaded.
        
        Args:
            template_path: Path to the template file
            
        Returns:
            True if template is valid, False otherwise
        """
        try:
            self.env.get_template(template_path)
            return True
        except Exception:
            return False


# Global instance for easy access
prompt_manager = PromptManager()


def get_agent_prompt(agent_type: str, ticker: str, **kwargs) -> str:
    """
    Convenience function to get an agent prompt.
    
    Args:
        agent_type: Type of agent
        ticker: Stock ticker symbol
        **kwargs: Additional context variables
        
    Returns:
        Rendered prompt string
    """
    return prompt_manager.render_agent_prompt(agent_type, ticker, kwargs)


def get_social_media_prompt(
    prompt_type: str, 
    ticker: str, 
    start_date: str, 
    end_date: str, 
    **kwargs
) -> str:
    """
    Convenience function to get a social media prompt.
    
    Args:
        prompt_type: Type of social media prompt
        ticker: Stock ticker symbol
        start_date: Analysis start date
        end_date: Analysis end date
        **kwargs: Additional context variables
        
    Returns:
        Rendered prompt string
    """
    return prompt_manager.render_social_media_prompt(
        prompt_type, ticker, start_date, end_date, context=kwargs
    )


def get_researcher_prompt(
    agent_type: str,
    ticker: str,
    market_research_report: str = "",
    sentiment_report: str = "",
    news_report: str = "",
    fundamentals_report: str = "",
    history: str = "",
    current_response: str = "",
    past_memory_str: str = "",
    **kwargs
) -> str:
    """
    Convenience function to get a researcher prompt.
    
    Args:
        agent_type: Type of researcher (bull_researcher, bear_researcher)
        ticker: Stock ticker symbol
        market_research_report: Market analysis report
        sentiment_report: Social media sentiment report
        news_report: News analysis report
        fundamentals_report: Fundamentals analysis report
        history: Debate conversation history
        current_response: Most recent argument from opposing side
        past_memory_str: Past experiences and lessons learned
        **kwargs: Additional context variables
        
    Returns:
        Rendered prompt string
    """
    return prompt_manager.render_researcher_prompt(
        agent_type, ticker, market_research_report, sentiment_report,
        news_report, fundamentals_report, history, current_response, 
        past_memory_str, context=kwargs
    )
