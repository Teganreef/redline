from ingest.normalize import clean_section

def test_removes_soft_hyphen():
    dirty = "wo\xadrd"
    cleaned = clean_section(dirty)
    assert "\xad" not in cleaned

def test_correct_nonbreaking_spaces():
    dirty = "word\xa0word"
    cleaned = clean_section(dirty)
    assert cleaned == "word word"