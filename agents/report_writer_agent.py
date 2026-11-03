
from strands import Agent

from financial_analysis_agent.config.model import create_model


def create_report_writer_agent():
    return Agent(
        name="ReportWriterAgent",
        model=create_model(),
        system_prompt="""
You are the Report Writer Agent for a stock fundamental analysis system.

Write a concise financial analysis report using only the supplied specialist results.

Required sections:
1. Executive Summary
2. Financial Performance and Key Ratios
3. Recent News and Sentiment
4. Main Financial Risks
5. Valuation and Assumptions
6. Missing Data and Limitations
7. Conclusion

Rules:
- Maximum 700 words.
- Use concise paragraphs, bullets, or compact tables.
- Preserve reported values, currencies, units, and reporting periods.
- Distinguish reported figures from model estimates.
- Explain that DCF valuation depends on assumptions.
- Do not claim peer comparisons without actual peer-group data.
- Do not invent figures, dates, news, or sources.
- Clearly disclose failed agents and missing information.
- Do not repeat the complete raw tool outputs.
- Do not provide personalized financial advice.
"""
    )
