# Election News Ticker Finder

Pull election-related articles with the GDELT Doc API, find companies/tickers that show up alongside each candidate, and summarize the most co-mentioned tickers.

## Quick Start
1. Edit `config/settings.yaml`:
   - `candidates`: names/aliases to search for.
   - `doc_api.keywords`: OR-joined keywords that must appear with the candidate (e.g., `stock`, `coin`).
   - Choose one date selector:
     - `doc_api.timespan`: rolling window (`1d`, `7d`, etc.), **or**
     - `doc_api.date_range`: `DD-Mon-YYYY - DD-Mon-YYYY` (inclusive; internally split per day), **or**
     - `startdatetime` / `enddatetime` if you add them manually in the YAML (`YYYYMMDDHHMMSS`, UTC).
   - Optional filters: `domain_whitelist` (`site:domain`), `source_lang`, `source_country`, `maxrecords` (Doc API cap is 250/query).
2. Activate your venv and run:
   ```bash
   source ../pe-env-312/bin/activate  # adjust if your env path differs
   python run.py
   ```

## YAML config notes
- All runtime settings are read from `config/settings.yaml`.
- The Doc API request is built from the YAML fields under `doc_api` and the candidate list in `candidates`.
- By adjusting the time window and keywords, this can be used independently to find stocks associated with any person or topic, not just presidential elections.

## What the pipeline does
- Uses the GDELT Doc API for all article retrieval.
- Doc API call per candidate × keyword bundle using `mode=ArtList` and `query="<candidate>" AND ("k1" OR "k2")` plus optional `site:domain`, `sourcelang`, `sourcecountry`, `timespan` or `startdatetime`/`enddatetime`. If `date_range` is set, it fans out daily queries to dodge Doc API date parsing quirks.
- Fetch article bodies and strip HTML (`modules/crawler.fetch_article_text`).
- Build company aliases from NASDAQ/NYSE listings (auto-downloaded from DataHub, refreshed daily) and loose-match them in the article text (`modules/parser.extract_tickers`).
- Keep rows where a candidate and at least one ticker co-occur; ticker extraction stops at the first 3 hits to stay focused.
- Summarize top 5 mentioned tickers per candidate (counts only—no sentiment scoring in this version).
- Sentiment analysis is in progress and not part of the current output.

## Outputs
- `data/raw_articles.csv` — candidate, title/summary snippet, matched sentence, tickers, link, published time.
- `data/summary.csv` — top 5 ticker mentions per candidate with total mention counts.

Notes
- Ingestion is Doc API only (RSS/Mentions paths removed). Titles without tickers/companies are dropped before summarizing.
- Large local envs (`pe-env*`) should stay untracked; add them to `.gitignore` before committing.
