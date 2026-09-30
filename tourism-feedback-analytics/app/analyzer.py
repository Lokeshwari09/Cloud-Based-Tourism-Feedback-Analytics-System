"""Lightweight rule-based sentiment + topic analyzer (no external downloads needed)."""
import re
from collections import Counter

POS = {"great": 3, "excellent": 4, "amazing": 4, "beautiful": 3, "friendly": 3, "clean": 2, "good": 2,
       "wonderful": 4, "love": 3, "loved": 3, "perfect": 4, "delicious": 3, "helpful": 3, "comfortable": 2,
       "safe": 2, "best": 3, "fantastic": 4, "enjoyed": 3, "nice": 2, "affordable": 2, "recommend": 3,
       "scenic": 3, "peaceful": 2, "worth": 2, "awesome": 4, "smooth": 2, "fresh": 2, "polite": 2}
NEG = {"bad": -2, "terrible": -4, "dirty": -3, "rude": -3, "worst": -4, "poor": -3, "expensive": -2,
       "overpriced": -3, "crowded": -2, "noisy": -2, "unsafe": -3, "delay": -2, "delayed": -2, "boring": -2,
       "disappointing": -3, "disappointed": -3, "horrible": -4, "slow": -2, "waste": -3, "scam": -4,
       "smelly": -3, "broken": -2, "awful": -4, "cold": -1, "late": -2, "cheat": -3, "unhygienic": -3}
NEGATORS = {"not", "no", "never", "hardly", "isn't", "wasn't", "don't", "didn't", "cannot", "can't"}
BOOSTERS = {"very": 1.4, "really": 1.3, "extremely": 1.6, "so": 1.2, "too": 1.2}

TOPICS = {
    "Accommodation": {"hotel", "room", "rooms", "stay", "resort", "bed", "hostel", "homestay"},
    "Food": {"food", "restaurant", "meal", "breakfast", "dinner", "lunch", "taste", "delicious", "cafe", "seafood"},
    "Transport": {"bus", "taxi", "cab", "train", "flight", "road", "traffic", "transport", "auto"},
    "Safety": {"safe", "unsafe", "security", "police", "scam", "theft"},
    "Cost": {"price", "prices", "expensive", "cheap", "overpriced", "affordable", "cost", "ticket"},
    "Cleanliness": {"clean", "dirty", "smelly", "hygiene", "unhygienic", "garbage", "washroom"},
    "Staff": {"staff", "guide", "service", "rude", "friendly", "helpful", "polite", "manager", "crew", "hosts"},
    "Attractions": {"view", "views", "beach", "temple", "hill", "falls", "waterfalls", "museum", "park", "scenic", "fort", "ruins"},
}
STOP = set("""a an the and or but if is are was were be been to of in on at for with this that it its i we you they
my our your their from as by so very really just had have has there here also than then too not no can will would
could should about into out up down over after before again more most some any all one two get got""".split())


def tokenize(text):
    return re.findall(r"[a-z']+", text.lower())


def analyze(text, rating=None):
    words = tokenize(text)
    total = 0.0
    for i, w in enumerate(words):
        val = POS.get(w, 0) or NEG.get(w, 0)
        if not val:
            continue
        window = words[max(0, i - 2):i]
        if any(x in NEGATORS for x in window):
            val = -val * 0.8
        for x in window:
            val *= BOOSTERS.get(x, 1.0)
        total += val
    score = total / (abs(total) + 4) if total else 0.0
    if rating:  # blend star rating (1-5) as a weak signal
        score = 0.7 * score + 0.3 * ((float(rating) - 3) / 2)
    label = "positive" if score >= 0.15 else "negative" if score <= -0.15 else "neutral"
    wordset = set(words)
    topics = [t for t, kw in TOPICS.items() if wordset & kw] or ["General"]
    return {"score": round(score, 3), "label": label, "topics": topics}


def top_keywords(texts, n=12):
    c = Counter(w for t in texts for w in tokenize(t) if len(w) > 3 and w not in STOP)
    return c.most_common(n)
