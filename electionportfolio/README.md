# Election News Sentiment Pipeline

This project collects election-related news, identifies mentioned stocks, runs FinBERT sentiment analysis, and summarizes the tickers that trend positively or negatively for each candidate.

## How It Works
- `config/settings.yaml` defines:
  - `candidates`: names to look for in article titles/summaries
  - `period`: ISO dates (start/end) used to keep articles inside the time window
  - `feeds`: RSS/Atom sources to scan (latest headlines only)
- `run.py` orchestrates the full workflow:
  1. Crawl configured feeds (`modules/crawler.py`)
  2. Extract stock tickers for each headline (`modules/parser.py`)
  3. Score sentiment with FinBERT (`modules/sentiment.py`)
  4. Summarize per-candidate positive/negative tickers (`modules/analyzer.py`)
  5. Save results to `data/raw_articles.csv` and `data/summary.csv`

## Requirements
- Python 3.9+ (project tested inside `pe-env`)
- Packages: `feedparser`, `pandas`, `requests`, `yfinance`, `transformers`, `torch`, `PyYAML`
- Network access required for:
  - RSS feeds (latest stories only; historical archives not supported)
  - Downloading ticker CSVs from DataHub (NYSE, NASDAQ) on first run
  - FinBERT model download the first time sentiment runs

## Usage
```bash
source pe-env/bin/activate
python electionnews/run.py
```

Outputs:
- `data/raw_articles.csv` — crawled articles with extracted tickers and sentiment
- `data/summary.csv` — top 5 positive and negative tickers per candidate

You can tweak candidates, time range, or feeds by editing `config/settings.yaml`. For historical news coverage, replace RSS feeds with an API or dataset that provides backdated articles.***
