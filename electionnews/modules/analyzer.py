import pandas as pd

def summarize_sentiment(df):
    """후보자별 종목 언급 빈도 요약"""
    summary_rows = []

    for cand in df["candidate"].unique():
        sub = df[df["candidate"] == cand]
        exploded = sub.explode("tickers").dropna(subset=["tickers"])

        pos_counts = exploded[exploded["sentiment"]=="positive"]["tickers"].value_counts().head(5)
        neg_counts = exploded[exploded["sentiment"]=="negative"]["tickers"].value_counts().head(5)

        pos_dict = pos_counts.to_dict()
        neg_dict = neg_counts.to_dict()

        pos_str = ", ".join([f"{k} ({v})" for k,v in pos_dict.items()])
        neg_str = ", ".join([f"{k} ({v})" for k,v in neg_dict.items()])

        summary_rows.append({
            "candidate": cand,
            "positive_top5": pos_str,
            "negative_bottom5": neg_str,
            "total_positive_mentions": int(pos_counts.sum()),
            "total_negative_mentions": int(neg_counts.sum())
        })

    summary = pd.DataFrame(summary_rows)
    print("[analyzer] Summary table created.")
    return summary
