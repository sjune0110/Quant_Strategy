import pandas as pd
import requests
import html
import re
from datetime import datetime
from urllib.parse import urlencode


def crawl_gdelt_docapi_keywords(
    candidates,
    keywords,
    domains=None,
    maxrecords=75,
    timespan="1d",
    source_lang=None,
    source_country=None,
    startdatetime=None,
    enddatetime=None,
):
    """
    후보 × 키워드 조합으로 Doc API(ArtList)를 호출해 기사 목록 수집.
    keywords는 OR 묶음으로 포함.
    """
    domains = domains or []
    keywords = [k for k in keywords if k]
    records = []
    seen_links = set()

    for cand in candidates:
        kw_part = " OR ".join([f'"{k}"' for k in keywords]) if keywords else ""
        parts = [f'"{cand}"']
        if kw_part:
            parts.append(kw_part)  # avoid parentheses to satisfy GDELT parser
        if domains:
            parts.append(" OR ".join([f"site:{d}" for d in domains]))
        if source_country:
            parts.append(f"sourcecountry:{source_country}")
        if source_lang:
            parts.append(f"sourcelang:{source_lang}")
        query = " AND ".join(parts)

        params = {
            "query": query,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": maxrecords,
        }
        if startdatetime and enddatetime:
            params["startdatetime"] = startdatetime
            params["enddatetime"] = enddatetime
        else:
            params["timespan"] = timespan

        url = f"https://api.gdeltproject.org/api/v2/doc/doc?{urlencode(params)}"
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            print(
                f"[debug] query={query!r} "
                f"status={resp.status_code} "
                f"content-type={resp.headers.get('Content-Type')} "
                f"body_snippet={resp.text[:200]!r}"
            )
            if "json" not in resp.headers.get("Content-Type", "").lower():
                continue
            data = resp.json()
        except Exception:
            continue

        for art in data.get("articles", []):
            link = art.get("url")
            if link in seen_links:
                continue
            seen_links.add(link)
            title = art.get("title") or art.get("seendate")
            summary = art.get("excerpt") or ""
            published = _parse_docapi_datetime(art.get("seendate"))
            records.append(
                {
                    "feed": "gdelt_docapi",
                    "candidate": cand,
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "published": published,
                }
            )

    df = pd.DataFrame(records)
    print(f"[gdelt-docapi-keywords] Collected {len(df)} articles.")
    return df


def fetch_article_text(url: str) -> str:
    """Fetch article body text; strip HTML tags."""
    if not url:
        return ""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        text = resp.text
    except Exception:
        return ""

    # Drop scripts/styles/noscript
    text = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\\1>", " ", text)
    # Replace block tags with space
    text = re.sub(r"(?i)</?(p|div|br|li|ul|ol|span|h[1-6])[^>]*>", " ", text)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Remove obvious boilerplate/json blobs
    text = re.sub(r"self\\.\\w+\\s*=\\s*\\[.*?\\];?", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"window\\.\\w+\\s*=\\s*\\{.*?\\};?", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\\{[^{}]{200,}\\}", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\\s+", " ", text).strip()
    # Cap length to avoid runaway blobs
    return text[:4000]


def _parse_docapi_datetime(val):
    if not val:
        return None
    try:
        # expected format: 2024-10-01T12:34:56Z
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except Exception:
        return None
