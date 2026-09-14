import re

def strip_repeated_lines(text, min_repeats=3):
    """
    Page headers/footers (e.g. "Apple Inc. | 2025 Form 10-K | 6") repeat
    once per page and sit on their own line - real prose sentences don't
    repeat verbatim. The page number changes on every occurrence, so lines
    are compared by a digit-normalized template ("Apple Inc. | #### Form
    ##-K | #") rather than exact text. Templating instead of matching one
    company's literal header means this works for any filer, not just Apple.
    """
    lines = text.split("\n")

    def template(line):
        return re.sub(r"\d+", "#", line.strip())

    counts = {}
    for line in lines:
        t = template(line)
        if t:
            counts[t] = counts.get(t, 0) + 1

    repeated_templates = {t for t, count in counts.items() if count >= min_repeats}
    kept = [line for line in lines if template(line) not in repeated_templates]
    return "\n".join(kept)

def clean_section(text):
    text = text.replace("\xad","") #cleaning soft hypen chracter in document
    text = text.replace("\xa0"," ") #cleaning non breaking space in document

    text = text.replace("\u201c",'"') #replacing the symbol characters in documents wiht actual symbols
    text = text.replace("\u201d",'"')
    text = text.replace("\u2018","'")
    text = text.replace("\u2019","'")

    text = strip_repeated_lines(text) # remove any line (header/footer) that repeats across pages, regardless of company
    text = re.sub(r"\s+"," ", text) # taking a regex module and grouping spacing to remove any extra spaces

    text = text.strip()

    return text # returned clean txt

if __name__ == "__main__":

    with open("tests/fixtures/aapl_10k_2025_risk_factors.txt", "r") as f: #opening file as read option and attacthing to varible 
        data = f.read()

    cleaned = clean_section(data) # using clean function to clean data 

    print("RAW", data[:300]) #raw version data
    print("CLEANED", cleaned[:300]) #cleaned version of data 

    print("Cleaned text length:", len(cleaned))
    print("Middle chunk:", cleaned[30000:30500])
    print("'Form 10-K' count:", cleaned.count("Form 10-K"))
    
    index = cleaned.find("Form 10-K")
    print("First occurrence context:", cleaned[index-100:index+100])

    second_index = cleaned.find("Form 10-K", index + 1)
    print("Second occurrence context:", cleaned[second_index-100:second_index+100])



    