import questionary
from typing import List, Optional, Tuple, Dict

from cli.models import AnalystType

ANALYST_ORDER = [
    ("Market Analyst", AnalystType.MARKET),
    ("Social Media Analyst", AnalystType.SOCIAL),
    ("News Analyst", AnalystType.NEWS),
    ("Fundamentals Analyst", AnalystType.FUNDAMENTALS),
]


def get_ticker() -> str:
    """Prompt the user to enter a ticker symbol."""
    ticker = questionary.text(
        "Enter the ticker symbol to analyze:",
        validate=lambda x: len(x.strip()) > 0 or "Please enter a valid ticker symbol.",
        style=questionary.Style(
            [
                ("text", "fg:green"),
                ("highlighted", "noinherit"),
            ]
        ),
    ).ask()

    if not ticker:
        console.print("\n[red]No ticker symbol provided. Exiting...[/red]")
        exit(1)

    return ticker.strip().upper()


def get_analysis_date() -> str:
    """Prompt the user to enter a date in YYYY-MM-DD format."""
    import re
    from datetime import datetime

    def validate_date(date_str: str) -> bool:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return False
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    date = questionary.text(
        "Enter the analysis date (YYYY-MM-DD):",
        validate=lambda x: validate_date(x.strip())
        or "Please enter a valid date in YYYY-MM-DD format.",
        style=questionary.Style(
            [
                ("text", "fg:green"),
                ("highlighted", "noinherit"),
            ]
        ),
    ).ask()

    if not date:
        console.print("\n[red]No date provided. Exiting...[/red]")
        exit(1)

    return date.strip()


def select_analysts() -> List[AnalystType]:
    """Select analysts using an interactive checkbox."""
    choices = questionary.checkbox(
        "Select Your [Analysts Team]:",
        choices=[
            questionary.Choice(display, value=value) for display, value in ANALYST_ORDER
        ],
        instruction="\n- Press Space to select/unselect analysts\n- Press 'a' to select/unselect all\n- Press Enter when done",
        validate=lambda x: len(x) > 0 or "You must select at least one analyst.",
        style=questionary.Style(
            [
                ("checkbox-selected", "fg:green"),
                ("selected", "fg:green noinherit"),
                ("highlighted", "noinherit"),
                ("pointer", "noinherit"),
            ]
        ),
    ).ask()

    if not choices:
        console.print("\n[red]No analysts selected. Exiting...[/red]")
        exit(1)

    return choices


