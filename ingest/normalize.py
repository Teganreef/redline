import re 

def clean_section(text):
    text = text.replace("\xad","") #cleaning soft hypen chracter in document
    text = text.replace("\xa0"," ") #cleaning non breaking space in document 

    text = text.replace("\u201c",'"') #replacing the symbol characters in documents wiht actual symbols 
    text = text.replace("\u201d",'"')
    text = text.replace("\u2018","'")
    text = text.replace("\u2019","'")

    text = re.sub(r"Apple Inc\. \| \d{4} Form 10-K \| \d+", "", text) # taking regex module and removing repeating phrase 
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



    