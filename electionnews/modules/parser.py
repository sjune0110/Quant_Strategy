import re
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_SOURCES = [
    {
        "name": "nasdaq",
        "url": "https://datahub.io/core/nasdaq-listings/r/nasdaq-listed.csv",
        "path": DATA_DIR / "nasdaq-listed.csv",
    },
    {
        "name": "nyse",
        "url": "https://datahub.io/core/nyse-other-listings/r/nyse-listed.csv",
        "path": DATA_DIR / "nyse-listed.csv",
    },
]
STALE_AFTER = timedelta(days=1)

SYMBOL_COLUMNS = [
    "ACT Symbol",
    "Symbol",
    "Ticker",
    "Trading Symbol",
    "NASDAQ Symbol",
    "CQS Symbol",
]
NAME_COLUMNS = ["Company Name", "Security Name", "Name", "Company"]
GENERIC_SUFFIXES = {
    "inc", "inc.", "incorporated", "corp", "corp.", "corporation",
    "co", "co.", "company", "ltd", "ltd.", "limited", "plc", "sa", "nv",
    "group", "holdings", "holding", "ag", "spa", "llc",
    "common", "stock", "shares", "class"
}


def _download_latest_csv(url: str, target: Path) -> bool:
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        target.write_bytes(response.content)
        return True
    except Exception as exc:
        warnings.warn(
            f"Failed to update ticker listings from {url}: {exc}",
            RuntimeWarning,
        )
        return False


def _ensure_ticker_files():
    now = datetime.now()
    for source in DATA_SOURCES:
        path = source["path"]
        if path.exists():
            modified = datetime.fromtimestamp(path.stat().st_mtime)
            if now - modified <= STALE_AFTER:
                continue
        _download_latest_csv(source["url"], path)


_ensure_ticker_files()


def load_company_aliases():
    company_aliases: dict[str, list[str]] = {}

    for source in DATA_SOURCES:
        path = source["path"]
        if not path.exists():
            warnings.warn(
                f"Company CSV not found at {path}. "
                f"Try downloading from {source['url']}.",
                RuntimeWarning,
            )
            continue

        try:
            df = pd.read_csv(path)
        except Exception as exc:
            warnings.warn(
                f"Failed to read CSV {path}: {exc}",
                RuntimeWarning,
            )
            continue

        symbol_col = next((col for col in SYMBOL_COLUMNS if col in df.columns), None)
        name_col = next((col for col in NAME_COLUMNS if col in df.columns), None)

        if symbol_col is None or name_col is None:
            warnings.warn(
                f"CSV file {path} missing expected columns. "
                f"Found: {list(df.columns)}",
                RuntimeWarning,
            )
            continue

        trimmed = df[[symbol_col, name_col]].dropna()
        trimmed[name_col] = trimmed[name_col].astype(str).str.strip()

        for _, row in trimmed.iterrows():
            raw_name = row[name_col]
            if not raw_name:
                continue
            symbol = row[symbol_col]
            aliases = _build_name_aliases(raw_name)
            company_aliases[symbol] = aliases

    # crypto names
    crypto = {
        "Bitcoin": ["bitcoin"],
        "Ethereum": ["ethereum", "ether"],
        "Ripple": ["ripple"],
    }
    for sym, aliases in crypto.items():
        company_aliases[sym] = aliases

    return company_aliases


def _build_name_aliases(raw_name: str) -> list[str]:
    aliases: list[str] = []
    lower = raw_name.lower()
    aliases.append(lower)

    cleaned = re.sub(r"[^\w\s]", " ", lower)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned:
        aliases.append(cleaned)

    words = [w for w in cleaned.split() if w and w not in GENERIC_SUFFIXES]
    if words:
        base = " ".join(words)
        if base:
            aliases.append(base)

    # dedupe preserve order
    seen = set()
    uniq = []
    for a in aliases:
        if a and len(a) >= 4 and a not in seen:
            uniq.append(a)
            seen.add(a)
    return uniq


COMPANY_ALIASES = load_company_aliases()
# 블랙리스트 심볼 제거
BLACKLIST = {"MTCH", "NDAQ", "ROOT", "POST", "TISI"}
for sym in list(COMPANY_ALIASES.keys()):
    if sym in BLACKLIST:
        COMPANY_ALIASES.pop(sym, None)


def extract_tickers(text: str):
    """
    회사명(alias) 포함 여부만으로 집계. 느슨한 포함 검사 사용.
    """
    if not isinstance(text, str):
        return None
    norm = _normalize(text)
    found = []
    for sym, aliases in COMPANY_ALIASES.items():
        for alias in aliases:
            if alias and re.search(rf"\b{re.escape(alias)}\b", norm):
                found.append(sym)
                break
        if len(found) >= 3:
            break
    return found if found else None


def _normalize(text: str) -> str:
    t = text.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t
