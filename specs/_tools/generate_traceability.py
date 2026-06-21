#!/usr/bin/env python3
"""Generate master traceability matrix and validate CU-HU-FR-CA coverage."""
from __future__ import annotations

import json
from pathlib import Path

from implementation_evidence import FR_EVIDENCE

SPECS_ROOT = Path(__file__).resolve().parents[1]
MASTER_VERSION = "2.0.0"
MASTER_DATE = "2026-06-20"

# Each entry: spec, oe, ot, oo, meta, dept, pkg, cu, hu, fr, ca, impl, evidence
ROWS: list[dict] = []


def resolve_impl(fr: str) -> tuple[str, str]:
    impl, evidence = FR_EVIDENCE.get(fr, ("Pendiente", "—"))
    return impl, evidence


def add(spec, oe, ot, oo, meta, dept, pkg, cu, hu, fr, ca):
    impl, evidence = resolve_impl(fr)
    ROWS.append({
        "spec": spec, "oe": oe, "ot": ot, "oo": oo, "meta": meta,
        "dept": dept, "pkg": pkg, "cu": cu, "hu": hu, "fr": fr, "ca": ca,
        "impl": impl, "evidence": evidence,
    })

# --- 001 ---
S, OE, OT, OO, D, P = "001", "OE-01", "OT-01", "OO-01", "DEP-01", "PKG-01"
add(S, OE, OT, OO, "M-02", D, P, "CU-01", "US-01", "FR-001", "CA-001")
add(S, OE, OT, OO, "M-02", D, P, "CU-01", "US-01", "FR-002", "CA-001")
add(S, OE, OT, OO, "M-02", D, P, "CU-01", "US-01", "FR-003", "CA-001")
add(S, OE, OT, OO, "M-02", D, P, "CU-01", "US-01", "FR-004", "CA-008")
add(S, OE, OT, OO, "M-02", D, P, "CU-01", "US-01", "FR-017", "CA-001")
add(S, OE, OT, OO, "M-02", D, P, "CU-01", "US-01", "FR-018", "CA-001")
add(S, OE, OT, OO, "M-02", D, P, "CU-02", "US-02", "FR-005", "CA-002")
add(S, OE, OT, OO, "M-02", D, P, "CU-02", "US-02", "FR-006", "CA-002")
add(S, OE, OT, OO, "M-02", D, P, "CU-02", "US-02", "FR-007", "CA-002")
add(S, OE, OT, OO, "M-02", D, P, "CU-02", "US-02", "FR-020", "CA-002")
add(S, OE, OT, OO, "M-01", D, P, "CU-03", "US-03", "FR-008", "CA-003")
add(S, OE, OT, OO, "M-01", D, P, "CU-03", "US-03", "FR-009", "CA-003")
add(S, OE, OT, OO, "M-02", D, P, "CU-04", "US-04", "FR-010", "CA-004")
add(S, OE, OT, OO, "M-02", D, P, "CU-04", "US-04", "FR-011", "CA-004")
add(S, OE, OT, OO, "M-03", D, P, "CU-05", "US-05", "FR-012", "CA-005")
add(S, OE, OT, OO, "M-03", D, P, "CU-06", "US-06", "FR-013", "CA-006")
add(S, OE, OT, OO, "M-03", D, P, "CU-06", "US-06", "FR-014", "CA-006")
add(S, OE, OT, OO, "M-03", D, P, "CU-06", "US-07", "FR-015", "CA-007")
add(S, OE, OT, OO, "M-01", D, P, "CU-07", "US-01", "FR-016", "CA-001")
add(S, OE, OT, OO, "M-01", D, P, "CU-07", "US-02", "FR-016", "CA-002")
add(S, OE, OT, OO, "M-02", D, P, "CU-07", "US-02", "FR-019", "CA-002")
add(S, OE, OT, OO, "M-03", D, P, "CU-07", "US-06", "FR-019", "CA-006")

# --- 002 ---
S, OE, OT, OO, D, P = "002", "OE-01", "OT-02", "OO-02", "DEP-02", "PKG-02"
for cu, hu, fr, ca in [
    ("CU-P01", "US-P01", "FR-P01", "CA-001"),
    ("CU-P02", "US-P01", "FR-P02", "CA-001"),
    ("CU-P03", "US-P01", "FR-P03", "CA-001"),
    ("CU-P04", "US-P01", "FR-P04", "CA-001"),
    ("CU-P05", "US-P01", "FR-P05", "CA-001"),
    ("CU-P06", "US-P02", "FR-P06", "CA-002"),
    ("CU-P07", "US-P02", "FR-P07", "CA-002"),
]:
    add(S, OE, OT, OO, "M-1A", D, P, cu, hu, fr, ca)
