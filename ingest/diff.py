import pysbd
from rapidfuzz import fuzz, process
import difflib
from ingest.materiality import score_change, score_added_or_deleted

from ingest.normalize import clean_section # taking the clean sections into this file

def split_sentences(text):
    segmenter = pysbd.Segmenter(language="en" , clean=False) # using pysbd module to segment out the text
    sentences = segmenter.segment(text)
    return sentences

def load_and_split(filepath): #this cleans and splits setences into one clean function
    with open(filepath, "r") as f:
        raw = f.read()
    cleaned = clean_section(raw)
    sentences = split_sentences(cleaned)
    return sentences


def classify_and_score(old_sentences, new_sentences):
    """
    Same alignment/classification logic as the original script version,
    pulled into a function so run_poll.py can call it against live filings.
    Returns a list of dict rows: change_type, old_sentence, new_sentence,
    similarity_score, materiality_score.
    """
    rows = []

    for old_sentence in old_sentences: # comparing sentences in the old filing to the new one
        matched_text, score, index = process.extractOne(old_sentence, new_sentences, scorer=fuzz.ratio)

        if score >= 95: #scoring the sentences based on how much they've changed
            rows.append({
                "change_type": "unchanged",
                "old_sentence": old_sentence,
                "new_sentence": matched_text,
                "similarity_score": score,
                "materiality_score": score_change(old_sentence, score),
            })
        elif score >= 70:
            rows.append({
                "change_type": "modified",
                "old_sentence": old_sentence,
                "new_sentence": matched_text,
                "similarity_score": score,
                "materiality_score": score_change(old_sentence, score),
            })
        else:
            rows.append({
                "change_type": "deleted",
                "old_sentence": old_sentence,
                "new_sentence": None,
                "similarity_score": score,
                "materiality_score": score_added_or_deleted(old_sentence),
            })

    for new_sentence in new_sentences: # reverse pass over the new filing catches additions
        matched_text, score, index = process.extractOne(new_sentence, old_sentences, scorer=fuzz.ratio)

        if score < 70:
            rows.append({
                "change_type": "added",
                "old_sentence": None,
                "new_sentence": new_sentence,
                "similarity_score": score,
                "materiality_score": score_added_or_deleted(new_sentence),
            })

    return rows


if __name__ == "__main__":
    sentences_2025 = load_and_split("tests/fixtures/aapl_10k_2025_risk_factors.txt") # calling function and applying to sentences
    sentences_2024 = load_and_split("tests/fixtures/aapl_10k_2024_risk_factors.txt")

    print("2025 sentence count:", len(sentences_2025))
    print("2024 sentence count:", len(sentences_2024))

    rows = classify_and_score(sentences_2024, sentences_2025)

    unchanged_count = 0
    modified_count = 0
    deleted_count = 0
    added_count = 0

    for row in rows:
        if row["change_type"] == "unchanged":
            unchanged_count += 1
        elif row["change_type"] == "modified":
            modified_count += 1
            old_words = row["old_sentence"].split()
            new_words = row["new_sentence"].split()
            matcher = difflib.SequenceMatcher(None, old_words, new_words)
            print(f'[MODIFIED] (sim {row["similarity_score"]:.1f} | material {row["materiality_score"]:.0f})')
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag != "equal":
                    print(f"   {old_words[i1:i2]} -> {new_words[j1:j2]}")
        elif row["change_type"] == "deleted":
            deleted_count += 1
        elif row["change_type"] == "added":
            added_count += 1
            print(f'[ADDED] ({row["similarity_score"]:.1f} | material {row["materiality_score"]:.0f}) {row["new_sentence"][:60]}')

    print("Unchanged:", unchanged_count)
    print("Modified:", modified_count)
    print("Deleted: ", deleted_count)
    print("Added: ", added_count)



