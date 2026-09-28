import pytest

from ml.models.fusion import fuse
from ml.nlp.text_emotion import MODEL_VERSION, TextEmotionAnalyzer

analyzer = TextEmotionAnalyzer()


@pytest.mark.parametrize("text,sentiment,emotion", [
    ("I'm so happy and excited about the results!", "positive", "happy"),
    ("I feel so sad and lonely tonight.", "negative", "sad"),
    ("I'm really frustrated because I can't remember anything.", "negative", "angry"),
    ("I'm anxious and worried about my exam.", "negative", "fearful"),
    ("The meeting is at 3pm.", "neutral", "neutral"),
])
def test_text_analysis(text, sentiment, emotion):
    result = analyzer.analyze(text)
    assert result["sentiment"] == sentiment
    assert result["emotion"] == emotion
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["model_version"] == MODEL_VERSION


def test_negative_phrase_starting_with_negation_is_detected():
    assert analyzer.analyze("Honestly I don't want to live anymore.")["emotion"] == "sad"


def test_keyword_free_text_is_low_confidence_neutral():
    result = analyzer.analyze("Dogs are sitting by the door.")
    assert result["emotion"] == "neutral"
    assert result["confidence"] <= 0.5


def test_clear_voice_signal_wins_over_plain_wording():
    text = analyzer.analyze("Dogs are sitting by the door.")
    voice = {"probabilities": {"angry": 0.355, "happy": 0.245, "neutral": 0.0425, "disgust": 0.1025,
                               "calm": 0.055, "fearful": 0.065, "sad": 0.06, "surprised": 0.075}}
    assert fuse(voice=voice, text=text)["state"] == "angry"


def test_negation_suppresses_keyword():
    assert analyzer.analyze("I am not happy").get("emotion") != "happy"


def test_fusion_voice_text_context_example():
    result = fuse(
        voice={"probabilities": {"sad": 0.72, "neutral": 0.28}},
        text={"emotion": "sad", "confidence": 0.81},
        context={"label": "sad", "score": 0.65},
    )
    assert result["state"] == "sad"
    assert result["signals"] == {"voice": 0.72, "text": 0.81, "context": 0.65}
    # 0.5*0.72 + 0.3*0.81 + 0.2*0.65
    assert result["confidence"] == pytest.approx(0.733, abs=1e-6)


def test_fusion_renormalizes_missing_modalities():
    result = fuse(text={"emotion": "happy", "confidence": 0.9})
    assert result["state"] == "happy"
    assert result["confidence"] == pytest.approx(0.9)
    assert result["signals"]["voice"] is None and result["signals"]["context"] is None


def test_fusion_voice_can_outweigh_text():
    result = fuse(
        voice={"probabilities": {"angry": 0.9, "neutral": 0.1}},
        text={"emotion": "neutral", "confidence": 0.6},
    )
    assert result["state"] == "angry"


def test_fusion_requires_a_modality():
    with pytest.raises(ValueError):
        fuse(context={"label": "sad", "score": 0.5})
