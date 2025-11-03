import re
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_SOURCES = [
    {
        "name": "nyse",
        "url": "https://datahub.io/core/nyse-other-listings/r/nyse-listed.csv",
        "path": DATA_DIR / "nyse-listed.csv",
    },
    {
        "name": "nasdaq",
        "url": "https://datahub.io/core/nasdaq-listings/r/nasdaq-listed.csv",
        "path": DATA_DIR / "nasdaq-listed.csv",
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
    "group", "holdings", "holding", "ag", "spa", "llc"
}


# -------------------------------
# 0️⃣ CSV 자동 업데이트
# -------------------------------
def _download_latest_csv(url: str, target: Path) -> bool:
    """지정된 URL에서 최신 CSV를 내려받아 저장. 실패 시 False."""
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
    """각 데이터 소스의 CSV가 없거나 오래된 경우 갱신."""
    now = datetime.now()
    for source in DATA_SOURCES:
        path = source["path"]
        if path.exists():
            modified = datetime.fromtimestamp(path.stat().st_mtime)
            if now - modified <= STALE_AFTER:
                continue
        _download_latest_csv(source["url"], path)


_ensure_ticker_files()


# -------------------------------
# 1️⃣ 티커와 회사명 로드 (로컬/원격 CSV 기반)
# -------------------------------
def load_ticker_mappings():
    """여러 데이터 소스에서 티커/회사명 매핑을 구성"""
    combined_tickers: set[str] = set()
    mapping: dict[str, str] = {}

    for source in DATA_SOURCES:
        path = source["path"]
        if not path.exists():
            warnings.warn(
                f"Ticker CSV not found at {path}. "
                f"Try downloading from {source['url']}.",
                RuntimeWarning,
            )
            continue

        try:
            df = pd.read_csv(path)
        except Exception as exc:
            warnings.warn(
                f"Failed to read ticker CSV {path}: {exc}",
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
        trimmed[symbol_col] = trimmed[symbol_col].astype(str).str.strip().str.upper()
        trimmed[name_col] = trimmed[name_col].astype(str).str.strip()

        combined_tickers.update(trimmed[symbol_col])

        for _, row in trimmed.iterrows():
            symbol = row[symbol_col]
            raw_name = row[name_col]
            if not raw_name:
                continue
            _register_name_aliases(mapping, symbol, raw_name)

    return combined_tickers, mapping


def _register_name_aliases(mapping: dict[str, str], symbol: str, raw_name: str) -> None:
    lower_name = raw_name.lower()
    mapping[lower_name] = symbol

    cleaned = re.sub(r"[^\w\s]", " ", lower_name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned:
        mapping.setdefault(cleaned, symbol)

    words = [w for w in cleaned.split() if w and w not in GENERIC_SUFFIXES]
    if words:
        base = " ".join(words)
        mapping.setdefault(base, symbol)
        mapping.setdefault(words[0], symbol)
        if len(words) >= 2:
            mapping.setdefault(" ".join(words[:2]), symbol)


TICKERS, NAME_TO_TICKER = load_ticker_mappings()


# -------------------------------
# 2️⃣ 종목 추출 함수
# -------------------------------
def extract_tickers(text):
    """
    헤드라인에서 티커(symbol) 또는 회사 이름을 찾아서 매핑
    ex) "Tesla rises" → TSLA
    """
    if not isinstance(text, str):
        return None

    text_lower = text.lower()
    found = set()

    # (1) 직접 티커 포함 (단어 경계 기준)
    for ticker in TICKERS:
        pattern = rf"\\b{re.escape(ticker)}\\b"
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.add(ticker)

    # (2) 회사 이름 기반 탐색
    for name, ticker in NAME_TO_TICKER.items():
        if name in text_lower:
            found.add(ticker)

    return list(found)[:3] if found else None
