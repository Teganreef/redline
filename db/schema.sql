-- Metadata + changed sentences only. Full filing text is never stored here;
-- it is re-fetched from EDGAR by accession number on demand.

create table if not exists filings (
    id bigint generated always as identity primary key,
    ticker text not null,
    cik text not null,
    form_type text not null,
    filing_date date not null,
    accession_number text not null unique,
    created_at timestamptz not null default now()
);

create table if not exists diffs (
    id bigint generated always as identity primary key,
    filing_id bigint not null references filings(id) on delete cascade,
    change_type text not null check (change_type in ('unchanged', 'modified', 'added', 'deleted')),
    old_sentence text,
    new_sentence text,
    similarity_score real,
    materiality_score real,
    posted boolean not null default false,
    created_at timestamptz not null default now()
);

create index if not exists idx_diffs_filing_id on diffs (filing_id);
create index if not exists idx_diffs_posted on diffs (posted);
