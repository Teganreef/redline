from ingest.materiality import score_change, score_added_or_deleted, POST_THRESHOLD, is_material


def test_added_or_deleted_gets_full_magnitude():
    # no counterpart exists, so it should score as if similarity were 0
    text = "A brand new risk factor sentence."
    assert score_added_or_deleted(text) == score_change(text, 0)


def test_added_or_deleted_still_picks_up_keyword_bonus():
    text = "The Company received a subpoena from the SEC."
    score = score_added_or_deleted(text)
    assert score > 100  # base 100 magnitude + keyword hits


def test_threshold_sits_above_max_possible_modified_score():
    # modified sentences are similarity 70-94, so magnitude alone caps at 30.
    # even with one keyword hit that's only 40, comfortably under threshold.
    worst_case_modified_with_one_keyword = score_change(
        "we have identified a material weakness in our controls", 70
    )
    assert worst_case_modified_with_one_keyword < POST_THRESHOLD


def test_threshold_sits_below_added_deleted_floor():
    plain_new_sentence = "This is an entirely new sentence with no keywords."
    assert is_material(score_added_or_deleted(plain_new_sentence))
