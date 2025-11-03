# Election News Sentiment Pipeline

This module searches election-related headlines for candidate mentions, detects referenced stocks, and summarizes which tickers perform well or poorly.

## Quick Start
1. Edit `config/settings.yaml` to specify:
   - `candidates`: names to match in RSS headlines/summaries.
   - `period`: ISO start/end dates to filter articles.
   - `feeds`: RSS/Atom URLs. These only provide the latest stories.
2. Activate the project's virtual environment and run:
   ```bash
   source ../pe-env/bin/activate  # adjust path if needed
   python run.py
   ```

## Pipeline Overview
- `modules/crawler.py` collects articles mentioning configured candidates.
- `modules/parser.py` maps company names/symbols to tickers (NYSE + NASDAQ lists pulled from DataHub).
- `modules/sentiment.py` loads FinBERT to classify headline sentiment.
- `modules/analyzer.py` aggregates per-candidate positive/negative ticker counts.

Outputs are saved under `data/`:
- `raw_articles.csv` — articles with tickers and sentiment labels.
- `summary.csv` — top 5 positive / negative tickers per candidate.

> Historical news is not available via RSS. For past periods, swap the feeds with an API or dataset that serves archived articles.
