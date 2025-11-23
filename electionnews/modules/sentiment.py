from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import pandas as pd

# FinBERT 로드
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
labels = ["positive", "neutral", "negative"]

@torch.no_grad()
def get_sentiment(text):
    """단일 문장의 감성 분류"""
    try:
        inputs = tokenizer(text, return_tensors="pt", truncation=True)
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        return labels[torch.argmax(probs).item()]
    except:
        return "neutral"

def analyze_sentiment(df):
    """DataFrame 전체 감성 분석"""
    sentiments = []
    for t in df["title"]:
        sentiments.append(get_sentiment(t))
    df["sentiment"] = sentiments
    print(f"[sentiment] Sentiment analysis complete. ({df['sentiment'].value_counts().to_dict()})")
    return df
