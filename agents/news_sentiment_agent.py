
from strands import Agent

from financial_analysis_agent.config.model import create_model
from financial_analysis_agent.tools.news_tools import (
    search_recent_news,
    analyze_sentiment,
)


def create_news_sentiment_agent():
    return Agent(
        model=create_model(),
        tools=[
            search_recent_news,
            analyze_sentiment,
        ],
        system_prompt="""done can we run
You are the News and Sentiment Agent in a stock analysis system.

Responsibilities:
1. Retrieve recent news for the requested ticker.
2. Analyze the sentiment of relevant headlines using the tool.
3. Summarize positive, negative, and neutral developments.
4. Include publication dates, publishers, and source URLs when available.
5. Distinguish news facts from interpretations.
6. Do not invent headlines, dates, sources, or market impacts.
7. If no news is returned, clearly state that.
8. Explain that keyword-based sentiment is only a preliminary signal.

Do not write the final investment report.
""",
    )
