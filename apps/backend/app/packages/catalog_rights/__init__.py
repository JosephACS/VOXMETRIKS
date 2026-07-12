"""Catalog Rights and Contracts package — Spec 021.

Business rights-management domain: catalog assets/releases, ownership,
rights contracts (master/publishing/neighboring/other), territories,
authorized uses, conflicts, and approvals.

Kept fully distinct from:
  - dim_track / dim_album (analytics warehouse) — only optional,
    non-enforced warehouse_track_id / warehouse_album_id references.
  - app_commercial_contract (Spec 017 CRM/commercial contracting) — a
    rights_contract records legal rights ownership/licensing terms, not a
    sales/commercial agreement. The two tables are never joined or merged.
"""
