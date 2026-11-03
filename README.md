# Financial Analysis Agent

A multi-agent stock research system built with the [Strands Agents SDK](https://strandsagents.com). Give it a ticker and it produces a fundamental-analysis brief.

The LLM is `openai/gpt-oss-120b` on Groq. Market data comes from Yahoo Finance (`yfinance`), cached in Redis.

## How it works

```
                 ┌─ financial_data_agent  (statements, ratios) ─┐
 ticker ─ Phase 1 ─ news_sentiment_agent (news, sentiment)       ├─ in parallel
                 └─ risk_agent            (liquidity, leverage) ─┘
                              │
                     Phase 2: valuation_agent (DCF, multiples)
                              │
                     Phase 3: report_writer_agent ─► investment brief
```

- `run_analysis()` runs the three phases in a fixed order (phase 1 in parallel threads).
- `create_orchestrator_agent()` is the alternative: an orchestrator that calls the specialists as tools.
- If one agent fails, the run continues. The failure is printed and the report is marked incomplete.

## Setup

Requires Python 3.10+ and a Redis server.

```bash
git clone <your-repo-url> financial_analysis_agent
cd financial_analysis_agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Put your Groq key after `GROQ_API_KEY=` in `.env` (free key: https://console.groq.com/keys), and save the file.

Start Redis (macOS: `brew install redis && brew services start redis`) and check it:

```bash
redis-cli ping        # should print PONG
```

## Run

The code imports `financial_analysis_agent.…`, so run it from the **parent** folder of the project:

```bash
cd ..
python -m financial_analysis_agent.main
```

Enter a ticker (for example `AAPL`). It takes a few minutes. A good run ends with `FINAL INVESTMENT BRIEF` and no `These stages failed` warning.

Test the tools alone, without calling the model:

```bash
python -m financial_analysis_agent.test_cache
python -m financial_analysis_agent.test_financial_tools
python -m financial_analysis_agent.test_news_tools
python -m financial_analysis_agent.test_risk_tools
```

## Layout

| Path | What it is |
|---|---|
| `main.py` | Command-line entry point |
| `agents/` | The five specialist agents and the orchestrator |
| `tools/financial_tools.py` | Income statement, balance sheet, cash flow, key ratios |
| `tools/valuation_tools.py` | Simplified DCF model and the company's own multiples |
| `tools/news_tools.py` | Recent news and a keyword sentiment baseline |
| `tools/risk_tools.py` | Rule-based risk assessment |
| `tools/cache.py` | Redis cache with a 5-minute TTL |
| `config/model.py` | The shared Groq model |

## Limits

- Not investment advice. The DCF is simplified and depends on assumed growth and discount rates.
- Sentiment is keyword-based, not a trained model.
- Peer comparison is not done: only the company's own multiples are shown.
- The model does some arithmetic itself, so numbers in the report can differ between runs.
- Groq's free tier is rate-limited (about 8k tokens per minute); the run retries automatically.
