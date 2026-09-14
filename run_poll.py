"""
Orchestrator: for each ticker on the watchlist, find the two most recent
annual filings, diff their Item 1A sections, score materiality, and persist
changed sentences to Supabase. Safe to run repeatedly - idempotent on
accession number (see db/supabase_client.py).

Runs on GitHub Actions on a schedule (.github/workflows/poll.yml), so this
never assumes local state between runs.
"""
from dotenv import load_dotenv
from edgar import Company, set_identity

load_dotenv()  # picks up SUPABASE_URL / SUPABASE_KEY from a local .env; no-op if they're already set (e.g. in GitHub Actions)

from ingest.extract import extract_item_1a
from ingest.normalize import clean_section
from ingest.diff import split_sentences, classify_and_score
from db.supabase_client import get_client, insert_filing, insert_diffs, is_processed, mark_processed

WATCHLIST = ["AAPL", "MSFT", "GOOGL", "NVDA", "IONQ", "CEG", "VST", "ZS", "SOFI", "AVAV"]

ANNUAL_FORMS = ("10-K", "10-K/A")

# Boilerplate a 10-Q (or a short-form annual update) uses to point back at
# the last full risk factors disclosure instead of restating it. If we ever
# diff a section like this, the two are near-identical, so the pipeline
# would otherwise emit a misleading "no changes" result.
INCORPORATED_BY_REFERENCE_PHRASES = (
    "incorporated by reference",
    "no material changes to the risk factors",
    "no material change to the risk factors",
    "there have been no material changes",
)


def is_incorporated_by_reference(text):
    if not text:
        return False
    # Only worth checking short sections - a real Item 1A run is thousands
    # of words, boilerplate incorporation notices are a paragraph.
    if len(text) > 1000:
        return False
    lowered = " ".join(text.lower().split())
    return any(phrase in lowered for phrase in INCORPORATED_BY_REFERENCE_PHRASES)


def get_item_1a_text(filing):
    try:
        tenk_obj = filing.obj()
    except Exception:
        tenk_obj = None
    try:
        full_text = filing.text()
    except Exception:
        full_text = None
    return extract_item_1a(tenk_obj=tenk_obj, full_text=full_text)


def is_foreign_private_issuer_only(filings):
    return len(filings) > 0 and all(f.form == "20-F" for f in filings)


# Reading period_of_report downloads the whole filing from EDGAR, so only the
# newest few filings are inspected - enough for two periods plus amendments,
# without pulling decades of history for long-lived filers like MSFT.
RECENT_FILINGS_WINDOW = 6


def collapse_and_select_two(filings):
    """
    Pure helper: given a list of 10-K/10-K/A filings (any order), collapse
    each amended period onto its 10-K/A so the amendment supersedes the
    original instead of being treated as a separate, newer baseline, then
    return the two most recent periods, newest first. Periods are ranked by
    the period itself, not filing date, so a late amendment to an old year
    can't pose as the latest filing.
    """
    recent = sorted(filings, key=lambda f: f.filing_date, reverse=True)[:RECENT_FILINGS_WINDOW]

    by_period = {}
    for f in recent:
        period = f.period_of_report
        current = by_period.get(period)
        if current is None or (f.form == "10-K/A" and current.form != "10-K/A"):
            by_period[period] = f  # amendment supersedes the original

    newest_periods = sorted(by_period, reverse=True)[:2]
    return [by_period[p] for p in newest_periods]


def latest_annual_filing(filings):
    # most recently filed 10-K or 10-K/A; reads only the filing index, no download
    annual = [f for f in filings if f.form in ANNUAL_FORMS]
    if not annual:
        return None
    return max(annual, key=lambda f: f.filing_date)


def mark_seen(client, ticker, filing):
    filing_id = insert_filing(client, ticker, filing.cik, filing.form, filing.filing_date, filing.accession_no)
    mark_processed(client, filing_id)


def process_ticker(client, ticker):
    filings = Company(ticker).get_filings(form=["10-K", "10-K/A", "20-F"])

    if is_foreign_private_issuer_only(filings):
        print(f"[{ticker}] SKIP: only files 20-F (foreign private issuer), out of scope")
        return

    latest = latest_annual_filing(filings)
    if latest is None:
        print(f"[{ticker}] SKIP: no 10-K on file yet")
        return

    # Cheap check before any download: if the newest filing was already
    # handled on an earlier run, nothing new has been filed.
    if is_processed(client, latest.accession_no):
        print(f"[{ticker}] up to date ({latest.accession_no})")
        return

    selected = collapse_and_select_two([f for f in filings if f.form in ANNUAL_FORMS])

    if len(selected) < 2:
        f = selected[0]
        print(f"[{ticker}] BASELINE: no prior annual filing to diff against ({f.accession_no}), logging only")
        insert_filing(client, ticker, f.cik, f.form, f.filing_date, f.accession_no)
        mark_seen(client, ticker, latest)
        return

    newer, older = selected[0], selected[1]

    newer_text = get_item_1a_text(newer)
    older_text = get_item_1a_text(older)

    # not marked processed, so the next run retries it
    if newer_text is None:
        print(f"[{ticker}] MANUAL REVIEW: Item 1A extraction failed for {newer.accession_no}")
        return
    if older_text is None:
        print(f"[{ticker}] MANUAL REVIEW: Item 1A extraction failed for {older.accession_no}")
        return

    if is_incorporated_by_reference(newer_text) or is_incorporated_by_reference(older_text):
        print(f"[{ticker}] SKIP: risk factors incorporated by reference, nothing to diff")
        mark_seen(client, ticker, latest)
        return

    old_sentences = split_sentences(clean_section(older_text))
    new_sentences = split_sentences(clean_section(newer_text))

    rows = classify_and_score(old_sentences, new_sentences)
    changed_rows = [r for r in rows if r["change_type"] != "unchanged"]

    insert_filing(client, ticker, older.cik, older.form, older.filing_date, older.accession_no)
    newer_id = insert_filing(client, ticker, newer.cik, newer.form, newer.filing_date, newer.accession_no)

    inserted = insert_diffs(client, newer_id, changed_rows)
    mark_seen(client, ticker, latest)
    print(f"[{ticker}] {newer.accession_no}: {inserted} changed sentences persisted "
          f"(of {len(changed_rows)} found, {len(rows) - len(changed_rows)} unchanged)")


def main():
    set_identity("Tegan Dowd teganreef.d@gmail.com")
    client = get_client()

    for ticker in WATCHLIST:
        try:
            process_ticker(client, ticker)
        except Exception as e:
            print(f"[{ticker}] ERROR: {e}")


if __name__ == "__main__":
    main()
