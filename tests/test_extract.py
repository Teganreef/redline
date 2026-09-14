from ingest.extract import extract_item_1a


class FakeTenK:
    def __init__(self, risk_factors=None, raise_attr_error=False):
        self._risk_factors = risk_factors
        self._raise_attr_error = raise_attr_error

    @property
    def risk_factors(self):
        if self._raise_attr_error:
            raise AttributeError("no risk_factors on this object")
        return self._risk_factors


def load_fixture(name):
    with open(f"tests/fixtures/{name}") as f:
        return f.read()


def test_prefers_object_attribute_when_present():
    tenk = FakeTenK(risk_factors="Our business faces risks.")
    result = extract_item_1a(tenk_obj=tenk, full_text="irrelevant full text")
    assert result == "Our business faces risks."


def test_falls_back_to_regex_when_object_has_no_attribute():
    tenk = FakeTenK(raise_attr_error=True)
    full_text = load_fixture("mock_10k_full_text.txt")
    result = extract_item_1a(tenk_obj=tenk, full_text=full_text)
    assert "Our business is subject to a number of risks" in result
    assert "Item 1B" not in result


def test_falls_back_to_regex_when_object_attribute_is_blank():
    tenk = FakeTenK(risk_factors="   ")
    full_text = load_fixture("mock_10k_full_text.txt")
    result = extract_item_1a(tenk_obj=tenk, full_text=full_text)
    assert "supply chain could be disrupted" in result


def test_returns_none_for_manual_review_when_both_fail():
    tenk = FakeTenK(raise_attr_error=True)
    result = extract_item_1a(tenk_obj=tenk, full_text="no item 1a markers in here at all")
    assert result is None
