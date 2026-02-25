from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

if not os.environ.get("DEEPSEEK_API_KEY"):
    print("Error: DEEPSEEK_API_KEY environment variable is not set.")
    print("Please set it in your .env file or export it in your shell to run this test.")
    exit(1)

# Create a custom config that sets the provider to deepseek
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "deepseek"
config["deep_think_llm"] = "deepseek-chat"
config["quick_think_llm"] = "deepseek-chat"
config["max_debate_rounds"] = 1  # Minimum run
config["max_risk_discuss_rounds"] = 1  # Minimum run

# Configure data vendors to use yfinance
config["data_vendors"] = {
    "core_stock_apis": "yfinance",
    "technical_indicators": "yfinance",
    "fundamental_data": "yfinance",
    "news_data": "yfinance",
}

print("Initializing TradingAgentsGraph with DeepSeek provider (only Market Analyst)...")
ta = TradingAgentsGraph(
    selected_analysts=["market"],
    debug=True,
    config=config
)

# forward propagate with a minimum run
print("Starting minimum run for NVDA on 2024-05-10...")
try:
    _, decision = ta.propagate("NVDA", "2024-05-10")
    print("\n--- Final Trading Decision ---")
    print(decision)
except Exception as e:
    print(f"\nError during run: {e}")
