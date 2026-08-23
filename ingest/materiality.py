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

if __name__ == "__main__":
    boring = "The Company's results of operations and financial condition."
    serious = "The Company has substantial doubt about its ability to continue as a going concern."

    print("Boring:", score_change(boring, 94))
    print("Serious:", score_change(serious, 71))