def select_research_depth() -> int:
    """Select research depth using an interactive selection."""

    # Define research depth options with their corresponding values
    DEPTH_OPTIONS = [
        ("Deep - Comprehensive research, in depth debate and strategy discussion", 5),
        ("Shallow - Quick research, few debate and strategy discussion rounds", 1),
    ]

    choice = questionary.select(
        "Select Your [Research Depth]:",
        choices=[
            questionary.Choice(display, value=value) for display, value in DEPTH_OPTIONS
        ],
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:yellow noinherit"),
                ("highlighted", "fg:yellow noinherit"),
                ("pointer", "fg:yellow noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        console.print("\n[red]No research depth selected. Exiting...[/red]")
        exit(1)

    return choice


def select_shallow_thinking_agent(provider) -> str:
    """Select shallow thinking llm engine using an interactive selection."""

    SHALLOW_AGENT_OPTIONS = {
        "google-gemini-cli": [
            ("Gemini 2.5 Flash (Cloud Code Assist, free OAuth)", "gemini-2.5-flash"),
            ("Gemini 2.0 Flash (Cloud Code Assist, free OAuth)", "gemini-2.0-flash"),
        ],
        "codex": [
            ("GPT-5.1 Codex Mini (Subscription OAuth)", "gpt-5.1-codex-mini"),
            ("GPT-5.1 (Subscription OAuth)", "gpt-5.1"),
        ],
        "openai": [
            ("GPT-5 Mini - Cost-optimized reasoning", "gpt-5-mini"),
            ("GPT-5 Nano - Ultra-fast, high-throughput", "gpt-5-nano"),
            ("GPT-4.1 Mini", "gpt-4.1-mini"),
        ],
        "google": [
            ("Gemini 3 Flash - Next-gen fast", "gemini-3-flash-preview"),
            ("Gemini 2.5 Flash", "gemini-2.5-flash"),
        ],
        "xai": [
            ("Grok 4 Fast Non-Reasoning", "grok-4-fast-non-reasoning"),
            ("Grok 3 Fast", "grok-3-fast"),
        ],
        "kimi": [
            ("Kimi K2 p5 - Lightweight reasoning", "k2p5"),
        ],
        "deepseek": [
            ("DeepSeek V3 - Chat model", "deepseek-chat"),
        ],
        "minimax": [
            ("MiniMax M2.5 - Premium fast model", "MiniMax-M2.5"),
            ("Kimi K2.5 - Fallback", "kimi-k2.5"),
            ("DeepSeek V3 - Fallback", "deepseek-chat"),
        ],
    }

    provider_key = provider.lower()
    options = SHALLOW_AGENT_OPTIONS.get(provider_key, [])
    if not options:
        console.print(f"\n[red]No shallow thinking models configured for provider: {provider}[/red]")
        exit(1)

    choice = questionary.select(
        "Select Your [Quick-Thinking LLM Engine]:",
        choices=[
            questionary.Choice(display, value=value)
            for display, value in options
        ],
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:magenta noinherit"),
                ("highlighted", "fg:magenta noinherit"),
                ("pointer", "fg:magenta noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        console.print(
            "\n[red]No shallow thinking llm engine selected. Exiting...[/red]"
        )
        exit(1)

    return choice


def select_deep_thinking_agent(provider) -> str:
    """Select deep thinking llm engine using an interactive selection."""

    DEEP_AGENT_OPTIONS = {
        "google-gemini-cli": [
            ("Gemini 2.5 Pro (Cloud Code Assist, free OAuth)", "gemini-2.5-pro"),
            ("Gemini 3 Pro Preview (Cloud Code Assist, free OAuth)", "gemini-3-pro-preview"),
            ("Gemini 2.5 Flash (Cloud Code Assist, free OAuth)", "gemini-2.5-flash"),
        ],
        "codex": [
            ("GPT-5.2 Codex (Subscription OAuth)", "gpt-5.2-codex"),
            ("GPT-5.2 (Subscription OAuth)", "gpt-5.2"),
            ("GPT-5.3 Codex (Subscription OAuth)", "gpt-5.3-codex"),
        ],
        "openai": [
            ("GPT-5.2 - Latest flagship", "gpt-5.2"),
            ("GPT-5 Mini - Cost-optimized reasoning", "gpt-5-mini"),
            ("GPT-4.1 - Frontier", "gpt-4.1"),
        ],
        "google": [
            ("Gemini 3 Pro - Reasoning-first", "gemini-3-pro-preview"),
            ("Gemini 3.1 Pro Preview", "gemini-3.1-pro-preview"),
            ("Gemini 2.5 Pro", "gemini-2.5-pro"),
        ],
        "xai": [
            ("Grok 4 - Flagship", "grok-4"),
            ("Grok 4 Fast", "grok-4-fast"),
            ("Grok 3 - Previous generation", "grok-3"),
        ],
        "kimi": [
            ("Kimi K2 Thinking - Reasoning-first", "kimi-k2-thinking"),
            ("Kimi K2 p5", "k2p5"),
        ],
        "deepseek": [
            ("DeepSeek R1 - Reasoning-first", "deepseek-reasoner"),
            ("DeepSeek V3 - Chat model", "deepseek-chat"),
        ],
        "minimax": [
            ("MiniMax M2.5 - Premium reasoning model", "MiniMax-M2.5"),
            ("Kimi K2.5 - Fallback", "kimi-k2.5"),
            ("DeepSeek R1 - Fallback", "deepseek-reasoner"),
        ],
    }

    provider_key = provider.lower()
    options = DEEP_AGENT_OPTIONS.get(provider_key, [])
    if not options:
        console.print(f"\n[red]No deep thinking models configured for provider: {provider}[/red]")
        exit(1)

    choice = questionary.select(
        "Select Your [Deep-Thinking LLM Engine]:",
        choices=[
            questionary.Choice(display, value=value)
            for display, value in options
        ],
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:magenta noinherit"),
                ("highlighted", "fg:magenta noinherit"),
                ("pointer", "fg:magenta noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        console.print("\n[red]No deep thinking llm engine selected. Exiting...[/red]")
        exit(1)

    return choice

def select_llm_provider() -> tuple[str, str]:
    """Select the LLM provider using interactive selection.

    Returns (provider_key, backend_url).  All providers except DeepSeek and MiniMax are
    backed by the pi-ai-server; the backend_url is informational only.
    """
    PROVIDER_OPTIONS = [
        ("Google Gemini CLI  (OAuth, Free - via pi-ai-server)", "google-gemini-cli", ""),
        ("OpenAI Codex       (OAuth, Subscription - via pi-ai-server)", "codex", ""),
        ("OpenAI             (API Key - via pi-ai-server)", "openai", ""),
        ("Google Gemini      (API Key - via pi-ai-server)", "google", ""),
        ("xAI Grok           (API Key - via pi-ai-server)", "xai", ""),
        ("Kimi               (API Key - via pi-ai-server)", "kimi", ""),
        ("DeepSeek           (API Key - direct API)", "deepseek", "https://api.deepseek.com/v1"),
        ("MiniMax            (API Key - Anthropic compatible API)", "minimax", "https://api.minimax.io/anthropic"),
    ]

    choice = questionary.select(
        "Select your LLM Provider:",
        choices=[
            questionary.Choice(display, value=(provider_key, url))
            for display, provider_key, url in PROVIDER_OPTIONS
        ],
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:magenta noinherit"),
                ("highlighted", "fg:magenta noinherit"),
                ("pointer", "fg:magenta noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        console.print("\n[red]No provider selected. Exiting...[/red]")
        exit(1)

    provider_key, url = choice
    print(f"You selected: {provider_key}")

    return provider_key, url


def ask_openai_reasoning_effort() -> str:
    """Ask for OpenAI reasoning effort level."""
    choices = [
        questionary.Choice("Medium (Default)", "medium"),
        questionary.Choice("High (More thorough)", "high"),
        questionary.Choice("Low (Faster)", "low"),
    ]
    return questionary.select(
        "Select Reasoning Effort:",
        choices=choices,
        style=questionary.Style([
            ("selected", "fg:cyan noinherit"),
            ("highlighted", "fg:cyan noinherit"),
            ("pointer", "fg:cyan noinherit"),
        ]),
    ).ask()


def ask_gemini_thinking_config() -> str | None:
    """Ask for Gemini thinking configuration.

    Returns thinking_level: "high" or "minimal".
    Client maps to appropriate API param based on model series.
    """
    return questionary.select(
        "Select Thinking Mode:",
        choices=[
            questionary.Choice("Enable Thinking (recommended)", "high"),
            questionary.Choice("Minimal/Disable Thinking", "minimal"),
        ],
        style=questionary.Style([
            ("selected", "fg:green noinherit"),
            ("highlighted", "fg:green noinherit"),
            ("pointer", "fg:green noinherit"),
        ]),
    ).ask()