add(S, OE, OT, OO, "M-1A", D, P, "CU-P01", "US-P01", "FR-P08", "CA-006")
add(S, OE, OT, OO, "M-1A", D, P, "CU-P02", "US-P01", "FR-P09", "CA-004")
add(S, OE, OT, OO, "M-1A", D, P, "CU-P04", "US-P01", "FR-P10", "CA-004")
add(S, OE, OT, OO, "M-1A", D, P, "CU-P06", "US-P02", "FR-P11", "CA-005")
add(S, OE, OT, OO, "M-1A", D, P, "CU-P03", "US-P01", "FR-P12", "CA-001")
add(S, OE, OT, OO, "M-1D", D, P, "CU-P07", "US-P03", "FR-P13", "CA-002")
OO = "OO-03"
for cu, hu, fr, ca in [
    ("CU-F01", "US-F01", "FR-F01", "CA-003"),
    ("CU-F02", "US-F01", "FR-F02", "CA-003"),
    ("CU-F03", "US-F01", "FR-F03", "CA-003"),
    ("CU-F04", "US-F01", "FR-F04", "CA-005"),
    ("CU-F04", "US-F01", "FR-F05", "CA-005"),
    ("CU-F01", "US-F01", "FR-F06", "CA-003"),
]:
    add(S, OE, OT, OO, "M-1B", D, P, cu, hu, fr, ca)
add(S, OE, OT, OO, "M-1C", D, P, "CU-F01", "US-F01", "FR-F01", "CA-003")

# --- 003 ---
S, OE, OT, D, P = "003", "OE-01", "OT-03", "DEP-02", "PKG-02"
mappings_003 = [
    ("OO-04", "M-4A", "CU-C01", "US-C01", "FR-C01", "CA-001"),
    ("OO-04", "M-4A", "CU-C02", "US-C01", "FR-C02", "CA-001"),
    ("OO-04", "M-4A", "CU-C03", "US-C01", "FR-C03", "CA-001"),
    ("OO-04", "M-4A", "CU-C03", "US-C01", "FR-C04", "CA-001"),
    ("OO-04", "M-4A", "CU-C04", "US-C02", "FR-C07", "CA-001"),
    ("OO-04", "M-4C", "CU-C05", "US-C02", "FR-C08", "CA-001"),
    ("OO-04", "M-4C", "CU-C05", "US-C02", "FR-C09", "CA-001"),
    ("OO-04", "M-4C", "CU-C05", "US-C02", "FR-C10", "CA-003"),
    ("OO-04", "M-4A", "CU-C06", "US-C01", "FR-C05", "CA-001"),
    ("OO-04", "M-4A", "CU-C06", "US-C01", "FR-C06", "CA-001"),
    ("OO-04", "M-4A", "CU-C04", "US-C02", "FR-C11", "CA-001"),
    ("OO-04", "M-4A", "CU-C01", "US-C01", "FR-C12", "CA-004"),
    ("OO-05", "M-4B", "CU-S01", "US-S01", "FR-S01", "CA-002"),
    ("OO-05", "M-4B", "CU-S02", "US-S01", "FR-S02", "CA-002"),
    ("OO-05", "M-4B", "CU-S01", "US-S01", "FR-S03", "CA-002"),
    ("OO-05", "M-4B", "CU-S02", "US-S01", "FR-S04", "CA-002"),
    ("OO-05", "M-4B", "CU-S03", "US-S01", "FR-S01", "CA-002"),
    ("OO-15", "M-4C", "CU-AF01", "US-AF01", "FR-AF01", "CA-003"),
    ("OO-15", "M-4C", "CU-AF01", "US-AF01", "FR-AF02", "CA-003"),
    ("OO-15", "M-4C", "CU-AF02", "US-C02", "FR-C10", "CA-003"),
    ("OO-15", "M-4C", "CU-AF01", "US-AF01", "FR-AF03", "CA-003"),
    ("OO-04", "M-4A", "CU-C05", "US-C03", "FR-C13", "CA-005"),
]
for oo, meta, cu, hu, fr, ca in mappings_003:
    add(S, OE, OT, oo, meta, D, P, cu, hu, fr, ca)

