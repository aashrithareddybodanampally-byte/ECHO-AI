"""
Text sentiment and emotion analysis.

Sentiment: VADER compound score (>= 0.05 positive, <= -0.05 negative).
Emotion:   transparent keyword lexicon with simple negation handling, using
           the same label vocabulary as the voice model so fusion can combine them.

This is a heuristic baseline, not a trained or calibrated model. Its
confidence values are rule-derived and must not be read as probabilities
of a psychological state.
"""

import re

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

MODEL_VERSION = "vader-lexicon-v1"

EMOTION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "happy": ("happy", "glad", "great", "excited", "joy", "love", "wonderful", "awesome",
              "proud", "grateful", "relieved", "delighted", "fantastic", "good news"),
    "sad": ("sad", "down", "unhappy", "depressed", "lonely", "cry", "crying", "hopeless",
            "miserable", "heartbroken", "empty", "tired", "exhausted", "lost",
            "want to die", "don't want to live", "no reason to live", "worthless"),
    "angry": ("angry", "mad", "furious", "annoyed", "frustrated", "frustrating", "irritated",
              "hate", "rage", "fed up", "pissed"),
    "fearful": ("scared", "afraid", "anxious", "worried", "nervous", "panic", "stress",
                "stressed", "overwhelmed", "terrified", "fear", "can't handle"),
    "disgust": ("disgusted", "disgusting", "gross", "sick of", "revolting"),
    "surprised": ("surprised", "shocked", "unexpected", "wow", "can't believe", "amazed"),
    "calm": ("calm", "relaxed", "peaceful", "fine", "okay", "content", "at ease"),
}

_NEGATIONS = {"not", "no", "never", "isn't", "wasn't", "don't", "didn't", "doesn't",
              "aren't", "can't", "cannot", "won't", "nothing", "hardly"}


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z']+", text.lower())


def _count_hits(text: str) -> dict[str, int]:
    lowered = " " + " ".join(_tokens(text)) + " "
    tokens = lowered.split()
    hits: dict[str, int] = {}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        count = 0
        for keyword in keywords:
            kw_tokens = keyword.split()
            n = len(kw_tokens)
            for i in range(len(tokens) - n + 1):
                if tokens[i:i + n] != kw_tokens:
                    continue
                window = tokens[max(0, i - 3):i]
                # Phrases that start with a negation ("can't handle", "don't want to live")
                # are themselves the signal; don't treat that word as negating them.
                if kw_tokens[0] in _NEGATIONS or not _NEGATIONS.intersection(window):
                    count += 1
        if count:
            hits[emotion] = count
    return hits


class TextEmotionAnalyzer:
    def __init__(self):
        self._vader = SentimentIntensityAnalyzer()

    def analyze(self, text: str) -> dict:
        compound = self._vader.polarity_scores(text)["compound"]
        if compound >= 0.05:
            sentiment = "positive"
        elif compound <= -0.05:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        hits = _count_hits(text)
        if hits:
            # Ties are broken by lexicon order (dict order above).
            emotion = max(hits, key=lambda e: hits[e])
            confidence = min(0.95, 0.55 + 0.1 * (hits[emotion] - 1) + 0.3 * abs(compound))
        else:
            # No emotional keywords is weak evidence: keep "neutral" at or below 0.5 so
            # that, in fusion, a clear vocal signal is not overridden by plain wording.
            emotion = "neutral"
            confidence = 0.5 * (1.0 - abs(compound))
        return {
            "sentiment": sentiment,
            "emotion": emotion,
            "confidence": round(float(confidence), 4),
            "model_version": MODEL_VERSION,
            "compound": compound,
        }
