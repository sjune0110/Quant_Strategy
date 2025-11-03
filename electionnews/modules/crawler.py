import feedparser
import pandas as pd
from datetime import datetime, date


def _coerce_date(value):
    """Return date instance extracted from datetime/date inputs."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise TypeError(f"Unsupported date type: {type(value)!r}")


def crawl_feeds(candidates, start, end, feed_urls):
    """뉴스 RSS 피드에서 후보자 이름이 포함된 기사 수집"""
    start_date = _coerce_date(start)
    end_date = _coerce_date(end)
    data = []
    for url in feed_urls:
        try:
            feed = feedparser.parse(url)
            # print(f"[crawler] {url} entries={len(feed.entries)}")
            for entry in feed.entries:
                dt = None
                if hasattr(entry, "published_parsed"):
                    dt = datetime(*entry.published_parsed[:6])
                    article_date = dt.date()
                    if not (start_date <= article_date <= end_date):
                        # print(f"[crawler] skip {entry.title!r} - outside period")
                        continue

                text = (entry.title + " " + entry.get("summary", "")).lower()

                for cand in candidates:
                    if cand.lower() in text:
                        # print(f"[crawler] matched candidate {cand} in {entry.title!r}")
                        data.append({
                            "feed": url,
                            "candidate": cand,
                            "title": entry.title,
                            "summary": entry.get("summary", ""),
                            "link": entry.link,
                            "published": dt
                        })
        except Exception as e:
            print(f"[Error] Feed {url}: {e}")

    df = pd.DataFrame(data)
    print(f"[crawler] Collected {len(df)} articles.")
    return df
