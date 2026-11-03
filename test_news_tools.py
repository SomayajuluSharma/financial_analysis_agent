
import json

from financial_analysis_agent.tools.news_tools import (
    search_recent_news,
    analyze_sentiment,
)


def main():
    print("\n===== NEWS SEARCH =====")
    news = json.loads(search_recent_news("AAPL"))

    if "error" in news:
        print("News retrieval failed:", news["error"])
    else:
        print("Ticker:", news["ticker"])
        print("Articles found:", news["article_count"])

        for article in news["articles"][:5]:
            print("\nHeadline:", article["title"])
            print("Publisher:", article["publisher"])
            print("Published:", article["published_at"])
            print("URL:", article["url"])

    print("\n===== SENTIMENT TESTS =====")

    examples = [
        "Apple reports record revenue and strong growth.",
        "Apple shares plunge after disappointing earnings.",
        "Apple announces its quarterly earnings report.",
    ]

    for example in examples:
        result = json.loads(analyze_sentiment(example))
        print("\nText:", example)
        print("Result:", result)


if __name__ == "__main__":
    main()
