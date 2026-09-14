# Knowledge Dataset

Synthetic knowledge index dataset for the Solution Intelligence Engine. Contains 70 entries across 4 source types: `ticket`, `sap_note`, `sharepoint_doc`, `kb_article`. Each entry includes metadata for duplicate detection, quality filtering, and retrieval scoring.

## Source Types

- `ticket` — Support tickets (TIC-XXX)
- `sap_note` — SAP notes (KERNEL-XXX)
- `sharepoint_doc` — SharePoint documents (SP-XXX)
- `kb_article` — Knowledge base articles (KB-XXX)

## Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier per entry |
| `source_type` | string | Type of source (ticket/sap_note/sharepoint_doc/kb_article) |
| `title` | string | Short title describing the issue |
| `description` | string | Detailed problem description |
| `resolution` | string | Resolution/fix applied |
| `status` | string | Current status (Resolved/In Progress/Closed/etc.) |
| `category` | string | Problem category/domain |
| `access_level` | string | `standard` or `restricted` (security checks) |
| `date` | string | ISO date when entry was created |
| `duplicate_group` | string \| null | Group ID for duplicates/exact matches |
| `similarity_tier` | string | `exact_duplicate`, `near_duplicate`, or `unique` |
| `quality_flag` | string | `good`, `junk`, or `restricted` (filtering) |
| `deprecated_reference` | boolean | True if tied to retired systems |
| `worked_count` | array | `[times_worked, times_attempted]` for confidence scoring |

## Duplicate Detection

- **exact duplicate**: `duplicate_group` set, high similarity → linked as recurrence
- **near duplicate**: similar content but different details → flagged for merge
- **unique**: no duplicates → passes through completely

## Quality Filtering

Entries marked:
- **`good`** or **`restricted`** → kept in index
- **`junk`** → auto-rejected by ingestion pipeline

## Usage Notes

- `demo_tag` field is internal-only, for build/demo planning only
- `duplicate_group` identifies entries meant to be related (e.g., same issue, different sources)
- All 4 source types are simulated for the initial dataset