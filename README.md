# Redline

Public companies quietly change the language in their SEC filings all the time. A risk factor gets deleted, a sentence gets softened, an assurance disappears. Almost nobody catches it because nobody re-reads a 300 page 10-K line by line. This system does.

Redline pulls filings directly from SEC EDGAR, cleans the raw text, and compares a filing against its prior year version sentence by sentence. Each sentence is classified as unchanged, modified, added, or deleted, and every modified sentence gets a word level diff showing exactly what language changed.

The pipeline is fully deterministic. No LLMs anywhere in it. The same filing produces the same output every time, and every result traces back to a specific SEC accession number.

## How it works

EDGAR ingestion via edgartools, pulling filings by ticker and form type.

Normalization strips the junk that breaks text comparison: repeated page headers, soft hyphens, non breaking spaces, smart quotes, collapsed whitespace. Financial filings are formatted for print, not for parsing, and this layer decides the quality of everything downstream.

Sentence segmentation with pysbd rather than splitting on periods, because "U.S." and "Inc." are not sentence endings.

Alignment with rapidfuzz. Each sentence from the older filing is matched against every sentence in the newer one to find its best match, scored 0 to 100. Above 95 is unchanged, 70 to 94 is modified, below 70 means the sentence was deleted. A second pass runs the comparison in reverse to catch sentences that exist only in the new filing, which are additions.

Position based comparison does not work here. One deleted sentence shifts every sentence after it, so index to index matching breaks immediately. Fuzzy matching against the full list solves that.

Word level diffing with difflib inside every modified pair, producing the exact tokens that changed for red and green rendering.

## Stack

Python, edgartools, pysbd, rapidfuzz, difflib, pytest

## Status

Built: EDGAR ingestion, normalization, sentence segmentation, sentence alignment and classification, word level diffing, materiality scoring for all four change types (unchanged, modified, added, deleted), Item 1A extraction with a fallback chain (edgartools object attribute, then regex, then flag for manual review), a Supabase schema and client for storing filing metadata and changed sentences only, and a `run_poll.py` orchestrator wired to the ten-ticker watchlist and a GitHub Actions cron job on the free tier. Verified against Apple's 2024 and 2025 10-K filings, plus fixture-backed tests for 10-K/A amendments superseding the original, 10-Q risk factors incorporated by reference, IPO-year companies with no prior filing, and 20-F foreign private issuers.

Not yet run end to end against live EDGAR data for the full watchlist — `run_poll.py` has not been exercised outside of fixtures and unit tests, and no Supabase project has been provisioned or verified against yet.

Not built: card rendering, automated posting (Discord/X). Explicitly out of scope for now.
