import pysbd 
from rapidfuzz import fuzz 
import difflib

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




if __name__ == "__main__":
    sentences_2025 = load_and_split("tests/fixtures/aapl_10k_2025_risk_factors.txt") # calling function and applying to sentences
    sentences_2024 = load_and_split("tests/fixtures/aapl_10k_2024_risk_factors.txt")

    print("2025 sentence count:", len(sentences_2025))
    print("2024 sentence count:", len(sentences_2024))


    from rapidfuzz import process # Importing a string matching and comparison libary 

    unchanged_count = 0
    modified_count = 0 
    deleted_count = 0 

    for old_sentence in sentences_2024: # This comparing sentences in 2024 file too the 2025
        best_match = process.extractOne(old_sentence, sentences_2025, scorer=fuzz.ratio)
        matched_text, score, index = best_match

        if score >= 95: #scoring the sentences based on how much they've changed
            status = "UNCHANGED" 
            unchanged_count += 1
        elif score >= 70:
            status = "MODIFIED"
            modified_count += 1

            old_words = old_sentence.split()
            new_words = matched_text.split()
            matcher = difflib.SequenceMatcher(None, old_words, new_words)
            print(f"[MODIFIED] ({score:.1f})")
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag != "equal":
                    print(f"   {old_words[i1:i2]} -> {new_words[j1:j2]}")
        else:
            status = "DELETED"
            deleted_count += 1

    added_count = 0 

    for new_sentences in sentences_2025: # This is reverse comparing 2025 to 2024 as if a second lare of protection 
        best_match = process.extractOne(new_sentences, sentences_2024, scorer=fuzz.ratio)
        matched_text, score, index = best_match

        if score < 70:
            added_count += 1 
            print(f'[ADDED] ({score:.1f}) {new_sentences[:60]}')


    print("Unchanged:", unchanged_count)
    print("Modified:", modified_count)
    print("Deleted: ", deleted_count)
    print("Added: ", added_count)



