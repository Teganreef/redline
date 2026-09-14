import pytest

import run_poll
from run_poll import latest_annual_filing


class IndexOnlyFiling:
    # only what EDGAR's filing index gives for free; anything that needs
    # the full filing downloaded fails the test
    def __init__(self, form, filing_date, accession_no):
        self.form = form
        self.filing_date = filing_date
        self.accession_no = accession_no
        self.cik = "0000000000"

    @property
    def period_of_report(self):
        raise AssertionError("filing was downloaded")

    def obj(self):
        raise AssertionError("filing was downloaded")

    def text(self):
        raise AssertionError("filing was downloaded")


class FakeCompany:
    def __init__(self, filings):
        self._filings = filings

    def get_filings(self, form=None):
        return self._filings


TWO_10KS = [
    IndexOnlyFiling("10-K", "2025-01-15", "k-2025"),
    IndexOnlyFiling("10-K", "2024-01-15", "k-2024"),
]


def test_latest_is_the_most_recently_filed_annual_form():
    filings = [
        IndexOnlyFiling("10-K", "2025-01-15", "k-2025"),
        IndexOnlyFiling("10-K/A", "2025-03-01", "amendment"),
        IndexOnlyFiling("20-F", "2025-06-01", "foreign"),
    ]
    assert latest_annual_filing(filings).accession_no == "amendment"


def test_no_annual_filings_returns_none():
    assert latest_annual_filing([IndexOnlyFiling("20-F", "2025-06-01", "foreign")]) is None


def test_up_to_date_ticker_downloads_nothing(monkeypatch):
    checked = []
    monkeypatch.setattr(run_poll, "Company", lambda ticker: FakeCompany(TWO_10KS))
    monkeypatch.setattr(run_poll, "is_processed", lambda client, acc: checked.append(acc) or True)

    run_poll.process_ticker(client=None, ticker="TEST")

    assert checked == ["k-2025"]


def test_new_filing_goes_on_to_download(monkeypatch):
    monkeypatch.setattr(run_poll, "Company", lambda ticker: FakeCompany(TWO_10KS))
    monkeypatch.setattr(run_poll, "is_processed", lambda client, acc: False)

    with pytest.raises(AssertionError, match="filing was downloaded"):
        run_poll.process_ticker(client=None, ticker="TEST")
