from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class SentimentAnalyzer:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    def analyze(self, text: str) -> dict:
        if not text:
            return {
                "compound": 0.0,
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 0.0,
            }

        scores = self.analyzer.polarity_scores(text)
        return {
            "compound": round(scores["compound"], 4),
            "positive": round(scores["pos"], 4),
            "negative": round(scores["neg"], 4),
            "neutral": round(scores["neu"], 4),
        }

    def analyze_article(self, title: str, summary: str = "") -> dict:
        full_text = f"{title}. {summary}" if summary else title
        return self.analyze(full_text)

    def get_sentiment_label(self, compound: float) -> str:
        if compound >= 0.05:
            return "positive"
        elif compound <= -0.05:
            return "negative"
        return "neutral"
