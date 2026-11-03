
import json
from datetime import datetime, timezone

import yfinance as yf
from strands import tool

from financial_analysis_agent.tools.cache import get_or_fetch


def normalize_article(item):
    """Normalize Yahoo Finance news into a consistent format."""

    content = item.get("content", item)

    title = content.get("title")
    if not title:
        return None

    publisher = (
        content.get("publisher")
        or content.get("provider")
    )

    if isinstance(publisher, dict):
        publisher = publisher.get("displayName")

    published = (
        content.get("pubDate")
        or content.get("displayTime")
    )

    if not published:
        timestamp = (
            content.get("providerPublishTime")
            or item.get("providerPublishTime")
        )
        if timestamp:
            published = datetime.fromtimestamp(
                timestamp,
                tz=timezone.utc,
            ).isoformat()

    canonical = (
        content.get("canonicalUrl")
        or content.get("clickThroughUrl")
        or {}
    )

    if isinstance(canonical, dict):
        url = canonical.get("url")
    else:
        url = canonical

    # yfinance's search results carry the URL in a plain "link" field.
    url = url or content.get("link") or item.get("link")

    return {
        "title": title,
        "publisher": publisher,
        "published_at": published,
        "url": url,
    }


@tool
def search_recent_news(ticker: str) -> str:
    """
    Retrieve recent company headlines using Yahoo Finance Search.
    Returns up to 10 articles with publisher, date, and URL.
    """

    ticker = ticker.strip().upper()

    if not ticker:
        return json.dumps({"error": "Ticker cannot be empty"})

    cache_key = f"news:{ticker}:recent"

    def fetch_news():
        search = yf.Search(
            ticker,
            news_count=10,
            max_results=1,
            enable_fuzzy_query=False,
        )

        raw_news = search.news or []
        articles = []

        for item in raw_news:
            article = normalize_article(item)

            if article:
                articles.append(article)

        return json.dumps({
            "ticker": ticker,
            "source": "Yahoo Finance Search via yfinance",
            "article_count": len(articles),
            "articles": articles,
            "message": (
                "No articles returned by Yahoo Finance Search."
                if not articles
                else "News retrieved successfully."
            ),
        })

    try:
        return get_or_fetch(
            key=cache_key,
            fetch_function=fetch_news,
            ttl_seconds=300,
        )

    except Exception as exc:
        return json.dumps({
            "ticker": ticker,
            "error": (
                f"{type(exc).__name__}: {exc}"
            ),
        })


@tool
def analyze_sentiment(text: str) -> str:
    """
    Classify text using a simple keyword-based sentiment baseline.
    """

    if not text or not text.strip():
        return json.dumps({"error": "Text cannot be empty"})

    words = set(text.lower().split())

    positive_words = {
        "beat", "beats", "growth", "grew", "profit",
        "profits", "surge", "surged", "gain", "gains",
        "upgrade", "upgraded", "strong", "record",
        "bullish", "outperform", "positive", "raised",
        "exceeded", "improved",
    }

    negative_words = {
        "miss", "misses", "decline", "declined", "loss",
        "losses", "plunge", "plunged", "drop", "dropped",
        "downgrade", "downgraded", "weak", "lawsuit",
        "investigation", "bearish", "negative", "warning",
        "disappointing", "falls", "fell", "cut", "cuts",
    }

    positive_score = len(words & positive_words)
    negative_score = len(words & negative_words)

    if positive_score > negative_score:
        sentiment = "positive"
    elif negative_score > positive_score:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return json.dumps({
        "sentiment": sentiment,
        "positive_keyword_matches": positive_score,
        "negative_keyword_matches": negative_score,
        "method": "keyword-based baseline",
        "warning": (
            "This is a prototype. It does not reliably understand "
            "negation, context, or financial nuance."
        ),
    })
