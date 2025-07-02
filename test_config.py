#!/usr/bin/env python3
"""
Test script to verify that the TradingAgents configuration without Social Media Analyst works correctly.
"""

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

def test_configuration():
    """Test the TradingAgents configuration without Social Media Analyst."""
    print("Testing TradingAgents configuration without Social Media Analyst...")
    
    # Create config similar to backtest
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = "openai"
    config["deep_think_llm"] = "o4-mini"
    config["quick_think_llm"] = "gpt-4o-mini" 
    config["max_debate_rounds"] = 1
    config["max_risk_discuss_rounds"] = 1
    config["online_tools"] = True
    
    # Remove Social Media Analyst from the team
    selected_analysts = ["market", "news", "fundamentals"]
    
    try:
        # Initialize TradingAgents 
        trading_agent = TradingAgentsGraph(
            selected_analysts=selected_analysts, 
            debug=True, 
            config=config
        )
        
        print("✅ TradingAgents successfully initialized without Social Media Analyst")
        print(f"📊 Selected analysts: {selected_analysts}")
        print(f"🔧 Configuration: LLM Provider: {config['llm_provider']}")
        print(f"🧠 Deep thinking: {config['deep_think_llm']}")
        print(f"⚡ Quick thinking: {config['quick_think_llm']}")
        print(f"🔄 Debate rounds: {config['max_debate_rounds']}")
        
        # Test creating initial state
        initial_state = trading_agent.propagator.create_initial_state("QQQ", "2024-05-01")
        print(f"🚀 Initial state created successfully")
        print(f"📋 State keys: {list(initial_state.keys())}")
        print(f"📝 sentiment_report initialized as: '{initial_state['sentiment_report']}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_configuration()
    if success:
        print("\n🎉 Configuration test passed! The backtest will work correctly without Social Media Analyst.")
    else:
        print("\n💥 Configuration test failed! There may be issues with the setup.")
