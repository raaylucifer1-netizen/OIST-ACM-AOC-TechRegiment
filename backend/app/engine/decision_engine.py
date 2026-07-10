"""Decision Engine — post-processes LLM responses to extract structured data."""

import re
import json


def calculate_temperature(profile: dict) -> float:
    """Calculate LLM temperature based on persona personality.
    
    Higher openness and neuroticism → more creative/variable responses.
    Higher conscientiousness → more predictable/structured responses.
    """
    base = 0.5
    openness_mod = (profile.get("openness", 50) - 50) * 0.004
    neuroticism_mod = (profile.get("neuroticism", 50) - 50) * 0.002
    conscientiousness_mod = (50 - profile.get("conscientiousness", 50)) * 0.003
    impulse_mod = (profile.get("impulse_buying", 50) - 50) * 0.001

    temp = base + openness_mod + neuroticism_mod + conscientiousness_mod + impulse_mod
    return max(0.1, min(1.0, temp))  # Clamp between 0.1 and 1.0


def extract_sentiment(response: str) -> float:
    """Extract sentiment from response text. Returns -1.0 to 1.0."""
    # Simple keyword-based sentiment (fast, no external deps)
    positive_words = {
        "love", "great", "excellent", "amazing", "wonderful", "fantastic", "happy",
        "excited", "definitely", "absolutely", "yes", "buy", "recommend", "support",
        "trust", "prefer", "enjoy", "good", "nice", "awesome", "perfect", "best",
        "sure", "agree", "positive", "helpful", "valuable", "worth", "impressed",
    }
    negative_words = {
        "hate", "terrible", "awful", "bad", "worst", "never", "no", "refuse",
        "disagree", "oppose", "avoid", "expensive", "overpriced", "scam", "waste",
        "disappointed", "frustrated", "angry", "worried", "concerned", "skeptical",
        "doubt", "distrust", "fear", "annoyed", "boring", "useless", "poor",
    }

    words = set(re.findall(r'\b\w+\b', response.lower()))
    pos_count = len(words & positive_words)
    neg_count = len(words & negative_words)

    total = pos_count + neg_count
    if total == 0:
        return 0.0

    sentiment = (pos_count - neg_count) / total
    return max(-1.0, min(1.0, sentiment))


def extract_decision(response: str) -> str:
    """Extract a decision keyword from the response."""
    response_lower = response.lower()

    # Look for explicit decision markers
    decision_patterns = [
        (r'\b(yes|definitely|absolutely|i would|i\'d buy|support|prefer option.?a)\b', "yes"),
        (r'\b(no|never|refuse|oppose|i wouldn\'t|not interested|would not)\b', "no"),
        (r'\b(maybe|perhaps|might|consider|it depends|not sure|neutral)\b', "maybe"),
        (r'\b(stay|continue|keep)\b', "stay"),
        (r'\b(leave|switch|stop|quit)\b', "leave"),
        (r'\bpersuaded\b', "persuaded"),
        (r'\bnot.?persuaded\b', "not_persuaded"),
        (r'\boption.?a\b', "option_a"),
        (r'\boption.?b\b', "option_b"),
    ]

    for pattern, decision in decision_patterns:
        if re.search(pattern, response_lower):
            return decision

    return "neutral"


def extract_confidence(response: str, profile: dict) -> float:
    """Extract response confidence based on language certainty and persona confidence score."""
    # High-confidence language markers
    confident_markers = ["definitely", "absolutely", "certainly", "sure", "clearly", "obviously", "without doubt"]
    uncertain_markers = ["maybe", "perhaps", "not sure", "might", "could be", "i think", "possibly", "i guess"]

    response_lower = response.lower()
    confident_count = sum(1 for m in confident_markers if m in response_lower)
    uncertain_count = sum(1 for m in uncertain_markers if m in response_lower)

    # Language-based confidence
    if confident_count + uncertain_count == 0:
        language_confidence = 0.5
    else:
        language_confidence = confident_count / (confident_count + uncertain_count)

    # Blend with persona's base confidence score
    persona_confidence = profile.get("confidence", 50) / 100
    blended = (language_confidence * 0.6) + (persona_confidence * 0.4)

    return round(max(0.0, min(1.0, blended)), 2)


def process_response(response: str, profile: dict) -> dict:
    """Process an LLM response and extract structured metadata."""
    return {
        "sentiment": extract_sentiment(response),
        "decision": extract_decision(response),
        "confidence": extract_confidence(response, profile),
    }
