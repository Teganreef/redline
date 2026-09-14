import os
from supabase import create_client


def get_client():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    return create_client(url, key)


def insert_filing(client, ticker, cik, form_type, filing_date, accession_number):
    """
    Upsert on accession_number so re-running the poller never creates a
    duplicate filings row. Returns the filing's id.
    """
    result = client.table("filings").upsert(
        {
            "ticker": ticker,
            "cik": str(cik),
            "form_type": form_type,
            "filing_date": str(filing_date),
            "accession_number": accession_number,
        },
        on_conflict="accession_number",
    ).execute()
    return result.data[0]["id"]


def insert_diffs(client, filing_id, rows):
    """
    Insert diff rows for a filing. A filing that already has diff rows is
    left alone, so re-running the poller never duplicates rows.
    Returns the number of rows inserted.
    """
    existing = client.table("diffs").select("id").eq("filing_id", filing_id).limit(1).execute()
    if existing.data:
        return 0

    payload = [
        {
            "filing_id": filing_id,
            "change_type": row["change_type"],
            "old_sentence": row.get("old_sentence"),
            "new_sentence": row.get("new_sentence"),
            "similarity_score": row.get("similarity_score"),
            "materiality_score": row.get("materiality_score"),
            "posted": False,
        }
        for row in rows
    ]

    if not payload:
        return 0

    client.table("diffs").insert(payload).execute()
    return len(payload)
