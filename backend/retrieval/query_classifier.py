# backend/retrieval/query_classifier.py

from typing import Literal


# -----------------------------
# QUERY TYPES
# -----------------------------
QueryType = Literal[
    "explanation",
    "code_search",
    "debugging",
    "usage",
    "general"
]


# -----------------------------
# RULE-BASED CLASSIFIER
# -----------------------------
def classify_query(query: str) -> QueryType:
    """
    Classify query into type
    """

    q = query.lower()

    # -------------------------
    # DEBUGGING
    # -------------------------
    debug_keywords = [
        "error", "bug", "issue", "fix", "not working",
        "exception", "traceback", "fails", "failure"
    ]
    if any(word in q for word in debug_keywords):
        return "debugging"

    # -------------------------
    # CODE SEARCH
    # -------------------------
    code_keywords = [
        "where", "find", "locate", "which file",
        "function", "class", "method"
    ]
    if any(word in q for word in code_keywords):
        return "code_search"

    # -------------------------
    # USAGE / HOW-TO
    # -------------------------
    usage_keywords = [
        "how to", "how do i", "usage", "use", "example",
        "implement", "call", "run"
    ]
    if any(word in q for word in usage_keywords):
        return "usage"

    # -------------------------
    # EXPLANATION
    # -------------------------
    explanation_keywords = [
        "what", "why", "explain", "overview", "purpose"
    ]
    if any(word in q for word in explanation_keywords):
        return "explanation"

    # -------------------------
    # DEFAULT
    # -------------------------
    return "general"


# -----------------------------
# OPTIONAL: CONFIDENCE SCORE
# -----------------------------
def classify_with_confidence(query: str):
    """
    Returns type + simple confidence score
    """

    q = query.lower()

    scores = {
        "debugging": 0,
        "code_search": 0,
        "usage": 0,
        "explanation": 0
    }

    for word in ["error", "bug", "fix"]:
        if word in q:
            scores["debugging"] += 1

    for word in ["where", "find", "function"]:
        if word in q:
            scores["code_search"] += 1

    for word in ["how", "use", "implement"]:
        if word in q:
            scores["usage"] += 1

    for word in ["what", "why", "explain"]:
        if word in q:
            scores["explanation"] += 1

    # pick max
    query_type = max(scores, key=scores.get)
    confidence = scores[query_type] / (sum(scores.values()) + 1e-5)

    return query_type, round(confidence, 2)


# -----------------------------
# TEST
# -----------------------------
if __name__ == "__main__":
    while True:
        q = input("\nEnter query: ")

        q_type = classify_query(q)
        q_type_conf, conf = classify_with_confidence(q)

        print(f"\nType: {q_type}")
        print(f"Type (with confidence): {q_type_conf} ({conf})")