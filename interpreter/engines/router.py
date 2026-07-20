"""Question router — pick the right engine(s) by the TYPE of question.

The chat layer classifies intent, the router maps it to engines. Timing questions
go to the daśā clock (confirmed by Jaimini chara + Tājika annual); yes/no and
quality questions go to KP. The router returns engine NAMES only — it never
interprets. (Established by blind test: KP is promise/quality, the daśā×transit
stack is the clock.)
"""

from __future__ import annotations

# intent -> ordered engines (primary first). The AI still reads every engine it
# is handed; ordering only signals which testimony leads for that question type.
_ROUTING = {
    "timing":  ["dasha_timing", "jaimini", "tajika"],   # WHEN
    "yes_no":  ["kp", "dasha_timing"],                  # WILL it / did it
    "quality": ["kp", "jaimini"],                       # HOW / will it last / afflicted
}

# keyword → intent (first match wins; order matters — timing words are checked
# before the generic yes/no "will").
_INTENT_CUES = [
    ("timing",  ("when", "date", "time", "kab", "which year", "which month",
                 "how soon", "by when")),
    ("quality", ("how good", "quality", "will it last", "happy", "afflict",
                 "kaisa", "kaisi", "successful", "long last")),
    ("yes_no",  ("will i", "will he", "will she", "will we", "did i", "did he",
                 "did she", "is there", "can i", "chance", "possible", "yes or no",
                 "hoga", "hogi", "milega", "milegi")),
]


def classify(question: str) -> str:
    """Best-effort intent from a natural-language question. Defaults to 'timing'
    (the most common ask and the one that most needs the daśā stack)."""
    q = (question or "").lower()
    for intent, cues in _INTENT_CUES:
        if any(c in q for c in cues):
            return intent
    return "timing"


def route(intent: str) -> list[str]:
    """Engine names for an intent (falls back to the timing stack)."""
    return list(_ROUTING.get(intent, _ROUTING["timing"]))
