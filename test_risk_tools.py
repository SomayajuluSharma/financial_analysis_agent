
import json

from financial_analysis_agent.tools.risk_tools import assess_financial_risks


def main():
    print("Testing Risk Assessment Tool...\n")

    raw_result = assess_financial_risks("AAPL")
    result = json.loads(raw_result)

    print(json.dumps(result, indent=2))

    if "error" in result:
        raise SystemExit(f"Risk assessment failed: {result['error']}")

    print("\nRisk assessment tool test passed!")


if __name__ == "__main__":
    main()
