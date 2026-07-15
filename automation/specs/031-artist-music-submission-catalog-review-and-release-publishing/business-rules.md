# Business rules — Spec 031

| ID | Rule |
|----|------|
| BR-PUB-01 | Private upload ≠ public catalog |
| BR-PUB-02 | Cannot publish before approve |
| BR-PUB-03 | Rights ownership sum must be 100% per rights_type+asset |
| BR-PUB-04 | Open blocking conflict blocks publish |
| BR-PUB-05 | Duplicate audio sha256 in org blocks submit |
| BR-PUB-06 | Duplicate ISRC in org blocks submit |
| BR-PUB-07 | Soft-warn title+artist+duration near-dup |
| BR-PUB-08 | No destructive delete of published release |
| BR-PUB-09 | Withdraw/suspend require reason |
| BR-PUB-10 | Suspended/withdrawn not searchable / not newly playable |
| BR-PUB-11 | Finance cannot approve content |
| BR-PUB-12 | Artist cannot view other artists’ submissions (portal scope) |
| BR-PUB-13 | Media magic+MIME+size validated; no trust extension alone |
| BR-PUB-14 | Audio resolve preference: local_published first |
| BR-PUB-15 | Imported dim_track ids &lt; 100000 untouched; demo inserts ≥ 9_000_000 `[DEMO-SUBMIT]` only if needed |
| BR-PUB-16 | Spec 030 may use published assets/events; publish does not mint mass events |
