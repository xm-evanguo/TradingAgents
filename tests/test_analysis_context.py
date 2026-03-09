import unittest

from tradingagents.analysis_context import (
    build_default_analysis_message,
    get_default_analysis_context,
)
from tradingagents.graph.propagation import Propagator
from tradingagents.prompts import get_agent_prompt


class AnalysisContextTest(unittest.TestCase):
    def test_default_analysis_context_matches_manual_script_windows(self) -> None:
        context = get_default_analysis_context("2026-03-09")

        self.assertEqual(context["market_start_date"], "2026-01-08")
        self.assertEqual(context["market_end_date"], "2026-03-09")
        self.assertEqual(context["market_look_back_days"], 60)
        self.assertEqual(context["news_start_date"], "2026-03-02")
        self.assertEqual(context["news_end_date"], "2026-03-09")
        self.assertEqual(context["news_look_back_days"], 7)
        self.assertEqual(context["global_news_limit"], 10)
        self.assertEqual(context["fundamentals_date"], "2026-03-09")

    def test_default_analysis_context_rejects_invalid_dates(self) -> None:
        with self.assertRaises(ValueError):
            get_default_analysis_context("2026-99-99")

    def test_graph_initial_message_and_prompts_include_default_windows(self) -> None:
        trade_date = "2026-03-09"
        context = get_default_analysis_context(trade_date)
        state = Propagator().create_initial_state("WDAY", trade_date)
        user_message = state["messages"][0][1]
        market_prompt = get_agent_prompt("market_analyst", "WDAY", **context)
        news_prompt = get_agent_prompt("news_analyst", "WDAY", **context)

        self.assertEqual(user_message, build_default_analysis_message("WDAY", trade_date))
        self.assertIn("2026-01-08 to 2026-03-09", user_message)
        self.assertIn("Do not ask for a date range clarification", market_prompt)
        self.assertIn("2026-03-02", news_prompt)
        self.assertIn("get_insider_transactions", news_prompt)


if __name__ == "__main__":
    unittest.main()
