import yaml
import pandas as pd
from datetime import datetime
from pathlib import Path
from modules import crawler, parser, sentiment, analyzer

# 1️⃣ 설정 로드
BASE_DIR = Path(__file__).resolve().parent
config_path = BASE_DIR / "config" / "settings.yaml"
cfg = yaml.safe_load(config_path.read_text())
cands = cfg["candidates"]
feeds = cfg["feeds"]
start = datetime.fromisoformat(cfg["period"]["start"])
end = datetime.fromisoformat(cfg["period"]["end"])

print(f"[run] Candidates: {cands}")
print(f"[run] Period: {start.date()} ~ {end.date()}")
print(f"[run] Feeds: {len(feeds)} sources")

# 2️⃣ 뉴스 크롤링
df = crawler.crawl_feeds(cands, start, end, feeds)

# 3️⃣ 종목 추출
df["tickers"] = df["title"].apply(parser.extract_tickers)

# 4️⃣ 감성 분석
df = sentiment.analyze_sentiment(df)

# 5️⃣ 요약
summary = analyzer.summarize_sentiment(df)

# 6️⃣ 저장
raw_path = BASE_DIR / "data" / "raw_articles.csv"
summary_path = BASE_DIR / "data" / "summary.csv"
df.to_csv(raw_path, index=False)
summary.to_csv(summary_path, index=False)

print("\n✅ Analysis complete! Results saved to data/summary.csv")
print(summary)