# --- 004 ---
S, OE, OT, D, P = "004", "OE-01", "OT-04", "DEP-02", "PKG-03"
mappings_004 = [
    ("OO-06", "M-6A", "CU-R01", "US-R01", "FR-R01", "CA-001"),
    ("OO-06", "M-6A", "CU-R01", "US-R01", "FR-R02", "CA-001"),
    ("OO-06", "M-6A", "CU-R01", "US-R01", "FR-R03", "CA-005"),
    ("OO-06", "M-6A", "CU-R01", "US-R01", "FR-R07", "CA-003"),
    ("OO-06", "M-6B", "CU-R01", "US-R01", "FR-R03", "CA-001"),
    ("OO-06", "M-6A", "CU-R02", "US-R01", "FR-R02", "CA-001"),
    ("OO-06", "M-6A", "CU-R03", "US-R01", "FR-R04", "CA-001"),
    ("OO-06", "M-6A", "CU-R04", "US-R01", "FR-R09", "CA-001"),
    ("OO-06", "M-6A", "CU-R05", "US-R02", "FR-R05", "CA-002"),
    ("OO-06", "M-6A", "CU-R06", "US-R02", "FR-R06", "CA-002"),
    ("OO-06", "M-6A", "CU-R07", "US-R02", "FR-R10", "CA-002"),
    ("OO-06", "M-6A", "CU-R01", "US-R02", "FR-R08", "CA-003"),
    ("OO-06", "M-6A", "CU-R08", "US-R03", "FR-R12", "CA-001"),
    ("OO-06", "M-6A", "CU-R01", "US-R04", "FR-R11", "CA-003"),
    ("OO-06", "M-6A", "CU-R01", "US-R04", "FR-R13", "CA-006"),
    ("OO-07", "M-7A", "CU-H01", "US-H01", "FR-H01", "CA-004"),
    ("OO-07", "M-7A", "CU-H01", "US-H01", "FR-H02", "CA-004"),
    ("OO-07", "M-7A", "CU-H02", "US-H01", "FR-H03", "CA-004"),
    ("OO-07", "M-7A", "CU-H03", "US-H01", "FR-H04", "CA-004"),
    ("OO-07", "M-7A", "CU-H04", "US-H01", "FR-H04", "CA-006"),
    ("OO-07", "M-7A", "CU-H03", "US-H01", "FR-H05", "CA-004"),
    ("OO-07", "M-7A", "CU-H02", "US-H01", "FR-H06", "CA-004"),
]
for oo, meta, cu, hu, fr, ca in mappings_004:
    add(S, OE, OT, oo, meta, D, P, cu, hu, fr, ca)

# --- 005 ---
S, OE, OT, D, P = "005", "OE-01", "OT-05", "DEP-03", "PKG-04"
mappings_005 = [
    ("OO-08", "M-8A", "CU-RC01", "US-RC01", "FR-RC01", "CA-001"),
    ("OO-08", "M-8A", "CU-RC01", "US-RC01", "FR-RC03", "CA-001"),
    ("OO-08", "M-8A", "CU-RC01", "US-RC01", "FR-RC04", "CA-001"),
    ("OO-08", "M-8A", "CU-RC01", "US-RC01", "FR-RC06", "CA-001"),
    ("OO-08", "M-8A", "CU-RC01", "US-RC01", "FR-RC08", "CA-001"),
    ("OO-08", "M-8B", "CU-RC02", "US-RC01", "FR-RC02", "CA-001"),
    ("OO-08", "M-8A", "CU-RC02", "US-RC01", "FR-RC05", "CA-002"),
    ("OO-08", "M-8A", "CU-RC03", "US-RC02", "FR-RC07", "CA-006"),
    ("OO-08", "M-8A", "CU-RC04", "US-RC02", "FR-RC07", "CA-007"),
    ("OO-09", "M-9A", "CU-HI01", "US-HI01", "FR-HI01", "CA-003"),
    ("OO-09", "M-9A", "CU-HI01", "US-HI01", "FR-HI02", "CA-004"),
    ("OO-09", "M-9A", "CU-HI01", "US-HI01", "FR-HI03", "CA-003"),
    ("OO-09", "M-9B", "CU-HI01", "US-HI01", "FR-HI03", "CA-004"),
    ("OO-09", "M-9A", "CU-HI04", "US-HI02", "FR-HI01", "CA-003"),
    ("OO-09", "M-9A", "CU-HI04", "US-HI02", "FR-HI07", "CA-003"),
    ("OO-09", "M-9B", "CU-HI02", "US-HI02", "FR-HI04", "CA-005"),
    ("OO-09", "M-9B", "CU-HI02", "US-HI02", "FR-HI05", "CA-005"),
    ("OO-09", "M-9B", "CU-HI03", "US-HI02", "FR-HI06", "CA-003"),
    ("OO-09", "M-9B", "CU-HI03", "US-HI02", "FR-HI06", "CA-005"),
    ("OO-09", "M-9B", "CU-HI02", "US-HI02", "FR-HI08", "CA-005"),
    ("OO-09", "M-9A", "CU-HI01", "US-HI03", "FR-HI09", "CA-006"),
    ("OO-09", "M-9B", "CU-HI05", "US-HI04", "FR-HI10", "CA-003"),
]
for oo, meta, cu, hu, fr, ca in mappings_005:
    add(S, OE, OT, oo, meta, D, P, cu, hu, fr, ca)

