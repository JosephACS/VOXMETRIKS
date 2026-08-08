> **Nota histórica:** este documento es intención histórica de Spec-Driven Development.
> No es fuente del estado actual del producto.
> La verdad vigente está en [`docs/STATUS.md`](../../../docs/STATUS.md).
> La documentación completa anterior es recuperable desde Git en el commit `d2f6a27f`.

# Spec 031 — Artist Music Submission, Catalog Review and Release Publishing

**Status:** `CLOSED_WITH_ACCEPTED_DEBT` (target at closure)
**Date:** 2026-07-15
**Package:** `catalog_publishing`
**Depends on:** Spec 020 artists · Spec 021 catalog rights · Spec 030 royalties (consumer of published assets/events)

## Summary

Artists, managers and labels can **submit** new music privately, pass **catalog review** and **rights checks**, then **publish** into the playable catalog without replacing the imported warehouse (~89 740 tracks).

| Verb | Meaning |
|------|---------|
| Upload | Private media + metadata — **not** public |
| Submit | Enter review; sensitive fields lock |
| Approve | Rules OK — may still be **scheduled** |
| Publish | Visible, searchable, playable |
| Withdraw/Suspend | Hide; keep history/contracts/events |

## Rules (non-negotiable)

- No real distribution to Spotify/Apple
- No professional multi-format transcoder claim
- No publish before approval
- No executables as media
- Backend is source of truth · RBAC · org isolation · audit
- Spec 030 may consume published assets/events later — do not auto-mint thousands of events on publish

## Success criteria

1. `demo.artist` can create → submit → (reviewer) approve → publish
2. Unpublished audio is not publicly listable
3. Published track playable via `local_published` audio source priority
4. Rights % ≠ 100 or open conflict blocks publish
5. Golden Path S031 + S030/S029/S028 still green
6. Imported catalog cardinality unchanged for legacy ids

## Actors

Artist / Artist manager · Label content manager · Catalog reviewer · Rights manager · Platform admin (incidents) · Finance (read royalties only — never content approve)
