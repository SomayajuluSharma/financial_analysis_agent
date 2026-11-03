
from financial_analysis_agent.tools.cache import (
    get_or_fetch,
    get_redis_client,
)


def main():
    client = get_redis_client()

    client.delete("test:financials:AAPL")

    calls = {"count": 0}

    def fake_fetch():
        calls["count"] += 1
        return {
            "ticker": "AAPL",
            "revenue": 416_161_000_000,
        }

    first = get_or_fetch(
        "test:financials:AAPL",
        fake_fetch,
        ttl_seconds=60,
    )

    second = get_or_fetch(
        "test:financials:AAPL",
        fake_fetch,
        ttl_seconds=60,
    )

    print("First:", first)
    print("Second:", second)
    print("Fetch calls:", calls["count"])
    print("Redis TTL:", client.ttl("test:financials:AAPL"))

    assert first == second
    assert calls["count"] == 1
    assert client.ttl("test:financials:AAPL") > 0

    client.delete("test:financials:AAPL")

    print("Redis cache test passed!")


if __name__ == "__main__":
    main()