# --- 006 ---
S, OE, OT, D, P = "006", "OE-01", "OT-06", "DEP-01", "PKG-05"
mappings_006 = [
    ("OO-11", "M-11A", "CU-PF01", "US-PF01", "FR-PF01", "CA-001"),
    ("OO-11", "M-11A", "CU-PF01", "US-PF01", "FR-PF02", "CA-001"),
    ("OO-11", "M-11A", "CU-PF01", "US-PF01", "FR-PF03", "CA-001"),
    ("OO-11", "M-11A", "CU-PF02", "US-PF01", "FR-PF04", "CA-002"),
    ("OO-11", "M-11A", "CU-PF03", "US-PF02", "FR-PF05", "CA-001"),
    ("OO-10", "M-10B", "CU-ST01", "US-ST01", "FR-ST01", "CA-003"),
    ("OO-10", "M-10B", "CU-ST01", "US-ST01", "FR-ST02", "CA-003"),
    ("OO-10", "M-10B", "CU-ST02", "US-ST01", "FR-ST03", "CA-003"),
    ("OO-10", "M-10B", "CU-ST01", "US-ST01", "FR-ST04", "CA-003"),
    ("OO-10", "M-10A", "CU-ST03", "US-ST02", "FR-ST05", "CA-004"),
    ("OO-10", "M-10A", "CU-ST03", "US-ST02", "FR-ST06", "CA-004"),
    ("OO-10", "M-10A", "CU-ST03", "US-ST02", "FR-ST08", "CA-004"),
    ("OO-10", "M-10B", "CU-ST04", "US-ST03", "FR-ST07", "CA-003"),
    ("OO-10", "M-10B", "CU-ST04", "US-ST03", "FR-ST04", "CA-003"),
    ("OO-10", "M-10A", "CU-ST05", "US-ST04", "FR-ST09", "CA-005"),
    ("OO-10", "M-10A", "CU-ST05", "US-ST04", "FR-ST10", "CA-005"),
    ("OO-10", "M-10A", "CU-ST06", "US-ST05", "FR-ST11", "CA-006"),
    ("OO-10", "M-10A", "CU-ST01", "US-ST01", "FR-ST12", "CA-007"),
]
for oo, meta, cu, hu, fr, ca in mappings_006:
    add(S, OE, OT, oo, meta, D, P, cu, hu, fr, ca)

