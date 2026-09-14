MATERIAL_KEYWORDS = [
    "material weakness",
    "going concern",
    "restatement",
    "sec investigation",
    "subpoena",
    "resigned",
    "delisting",
    "substantial doubt",
    "impairment",
    "covenant",
]

def score_change(text, similarity_score):
    score = 0
    for keyword in MATERIAL_KEYWORDS:
        if keyword in text.lower():
            score += 10
    score += 100 - similarity_score
    return score

def score_added_or_deleted(text):
    # added/deleted sentences have no counterpart in the other filing, so
    # there's no similarity score to compute magnitude from. Treat them as
    # maximally changed (similarity 0) rather than leaving them unscored.
    return score_change(text, 0)

# Modified sentences are similarity 70-94, so magnitude alone caps at 30.
# On the AAPL 2024 vs 2025 fixture the highest-scoring modified sentence
# (one keyword hit, lowest similarity in range) came out to 29.45. Added
# and deleted sentences, scored via score_added_or_deleted above, floor at
# 100. That's a wide, real gap: 30 sits at the very edge of what a modified
# sentence can reach, so 30 stays technically reachable but practically
# never crosses on rewordings. 50 sits comfortably inside the gap, well
# clear of even a modified sentence with a keyword hit or two (29.45 + 20 =
# 49.45), while still well under the added/deleted floor of 100.
POST_THRESHOLD = 50

def is_material(score):
    return score >= POST_THRESHOLD

if __name__ == "__main__":
    boring = "The Company's results of operations and financial condition."
    serious = "The Company has substantial doubt about its ability to continue as a going concern."

    print("Boring:", score_change(boring, 94))
    print("Serious:", score_change(serious, 71))