import logging

from financial_analysis_agent.agents.orchestrator_agent import run_analysis

logging.basicConfig(level=logging.WARNING)


def main():
    ticker = input("Enter stock ticker (e.g. AAPL): ").strip().upper()

    try:
        results = run_analysis(ticker)
    except ValueError as exc:
        print(f"Input error: {exc}")
        return

    print("\n" + "=" * 20 + " FINAL INVESTMENT BRIEF " + "=" * 20)
    print(results["report"])

    # Show failed stages clearly, even if a report was produced.
    failed = [
        name for name, result in results.items()
        if isinstance(result, str) and result.startswith("AGENT FAILED:")
    ]

    if failed:
        print("\nWARNING: These stages failed:", ", ".join(failed))
        print("Treat the report as incomplete until these stages are rerun.")


if __name__ == "__main__":
    main()