# --- 007 ---
S, OE, OT, OO, D, P = "007", "OE-01", "OT-07", "OO-12", "DEP-04", "PKG-06"
mappings_007 = [
    ("M-12A", "CU-AN01", "US-AN01", "FR-AN01", "CA-001"),
    ("M-12A", "CU-AN01", "US-AN01", "FR-AN08", "CA-001"),
    ("M-12A", "CU-AN01", "US-AN01", "FR-AN09", "CA-001"),
    ("M-12A", "CU-AN01", "US-AN01", "FR-AN24", "CA-001"),
    ("M-12A", "CU-AN01", "US-AN01", "FR-AN23", "CA-001"),
    ("M-12D", "CU-AN01", "US-AN01", "FR-AN26", "CA-011"),
    ("M-12A", "CU-AN02", "US-AN01", "FR-AN02", "CA-002"),
    ("M-12A", "CU-AN02", "US-AN01", "FR-AN10", "CA-002"),
    ("M-12A", "CU-AN07", "US-AN02", "FR-AN03", "CA-001"),
    ("M-12A", "CU-AN07", "US-AN02", "FR-AN11", "CA-001"),
    ("M-12B", "CU-AN03", "US-AN02", "FR-AN05", "CA-003"),
    ("M-12B", "CU-AN03", "US-AN02", "FR-AN12", "CA-003"),
    ("M-12B", "CU-AN03", "US-AN02", "FR-AN13", "CA-003"),
    ("M-12B", "CU-AN03", "US-AN02", "FR-AN17", "CA-006"),
    ("M-12B", "CU-AN03", "US-AN02", "FR-AN18", "CA-007"),
    ("M-12C", "CU-AN04", "US-AN03", "FR-AN07", "CA-004"),
    ("M-12C", "CU-AN04", "US-AN03", "FR-AN14", "CA-004"),
    ("M-12C", "CU-AN04", "US-AN03", "FR-AN04", "CA-004"),
    ("M-12C", "CU-AN04", "US-AN03", "FR-AN16", "CA-004"),
    ("M-12C", "CU-AN06", "US-AN03", "FR-AN06", "CA-004"),
    ("M-12D", "CU-AN06", "US-AN03", "FR-AN20", "CA-009"),
    ("M-12D", "CU-AN05", "US-AN04", "FR-AN15", "CA-005"),
    ("M-12D", "CU-AN05", "US-AN04", "FR-AN16", "CA-005"),
    ("M-12D", "CU-AN08", "US-AN05", "FR-AN01", "CA-008"),
    ("M-12D", "CU-AN08", "US-AN05", "FR-AN02", "CA-008"),
    ("M-12D", "CU-AN08", "US-AN05", "FR-AN19", "CA-008"),
    ("M-12D", "CU-AN09", "US-AN05", "FR-AN06", "CA-009"),
    ("M-12D", "CU-AN09", "US-AN05", "FR-AN05", "CA-009"),
    ("M-12D", "CU-AN09", "US-AN05", "FR-AN20", "CA-009"),
    ("M-12C", "CU-AN01", "US-AN06", "FR-AN21", "CA-010"),
    ("M-12C", "CU-AN03", "US-AN06", "FR-AN21", "CA-010"),
    ("M-12C", "CU-AN04", "US-AN06", "FR-AN21", "CA-010"),
    ("M-12C", "CU-AN05", "US-AN06", "FR-AN21", "CA-010"),
    ("M-12D", "CU-AN01", "US-AN06", "FR-AN22", "CA-011"),
    ("M-12D", "CU-AN03", "US-AN06", "FR-AN22", "CA-011"),
    ("M-12C", "CU-AN01", "US-AN06", "FR-AN25", "CA-010"),
]
for meta, cu, hu, fr, ca in mappings_007:
    add(S, OE, OT, OO, meta, D, P, cu, hu, fr, ca)

# --- 008 ---
S, OE, OT, OO, D, P = "008", "OE-01", "OT-08", "OO-13", "DEP-05", "PKG-07"
mappings_008 = [
    ("M-13A", "CU-PM01", "US-PM01", "FR-PM07", "CA-001"),
    ("M-13A", "CU-PM01", "US-PM01", "FR-PM08", "CA-001"),
    ("M-13A", "CU-PM01", "US-PM01", "FR-PM21", "CA-001"),
    ("M-13A", "CU-PM05", "US-PM01", "FR-PM04", "CA-002"),
    ("M-13A", "CU-PM05", "US-PM01", "FR-PM16", "CA-002"),
    ("M-13D", "CU-PM04", "US-PM04", "FR-PM03", "CA-003"),
    ("M-13C", "CU-PM06", "US-PM02", "FR-PM01", "CA-004"),
    ("M-13C", "CU-PM06", "US-PM02", "FR-PM09", "CA-004"),
    ("M-13C", "CU-PM02", "US-PM02", "FR-PM09", "CA-004"),
    ("M-13C", "CU-PM02", "US-PM02", "FR-PM10", "CA-004"),
    ("M-13D", "CU-PM03", "US-PM02", "FR-PM02", "CA-005"),
    ("M-13D", "CU-PM03", "US-PM02", "FR-PM12", "CA-005"),
    ("M-13D", "CU-PM03", "US-PM02", "FR-PM22", "CA-005"),
    ("M-13D", "CU-PM03", "US-PM03", "FR-PM11", "CA-006"),
    ("M-13D", "CU-PM03", "US-PM03", "FR-PM13", "CA-006"),
    ("M-13D", "CU-PM03", "US-PM03", "FR-PM14", "CA-005"),
    ("M-13D", "CU-PM03", "US-PM03", "FR-PM15", "CA-007"),
    ("M-13D", "CU-PM03", "US-PM06", "FR-PM17", "CA-008"),
    ("M-13B", "CU-PM07", "US-PM05", "FR-PM18", "CA-009"),
    ("M-13B", "CU-PM07", "US-PM05", "FR-PM19", "CA-009"),
    ("M-13B", "CU-PM07", "US-PM05", "FR-PM20", "CA-010"),
    ("M-13B", "CU-PM01", "US-PM06", "FR-PM05", "CA-011"),
    ("M-13B", "CU-PM01", "US-PM06", "FR-PM06", "CA-011"),
    ("M-13B", "CU-PM01", "US-PM06", "FR-PM23", "CA-011"),
    ("M-13B", "CU-PM01", "US-PM06", "FR-PM25", "CA-011"),
    ("M-13A", "CU-PM08", "US-PM07", "FR-PM24", "CA-012"),
]
for meta, cu, hu, fr, ca in mappings_008:
    add(S, OE, OT, OO, meta, D, P, cu, hu, fr, ca)

