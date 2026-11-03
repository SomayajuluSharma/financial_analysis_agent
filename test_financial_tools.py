
import json

from financial_analysis_agent.tools.financial_tools import (
    get_income_statement,
    get_balance_sheet,
    get_cash_flow_statement,
    compute_key_ratios,
)


def main():
    tools_to_test = [
        ("INCOME STATEMENT", get_income_statement),
        ("BALANCE SHEET", get_balance_sheet),
        ("CASH FLOW STATEMENT", get_cash_flow_statement),
        ("KEY RATIOS", compute_key_ratios),
    ]

    for name, function in tools_to_test:
        print(f"\n{'=' * 15} {name} {'=' * 15}")

        result = json.loads(function("AAPL"))

        if "error" in result:
            print("Error:", result["error"])
        else:
            print(json.dumps(result, indent=2))

    print("\nTool testing completed.")


if __name__ == "__main__":
    main()
