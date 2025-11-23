import os
from datetime import datetime

def ensure_dir(path):
    """폴더가 없으면 자동으로 생성"""
    os.makedirs(path, exist_ok=True)

def timestamp():
    """현재 시간을 문자열로 반환 (로그용)"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(msg):
    """시간 표시 포함 간단한 로그 출력"""
    print(f"[{timestamp()}] {msg}")

def save_dataframe(df, path):
    """DataFrame을 CSV로 저장하고 로그 남김"""
    ensure_dir(os.path.dirname(path))
    df.to_csv(path, index=False)
    log(f"Saved {len(df)} rows → {path}")
