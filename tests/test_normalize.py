from ingest.normalize import clean_section

def test_removes_soft_hyphen():
    dirty = "wo\xadrd"
    cleaned = clean_section(dirty)
    assert "\xad" not in cleaned

def test_strips_repeated_page_header_with_changing_page_numbers():
    dirty = (
        "First risk.\nAcme Corp | 2025 Form 10-K | 4\n"
        "Second risk.\nAcme Corp | 2025 Form 10-K | 5\n"
        "Third risk.\nAcme Corp | 2025 Form 10-K | 6\n"
    )
    assert clean_section(dirty) == "First risk. Second risk. Third risk."

def test_keeps_lines_that_repeat_fewer_than_three_times():
    dirty = "Supply risk.\nSupply risk.\nDemand risk."
    assert clean_section(dirty) == "Supply risk. Supply risk. Demand risk."

def test_correct_nonbreaking_spaces():
    dirty = "word\xa0word"
    cleaned = clean_section(dirty)
    assert cleaned == "word word"