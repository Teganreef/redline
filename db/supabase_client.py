import os
from datetime import datetime, timezone
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


def is_processed(client, accession_number):
    result = (
        client.table("filings")
        .select("processed_at")
        .eq("accession_number", accession_number)
        .limit(1)
        .execute()
    )
    return bool(result.data) and result.data[0]["processed_at"] is not None


def mark_processed(client, filing_id):
    # called last, after diffs are saved, so a run that dies halfway gets redone
    client.table("filings").update(
        {"processed_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", filing_id).execute()