# --- 009 ---
S, OE, OT, OO, D, P = "009", "OE-01", "OT-09", "OO-14", "DEP-05", "PKG-07"
mappings_009 = [
    ("M-14A", "CU-DE01", "US-DE01", "FR-DE01", "CA-001"),
    ("M-14A", "CU-DE01", "US-DE01", "FR-DE03", "CA-001"),
    ("M-14A", "CU-DE01", "US-DE01", "FR-DE13", "CA-001"),
    ("M-14A", "CU-DE01", "US-DE01", "FR-DE14", "CA-001"),
    ("M-14A", "CU-DE02", "US-DE01", "FR-DE09", "CA-002"),
    ("M-14A", "CU-DE05", "US-DE01", "FR-DE15", "CA-003"),
    ("M-14D", "CU-DE03", "US-DE02", "FR-DE02", "CA-004"),
    ("M-14D", "CU-DE03", "US-DE02", "FR-DE04", "CA-004"),
    ("M-14C", "CU-DE03", "US-DE02", "FR-DE12", "CA-005"),
    ("M-14C", "CU-DE03", "US-DE02", "FR-DE11", "CA-005"),
    ("M-14D", "CU-DE04", "US-DE02", "FR-DE06", "CA-006"),
    ("M-14D", "CU-DE04", "US-DE02", "FR-DE10", "CA-006"),
    ("M-14D", "CU-DE05", "US-DE02", "FR-DE07", "CA-005"),
    ("M-14A", "CU-DE06", "US-DE03", "FR-DE16", "CA-007"),
    ("M-14B", "CU-DE07", "US-DE04", "FR-DE08", "CA-008"),
    ("M-14B", "CU-DE07", "US-DE04", "FR-DE18", "CA-008"),
    ("M-14B", "CU-DE07", "US-DE04", "FR-DE17", "CA-009"),
    ("M-14B", "CU-DE01", "US-DE04", "FR-DE19", "CA-009"),
    ("M-14D", "CU-DE03", "US-DE04", "FR-DE21", "CA-009"),
    ("M-14C", "CU-DE03", "US-DE02", "FR-DE05", "CA-010"),
]
for meta, cu, hu, fr, ca in mappings_009:
    add(S, OE, OT, OO, meta, D, P, cu, hu, fr, ca)

# --- 010 ---
S, OE, OT, OO, D, P = "010", "OE-01", "OT-09", "OO-16", "DEP-06", "PKG-02"
mappings_010 = [
    ("M-16A", "CU-CS01", "US-CS01", "FR-CS01", "CA-001"),
    ("M-16A", "CU-CS01", "US-CS01", "FR-CS16", "CA-001"),
    ("M-16A", "CU-CS01", "US-CS01", "FR-CS19", "CA-001"),
    ("M-16B", "CU-CS02", "US-CS01", "FR-CS02", "CA-002"),
    ("M-16B", "CU-CS02", "US-CS01", "FR-CS16", "CA-002"),
    ("M-16C", "CU-CS03", "US-CS01", "FR-CS03", "CA-003"),
    ("M-16C", "CU-CS03", "US-CS01", "FR-CS14", "CA-003"),
    ("M-16B", "CU-CS04", "US-CS02", "FR-CS04", "CA-004"),
    ("M-16B", "CU-CS04", "US-CS02", "FR-CS17", "CA-004"),
    ("M-16B", "CU-CS05", "US-CS02", "FR-CS05", "CA-005"),
    ("M-16B", "CU-CS06", "US-CS02", "FR-CS06", "CA-006"),
    ("M-16B", "CU-CS07", "US-CS03", "FR-CS07", "CA-007"),
    ("M-16B", "CU-CS07", "US-CS03", "FR-CS18", "CA-007"),
    ("M-16B", "CU-CS08", "US-CS03", "FR-CS08", "CA-008"),
    ("M-16B", "CU-CS09", "US-CS03", "FR-CS09", "CA-009"),
    ("M-16A", "CU-CS01", "US-CS04", "FR-CS20", "CA-010"),
    ("M-16A", "CU-CS01", "US-CS04", "FR-CS21", "CA-010"),
    ("M-16A", "CU-CS01", "US-CS04", "FR-CS22", "CA-010"),
    ("M-16C", "CU-CS03", "US-CS04", "FR-CS23", "CA-003"),
    ("M-16D", "CU-CS01", "US-CS05", "FR-CS15", "CA-011"),
    ("M-16D", "CU-CS01", "US-CS05", "FR-CS10", "CA-012"),
]
for meta, cu, hu, fr, ca in mappings_010:
    add(S, OE, OT, OO, meta, D, P, cu, hu, fr, ca)

