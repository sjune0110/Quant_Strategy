import yaml
import pandas as pd
import re
from pathlib import Path
from modules import crawler, parser
from datetime import datetime, timedelta

# 1️⃣ 설정 로드
BASE_DIR = Path(__file__).resolve().parent
config_path = BASE_DIR / "config" / "settings.yaml"
cfg = yaml.safe_load(config_path.read_text())
cands = cfg["candidates"]

print(f"[run] Candidates: {cands}")
print(f"[run] Mode: gdelt_docapi_keywords")

dcfg = cfg["doc_api"]
domains = dcfg.get("domain_whitelist", [])
maxrecords = dcfg.get("maxrecords", 75)
timespan = dcfg.get("timespan", "1d")
source_lang = dcfg.get("source_lang")
source_country = dcfg.get("source_country")
date_range = dcfg.get("date_range")
keywords = dcfg.get("keywords", [])

startdt = None
enddt = None
start_date_obj = None
end_date_obj = None
if date_range:
    # expected format: "01-Sep-2024 - 03-Nov-2024"
    try:
        if " - " in date_range:
            start_str, end_str = [s.strip() for s in date_range.split(" - ", 1)]
        else:
            start_str, end_str = [s.strip() for s in date_range.split("-", 1)]
        start_date_obj = datetime.strptime(start_str, "%d-%b-%Y")
        end_date_obj = datetime.strptime(end_str, "%d-%b-%Y")
        startdt = start_date_obj.strftime("%Y%m%d000000")
        enddt = (end_date_obj + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)).strftime("%Y%m%d%H%M%S")
        timespan = None  # ignore timespan when explicit date range is provided
    except Exception as exc:
        print(f"[run] Failed to parse date_range {date_range!r}: {exc}")

dfs = []
if start_date_obj and end_date_obj:
    days = (end_date_obj - start_date_obj).days
    for i in range(days + 1):
        day = start_date_obj + timedelta(days=i)
        day_start = day.strftime("%Y%m%d000000")
        day_end = (day + timedelta(days=1) - timedelta(seconds=1)).strftime("%Y%m%d%H%M%S")
        df_day = crawler.crawl_gdelt_docapi_keywords(
            cands,
            keywords,
            domains=domains,
            maxrecords=maxrecords,
            timespan=None,
            source_lang=source_lang,
            source_country=source_country,
            startdatetime=day_start,
            enddatetime=day_end,
        )
        dfs.append(df_day)
    df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
else:
    df = crawler.crawl_gdelt_docapi_keywords(
        cands,
        keywords,
        domains=domains,
        maxrecords=maxrecords,
        timespan=timespan,
        source_lang=source_lang,
        source_country=source_country,
        startdatetime=startdt,
        enddatetime=enddt,
    )

if df.empty:
    print("[run] No articles collected; exiting.")
    raise SystemExit(0)

# 3️⃣ 본문 크롤링
df["body"] = df["link"].apply(crawler.fetch_article_text)

# 4️⃣ 후보+티커가 같은 문장에 등장하는 경우만 카운트
def _clean_sentence(sent: str) -> bool:
    if not isinstance(sent, str):
        return False
    s = sent.strip()
    if not s:
        return False
    lower = s.lower()
    # 필터: 스크립트/boilerplate 흔적
    blacklist = ["self.__next", "window.__", "push([", "{", "}"]
    if any(b in lower for b in blacklist):
        return False
    # 알파벳 비중이 너무 낮은 경우 제외
    letters = sum(ch.isalpha() for ch in s)
    if letters == 0 or letters / max(len(s), 1) < 0.3:
        return False
    return True

sent_rows = []
for _, row in df.iterrows():
    title = row.get("title", "")
    summary_txt = row.get("summary", "")
    body = row.get("body", "")
    combined = f"{title}. {summary_txt}. {body[:2000]}"
    for cand in cands:
        if cand.lower() not in combined.lower():
            continue
        tickers = parser.extract_tickers(combined)
        if not tickers:
            continue
        sent_rows.append(
            {
                "candidate": cand,
                "title": title,
                "summary": summary_txt,
                "sentence": combined[:500],
                "tickers": tickers,
                "link": row.get("link"),
                "published": row.get("published"),
            }
        )

df_sent = pd.DataFrame(sent_rows)
if df_sent.empty:
    print("[run] No candidate-ticker sentences found; exiting.")
    raise SystemExit(0)

# 5️⃣ 요약 (동시 언급 횟수 Top5)
summary_rows = []
for cand in df_sent["candidate"].unique():
    exploded = df_sent[df_sent["candidate"] == cand].explode("tickers")
    counts = exploded["tickers"].value_counts()
    top5 = counts.head(5)
    top_str = ", ".join([f"{k} ({v})" for k, v in top5.items()])
    summary_rows.append(
        {
            "candidate": cand,
            "top5_mentions": top_str,
            "total_mentions": int(counts.sum()),
        }
    )
summary = pd.DataFrame(summary_rows)

# 6️⃣ 저장
raw_path = BASE_DIR / "data" / "raw_articles.csv"
summary_path = BASE_DIR / "data" / "summary.csv"
df_sent.to_csv(raw_path, index=False)
summary.to_csv(summary_path, index=False)

print("\n✅ Analysis complete! Results saved to data/summary.csv")
print(summary)
