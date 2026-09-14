from dataclasses import dataclass

from run_poll import (
    is_incorporated_by_reference,
    is_foreign_private_issuer_only,
    collapse_and_select_two,
)


@dataclass
class FakeFiling:
    form: str
    filing_date: str
    period_of_report: str
    accession_no: str
    cik: str = "0000000000"


def load_fixture(name):
    with open(f"tests/fixtures/{name}") as f:
        return f.read()


# 10-Q incorporating risk factors by reference: detect and skip silently

def test_detects_incorporated_by_reference_boilerplate():
    text = load_fixture("mock_10q_incorporated_by_reference.txt")
    assert is_incorporated_by_reference(text)


def test_does_not_flag_a_real_risk_factors_section():
    text = load_fixture("mock_10k_full_text.txt")
    assert not is_incorporated_by_reference(text)


def test_long_sections_are_never_flagged_even_with_the_phrase():
    # a real Item 1A section can legitimately use similar phrasing once
    # inside thousands of words - length is the signal, not just the phrase
    text = "boilerplate risk factor text. " * 200 + "incorporated by reference"
    assert not is_incorporated_by_reference(text)


# Foreign private issuers (20-F): out of scope, detect and skip

def test_20f_only_company_is_detected_as_out_of_scope():
    filings = [
        FakeFiling(form="20-F", filing_date="2025-04-01", period_of_report="2024-12-31", accession_no="acc-1"),
        FakeFiling(form="20-F", filing_date="2024-04-01", period_of_report="2023-12-31", accession_no="acc-2"),
    ]
    assert is_foreign_private_issuer_only(filings)


def test_company_with_any_10k_is_not_flagged_as_20f_only():
    filings = [
        FakeFiling(form="10-K", filing_date="2025-04-01", period_of_report="2024-12-31", accession_no="acc-1"),
    ]
    assert not is_foreign_private_issuer_only(filings)


def test_empty_filing_list_is_not_flagged_as_20f_only():
    assert not is_foreign_private_issuer_only([])


# 10-K/A amended filings: supersede the original, do not treat as a new baseline

def test_10ka_supersedes_the_original_for_the_same_period():
    filings = [
        FakeFiling(form="10-K", filing_date="2025-01-15", period_of_report="2024-12-31", accession_no="original"),
        FakeFiling(form="10-K/A", filing_date="2025-03-01", period_of_report="2024-12-31", accession_no="amendment"),
        FakeFiling(form="10-K", filing_date="2024-01-15", period_of_report="2023-12-31", accession_no="prior-year"),
    ]
    selected = collapse_and_select_two(filings)
    assert len(selected) == 2
    assert selected[0].accession_no == "amendment"
    assert selected[1].accession_no == "prior-year"


def test_10ka_wins_regardless_of_list_order():
    filings = [
        FakeFiling(form="10-K/A", filing_date="2025-03-01", period_of_report="2024-12-31", accession_no="amendment"),
        FakeFiling(form="10-K", filing_date="2025-01-15", period_of_report="2024-12-31", accession_no="original"),
    ]
    selected = collapse_and_select_two(filings)
    assert len(selected) == 1
    assert selected[0].accession_no == "amendment"


def test_late_amendment_to_old_year_does_not_count_as_latest():
    filings = [
        FakeFiling(form="10-K", filing_date="2025-01-15", period_of_report="2024-12-31", accession_no="latest"),
        FakeFiling(form="10-K/A", filing_date="2024-06-01", period_of_report="2022-12-31", accession_no="late-amendment"),
        FakeFiling(form="10-K", filing_date="2024-01-15", period_of_report="2023-12-31", accession_no="prior-year"),
    ]
    selected = collapse_and_select_two(filings)
    assert [f.accession_no for f in selected] == ["latest", "prior-year"]


class NeverDownloadedFiling:
    form = "10-K"

    def __init__(self, filing_date):
        self.filing_date = filing_date

    @property
    def period_of_report(self):
        raise AssertionError("old filings should never be downloaded")


def test_old_filings_are_never_downloaded():
    # long-lived filers (MSFT) have decades of 10-Ks; only the newest few
    # should be fetched from EDGAR
    recent = [
        FakeFiling(form="10-K", filing_date=f"20{y}-01-15", period_of_report=f"20{y - 1}-12-31", accession_no=f"acc-{y}")
        for y in range(20, 26)
    ]
    old = [NeverDownloadedFiling(f"19{y}-01-15") for y in range(90, 99)]
    selected = collapse_and_select_two(old + recent)
    assert [f.accession_no for f in selected] == ["acc-25", "acc-24"]


# IPO-year company with no prior filing: caller treats this as a baseline

def test_single_filing_returns_only_one_period():
    filings = [
        FakeFiling(form="10-K", filing_date="2025-01-15", period_of_report="2024-12-31", accession_no="only-one"),
    ]
    selected = collapse_and_select_two(filings)
    assert len(selected) == 1