# --- 011 ---
S, OE, OT, OO, D, P = "011", "OE-01", "OT-10", "OO-17", "DEP-01", "PKG-05"
mappings_011 = [
    ("M-17A", "CU-HO01", "US-HO01", "FR-HO06", "CA-001"),
    ("M-17A", "CU-HO01", "US-HO01", "FR-HO08", "CA-001"),
    ("M-17A", "CU-HO01", "US-HO01", "FR-HO09", "CA-001"),
    ("M-17A", "CU-HO01", "US-HO01", "FR-HO11", "CA-002"),
    ("M-17D", "CU-HO02", "US-HO02", "FR-HO10", "CA-003"),
    ("M-17D", "CU-HO02", "US-HO02", "FR-HO06", "CA-003"),
    ("M-17B", "CU-HO04", "US-HO01", "FR-HO01", "CA-004"),
    ("M-17B", "CU-HO04", "US-HO01", "FR-HO02", "CA-004"),
    ("M-17B", "CU-HO04", "US-HO01", "FR-HO03", "CA-004"),
    ("M-17C", "CU-HO04", "US-HO04", "FR-HO07", "CA-005"),
    ("M-17C", "CU-HO04", "US-HO04", "FR-HO08", "CA-005"),
    ("M-17C", "CU-HO04", "US-HO04", "FR-HO12", "CA-006"),
    ("M-17A", "CU-HO03", "US-HO03", "FR-HO04", "CA-007"),
    ("M-17A", "CU-HO05", "US-HO05", "FR-HO14", "CA-008"),
    ("M-17A", "CU-HO05", "US-HO05", "FR-HO15", "CA-008"),
    ("M-17A", "CU-HO05", "US-HO05", "FR-HO18", "CA-008"),
    ("M-17A", "CU-HO06", "US-HO05", "FR-HO16", "CA-009"),
    ("M-17A", "CU-HO06", "US-HO05", "FR-HO17", "CA-009"),
    ("M-17A", "CU-HO01", "US-HO01", "FR-HO19", "CA-010"),
]
for meta, cu, hu, fr, ca in mappings_011:
    add(S, OE, OT, OO, meta, D, P, cu, hu, fr, ca)


def validate():
    errors = []
    hus = {r["hu"] for r in ROWS}
    cus = {r["cu"] for r in ROWS}
    frs = {r["fr"] for r in ROWS}
    for r in ROWS:
        if not r["hu"]:
            errors.append(f"Missing HU for {r}")
        if not r["cu"]:
            errors.append(f"Missing CU for {r}")
        if not r["fr"]:
            errors.append(f"Missing FR for {r}")
        if not r["ca"]:
            errors.append(f"Missing CA for {r}")
    # Every CU must have at least one FR
    cu_fr = {}
    for r in ROWS:
        cu_fr.setdefault(r["cu"], set()).add(r["fr"])
    all_cus_expected = set()
    for spec_cus in [
        [f"CU-{i:02d}" for i in range(1, 8)],
        [f"CU-P0{i}" for i in range(1, 8)] + [f"CU-F0{i}" for i in range(1, 5)],
        [f"CU-C0{i}" for i in range(1, 7)] + [f"CU-S0{i}" for i in range(1, 4)] + ["CU-AF01", "CU-AF02"],
        [f"CU-R0{i}" for i in range(1, 9)] + [f"CU-H0{i}" for i in range(1, 5)],
        [f"CU-RC0{i}" for i in range(1, 5)] + [f"CU-HI0{i}" for i in range(1, 6)],
        [f"CU-PF0{i}" for i in range(1, 4)] + [f"CU-ST0{i}" for i in range(1, 7)],
        [f"CU-AN0{i}" for i in range(1, 10)],
        [f"CU-PM0{i}" for i in range(1, 9)],
        [f"CU-DE0{i}" for i in range(1, 8)],
        [f"CU-CS0{i}" for i in range(1, 10)],
        [f"CU-HO0{i}" for i in range(1, 7)],
    ]:
        all_cus_expected.update(spec_cus)
    frs_in_rows = {r["fr"] for r in ROWS}
    for fr in sorted(frs_in_rows):
        if fr not in FR_EVIDENCE:
            errors.append(f"FR without evidence mapping: {fr}")
    for cu in sorted(all_cus_expected):
        if cu not in cu_fr:
            errors.append(f"CU without FR mapping: {cu}")
    return errors, len(ROWS), len(hus), len(cus), len(frs)


def impl_summary() -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in ROWS:
        counts[r["impl"]] = counts.get(r["impl"], 0) + 1
    return counts


def render_master_md():
    summary = impl_summary()
    lines = [
        "# Matriz Maestra de Trazabilidad — Capa Operativa Voxmetriks",
        "",
        f"**Versión:** {MASTER_VERSION} | **Ratificado documental:** {MASTER_DATE}",
        "**Alcance:** Specs operativas `001`–`011` (capa operativa completa)",
        "**Cadena:** OE → OT → OO → Meta → Departamento → Paquete → CU → HU → FR → CA → Impl → Evidencia",
        "",
        "Referencia: Constitución v1.0.0 §12. Documento canónico transversal; las specs individuales",
        "incluyen subconjunto y detalle de casos de uso / historias de usuario.",
        "",
        "### Leyenda Impl",
        "",
        "| Valor | Significado |",
        "|-------|-------------|",
        "| **Implementado** | Comportamiento verificable en código según FR |",
        "| **Parcial** | Implementado con brechas documentadas en spec/auditoría |",
        "| **No implementado** | FR no presente en código |",
        "",
        "### Resumen implementación",
        "",
        f"| Métrica | Valor |",
        f"|---------|------:|",
        f"| Filas totales | {len(ROWS)} |",
        f"| Implementado | {summary.get('Implementado', 0)} |",
        f"| Parcial | {summary.get('Parcial', 0)} |",
        f"| No implementado | {summary.get('No implementado', 0)} |",
        f"| Pendiente (sin evidencia) | {summary.get('Pendiente', 0)} |",
        "",
        "Evidencia auditada: `specs/_tools/implementation_evidence.py` + `SPEC-008-011-EVIDENCE-AUDIT.md`.",
        "",
        "| Spec | OE | OT | OO | Meta | Dept | Paquete | CU | HU | FR | CA | Impl | Evidencia |",
        "|------|----|----|-----|------|------|---------|----|----|----|----|------|-----------|",
    ]
    for r in ROWS:
        lines.append(
            f"| {r['spec']} | {r['oe']} | {r['ot']} | {r['oo']} | {r['meta']} | {r['dept']} | {r['pkg']} | "
            f"{r['cu']} | {r['hu']} | {r['fr']} | {r['ca']} | {r['impl']} | `{r['evidence']}` |"
        )
    return "\n".join(lines) + "\n"


def render_fr_ca_by_spec(spec_id: str) -> str:
    seen = set()
    lines = [
        f"## Matriz CU → HU → FR → CA (Spec {spec_id})",
        "",
        "| CU | HU | FR | CA |",
        "|----|----|----|-----|",
    ]
    for r in ROWS:
        if r["spec"] != spec_id:
            continue
        key = (r["cu"], r["hu"], r["fr"], r["ca"])
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"| {r['cu']} | {r['hu']} | {r['fr']} | {r['ca']} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    errors, n_rows, n_hu, n_cu, n_fr = validate()
    out = SPECS_ROOT / "TRACEABILITY-MASTER.md"
    out.write_text(render_master_md(), encoding="utf-8")
    meta = SPECS_ROOT / "_tools" / "traceability-meta.json"
    summary = impl_summary()
    meta.write_text(json.dumps({
        "version": MASTER_VERSION,
        "rows": len(ROWS),
        "hus": n_hu,
        "cus": n_cu,
        "frs": n_fr,
        "specs": ["001", "002", "003", "004", "005", "006", "007", "008", "009", "010", "011"],
        "impl": summary,
        "errors": errors,
    }, indent=2), encoding="utf-8")
    if errors:
        print("VALIDATION ERRORS:")
        for e in errors:
            print(" ", e)
        raise SystemExit(1)
    print(f"OK: {n_rows} rows, {n_hu} HUs, {n_cu} CUs, {n_fr} FRs -> {out}")
