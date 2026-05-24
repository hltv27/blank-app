#!/usr/bin/env python3
"""
REBORNFENIX (RBFX) — Metaplex v3 Metadata Generator  v2.0
=============================================================
Two-tier collection on Solana:

  Tier 1 — 22 Founding Warriors  @ 100 USDC each
    · Imperial Purple (#4B0082 → #7B2FBE gradient)
    · Fully personalised after purchase (name + zodiac from patron)
    · Template metadata only — placeholders for name, zodiac, sword combo

  Tier 2 — 22,222 Legion of Honour  @ 10 USDC each
    · Circular medal: phoenix + unique Elder Futhark rune + knotwork border
    · Generation colour determined by ORDER OF PURCHASE (token_id range):
        Gen 1  #1–2222     Red Phoenix   #CC0000
        Gen 2  #2223–4444  Gold          #FFD700
        Gen 3  #4445–6666  Silver        #C0C0C0
        Gen 4  #6667–8888  Bronze        #CD7F32
        Gen 5  #8889–11110 Arctic Blue   #00CED1
        Gen 6  #11111–13332 Void Purple  #6A0DAD
        Gen 7  #13333–15554 Emerald      #50C878
        Gen 8  #15555–17776 Copper       #B87333
        Gen 9  #17777–19998 Obsidian     #1C1C1C
        Gen 10 #19999–22222 Iron         #808080

Norse warrior collection honouring resilience, fatherhood, and rebirth through loss.
"""

import json
import os
import random
from pathlib import Path
from collections import defaultdict
from typing import Optional

# ────────────────────────────────────────────────
# PATHS
# ────────────────────────────────────────────────
BASE_DIR   = Path("/home/user/blank-app/rebornfenix/metadata")
OUTPUT_DIR = BASE_DIR / "generated"
ATTRS_FILE = BASE_DIR / "runes_attributes.json"

# ────────────────────────────────────────────────
# COLLECTION CONSTANTS
# ────────────────────────────────────────────────
LEGION_SUPPLY          = 22_222
FOUNDING_WARRIOR_COUNT = 22
EXAMPLE_COUNT          = 5      # Legion examples written to disk by default

BASE_IMAGE_URL_LEGION   = "https://arweave.net/REBORNFENIX_LEGION_PLACEHOLDER"
BASE_IMAGE_URL_FOUNDING = "https://arweave.net/REBORNFENIX_FOUNDING_PLACEHOLDER"
COLLECTION_ADDRESS      = "RBFX_COLLECTION_PLACEHOLDER_SOLANA_ADDRESS"

DESCRIPTION_LEGION_EN = (
    "REBORNFENIX Legion of Honour — one of 22,222 warriors forged in the fires of "
    "Ragnarök. Each token carries a unique Elder Futhark rune and the colours of their "
    "generation, earned by the order in which they answered the call. Not all who trade "
    "are warriors. But every warrior who trades knows: you do not surrender. You adapt. "
    "You endure. You return."
)

DESCRIPTION_FOUNDING_EN = (
    "REBORNFENIX Founding Warrior — one of only 22. Imperial Purple. Fully personalised. "
    "In ancient Rome, wearing purple without being Emperor was punishable by death. "
    "The 22 Founding Warriors carry this colour — not because they claimed it, but because "
    "they built the fire that made it possible. This NFT bears the patron's chosen name "
    "and zodiac sign, and a sword engraved with a unique combination of Norse runes."
)

# ────────────────────────────────────────────────
# GENERATION RESOLVER
# Colour / generation determined by token_id range — NOT random
# ────────────────────────────────────────────────

# Each entry: (range_end_inclusive, generation_dict)
# Built at runtime from runes_attributes.json; kept here as fallback reference.
_GENERATION_RANGES = [
    (2222,  {"id": 1,  "name": "Phoenix Guard",    "color": "Red Phoenix",  "hex": "#CC0000"}),
    (4444,  {"id": 2,  "name": "Gold Battalion",   "color": "Gold",         "hex": "#FFD700"}),
    (6666,  {"id": 3,  "name": "Silver Vanguard",  "color": "Silver",       "hex": "#C0C0C0"}),
    (8888,  {"id": 4,  "name": "Bronze Legion",    "color": "Bronze",       "hex": "#CD7F32"}),
    (11110, {"id": 5,  "name": "Frost Warriors",   "color": "Arctic Blue",  "hex": "#00CED1"}),
    (13332, {"id": 6,  "name": "Void Seekers",     "color": "Void Purple",  "hex": "#6A0DAD"}),
    (15554, {"id": 7,  "name": "Midgard Rangers",  "color": "Emerald",      "hex": "#50C878"}),
    (17776, {"id": 8,  "name": "Copper Shields",   "color": "Copper",       "hex": "#B87333"}),
    (19998, {"id": 9,  "name": "Shadow Guard",     "color": "Obsidian",     "hex": "#1C1C1C"}),
    (22222, {"id": 10, "name": "Iron Born",        "color": "Iron",         "hex": "#808080"}),
]


def resolve_generation(token_id: int) -> dict:
    """Return generation info dict for a given Legion token_id (1–22222)."""
    for range_end, gen in _GENERATION_RANGES:
        if token_id <= range_end:
            return gen
    return _GENERATION_RANGES[-1][1]  # fallback: Iron Born


def load_generation_table(attrs_data: dict) -> list[dict]:
    """Load generation definitions from runes_attributes.json."""
    return attrs_data.get("generations", [])


# ────────────────────────────────────────────────
# RUNE SELECTION — sequential, not weighted random
# 22,222 tokens / 24 runes → each rune appears ~926 times
# Assignment: round-robin by token_id ensures every rune appears evenly,
# with a deterministic per-rune shuffle inside each cycle for ordering variety.
# ────────────────────────────────────────────────

def build_rune_assignment(supply: int, runes: list[dict]) -> list[dict]:
    """
    Pre-assign runes to all token_ids so each rune appears as evenly as possible.
    Returns a list of length `supply`, indexed by (token_id - 1).
    """
    n = len(runes)
    # Build a shuffled cycle of rune indices, repeated to cover supply
    rng = random.Random(0xAB1234)  # deterministic seed (0xAB1234 = RBFX seed)
    assignment = []
    while len(assignment) < supply:
        cycle = list(range(n))
        rng.shuffle(cycle)
        assignment.extend(cycle)
    return [runes[i] for i in assignment[:supply]]


# ────────────────────────────────────────────────
# LEGION ATTRIBUTE BUILDER
# ────────────────────────────────────────────────

def build_legion_attributes(token_id: int, rune: dict, generation: dict) -> list[dict]:
    """Return Metaplex-compatible attributes for a Legion of Honour NFT."""
    return [
        {"trait_type": "Rune",             "value": rune["name"]},
        {"trait_type": "Rune Symbol",      "value": rune["symbol"]},
        {"trait_type": "Rune Meaning",     "value": rune["meaning"]},
        {"trait_type": "Generation",       "value": generation["id"],   "display_type": "number"},
        {"trait_type": "Generation Name",  "value": generation["name"]},
        {"trait_type": "Ring Color",       "value": generation["color"]},
        {"trait_type": "Ring Color Hex",   "value": generation["hex"]},
        {"trait_type": "Token Number",     "value": token_id,            "display_type": "number"},
        {"trait_type": "Rune Number",      "value": rune["id"],          "display_type": "number"},
    ]


# ────────────────────────────────────────────────
# LEGION METADATA BUILDER
# ────────────────────────────────────────────────

def build_legion_metadata(token_id: int, rune: dict, generation: dict) -> dict:
    """
    Construct a Metaplex Token Metadata Program v3 compatible JSON object
    for a Legion of Honour NFT.
    Reference: https://docs.metaplex.com/programs/token-metadata/token-standard
    """
    image_url = f"{BASE_IMAGE_URL_LEGION}/{token_id:05d}.png"

    lore_line = (
        "Legion of Honour #{token_id:05d}. Generation {gen_id} — {gen_name}. "
        "The rune of {rune_name} burns at the centre of their medal. "
        "They answered the call when {gen_name} rode out. The ring is {color}. "
        "The oath is the same as every warrior who came before."
    ).format(
        token_id=token_id,
        gen_id=generation["id"],
        gen_name=generation["name"],
        rune_name=rune["name"],
        color=generation["color"],
    )

    lore_pt = (
        "Legião de Honra #{token_id:05d}. Geração {gen_id} — {gen_name}. "
        "A runa de {rune_name} arde no centro da sua medalha. "
        "Responderam ao chamado quando a {gen_name} partiu. O anel é {color}. "
        "O juramento é o mesmo de cada guerreiro que veio antes."
    ).format(
        token_id=token_id,
        gen_id=generation["id"],
        gen_name=generation["name"],
        rune_name=rune["name"],
        color=generation["color"],
    )

    return {
        "name":                    f"REBORNFENIX Legion #{token_id:05d}",
        "symbol":                  "RBFX",
        "description":             DESCRIPTION_LEGION_EN,
        "seller_fee_basis_points": 500,
        "image":                   image_url,
        "animation_url":           None,
        "external_url":            "https://rebornfenix.io",
        "attributes":              build_legion_attributes(token_id, rune, generation),
        "properties": {
            "files": [{"uri": image_url, "type": "image/png"}],
            "category": "image",
            "creators": [{"address": "RBFX_CREATOR_WALLET_PLACEHOLDER", "share": 100}],
        },
        "collection": {
            "name":     "REBORNFENIX",
            "family":   "RBFX",
            "verified": False,
            "address":  COLLECTION_ADDRESS,
        },
        "lore":             lore_line,
        "lore_pt":          lore_pt,
        "metadata_version": "2.0.0",
        "standard":         "Metaplex Token Metadata v3",
        "tier":             "Legion of Honour",
    }


# ────────────────────────────────────────────────
# FOUNDING WARRIOR ATTRIBUTE BUILDER
# ────────────────────────────────────────────────

def build_founding_attributes(warrior_slot: int, sword_combo: dict) -> list[dict]:
    """
    Return Metaplex-compatible attributes for a Founding Warrior template.
    Zodiac and patron name are PLACEHOLDERS — filled after purchase.
    """
    sword_runes_str = " · ".join(
        f"{sym} {name}"
        for sym, name in zip(sword_combo["runes"], sword_combo["rune_names"])
    )
    return [
        {"trait_type": "Tier",         "value": "Founding Warrior"},
        {"trait_type": "Color",        "value": "#4B0082 → #7B2FBE"},
        {"trait_type": "Color Name",   "value": "Imperial Purple"},
        {"trait_type": "Sword Runes",  "value": sword_runes_str},
        {"trait_type": "Sword Meaning","value": sword_combo["meaning"]},
        {"trait_type": "Zodiac",       "value": "PLACEHOLDER — provided by patron after purchase"},
        {"trait_type": "Patron Name",  "value": "PLACEHOLDER — provided by patron after purchase"},
        {"trait_type": "Token ID",     "value": warrior_slot, "display_type": "number"},
    ]


# ────────────────────────────────────────────────
# FOUNDING WARRIOR METADATA BUILDER
# ────────────────────────────────────────────────

def build_founding_metadata(warrior_slot: int, sword_combo: dict) -> dict:
    """
    Construct a Metaplex Token Metadata Program v3 compatible JSON object
    for a Founding Warrior TEMPLATE.
    Patron name and zodiac are left as placeholders pending patron input.
    """
    image_url = f"{BASE_IMAGE_URL_FOUNDING}/FW{warrior_slot:02d}_PLACEHOLDER.png"

    return {
        "name":                    f"REBORNFENIX Founding Warrior #FW{warrior_slot:02d}",
        "symbol":                  "RBFX",
        "description":             DESCRIPTION_FOUNDING_EN,
        "seller_fee_basis_points": 500,
        "image":                   image_url,
        "animation_url":           None,
        "external_url":            "https://rebornfenix.io",
        "attributes":              build_founding_attributes(warrior_slot, sword_combo),
        "properties": {
            "files": [{"uri": image_url, "type": "image/png"}],
            "category": "image",
            "creators": [{"address": "RBFX_CREATOR_WALLET_PLACEHOLDER", "share": 100}],
        },
        "collection": {
            "name":     "REBORNFENIX",
            "family":   "RBFX",
            "verified": False,
            "address":  COLLECTION_ADDRESS,
        },
        "lore": (
            f"Founding Warrior slot {warrior_slot} of 22. Imperial Purple. "
            f"Sword engraved with {' + '.join(sword_combo['rune_names'])} — "
            f"{sword_combo['meaning']}. "
            "This NFT awaits its patron's name and zodiac to be fully reborn."
        ),
        "lore_pt": (
            f"Founding Warrior posição {warrior_slot} de 22. Púrpura Imperial. "
            f"Espada gravada com {' + '.join(sword_combo['rune_names'])} — "
            f"{sword_combo['meaning']}. "
            "Este NFT aguarda o nome e o signo do patrono para renascer completamente."
        ),
        "metadata_version":  "2.0.0",
        "standard":          "Metaplex Token Metadata v3",
        "tier":              "Founding Warrior",
        "_customisation_note": (
            "After purchase, patron provides: (1) chosen name for arc-bottom text, "
            "(2) zodiac sign for shield. Art is then generated and this metadata updated. "
            "Max 1 per wallet. Supply: 22."
        ),
    }


# ────────────────────────────────────────────────
# DISTRIBUTION TRACKER
# ────────────────────────────────────────────────

class DistributionTracker:
    def __init__(self):
        self.generations = defaultdict(int)
        self.runes       = defaultdict(int)
        self.total       = 0

    def record(self, rune: dict, generation: dict):
        self.generations[f"Gen {generation['id']} — {generation['name']}"] += 1
        self.runes[rune["name"]] += 1
        self.total += 1

    def print_report(self):
        print("\n" + "=" * 65)
        print("REBORNFENIX — LEGION OF HONOUR GENERATION DISTRIBUTION REPORT")
        print("=" * 65)
        print(f"\nTotal Legion NFTs simulated: {self.total:,}")

        print("\n── GENERATIONS (colour by purchase order) ──")
        for gen_label, count in sorted(self.generations.items()):
            pct = count / self.total * 100
            print(f"  {gen_label:<35}: {count:>5,}  ({pct:>5.2f}%)")

        print("\n── RUNE DISTRIBUTION ──")
        sorted_runes = sorted(self.runes.items(), key=lambda x: -x[1])
        for name, count in sorted_runes:
            pct = count / self.total * 100
            bar = "█" * int(pct / 0.5)
            print(f"  {name:<12}: {count:>5,}  ({pct:>5.2f}%)  {bar}")

        print("\n── UNIQUENESS ANALYSIS ──")
        print(f"  24 runes × 10 generations = 240 unique attribute combos possible")
        print(f"  Collection size: {self.total:,}")
        print(f"  Each rune appears ~{self.total // 24:,} times across all generations")
        print(f"  Every token is individually unique by Token Number + art.")
        print("=" * 65 + "\n")


# ────────────────────────────────────────────────
# MAIN GENERATOR
# ────────────────────────────────────────────────

def generate(
    supply: int = LEGION_SUPPLY,
    example_count: int = EXAMPLE_COUNT,
    seed: Optional[int] = None,
    write_all: bool = False,
):
    """
    Generate Legion of Honour metadata (all `supply` tokens) and
    all 22 Founding Warrior templates.

    By default, writes only `example_count` Legion JSONs + all 22 Founding
    Warrior templates to disk. Pass write_all=True to write every Legion token.
    """
    if seed is not None:
        random.seed(seed)

    # ── Load attributes ──────────────────────────────────────────────────────
    with open(ATTRS_FILE, "r", encoding="utf-8") as f:
        attrs_data = json.load(f)

    runes          = attrs_data["elder_futhark_runes"]                # 24 runes
    sword_combos   = attrs_data["founding_warrior_sword_rune_combos"]["combos"]  # 22 combos

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    founding_dir = OUTPUT_DIR / "founding_warriors"
    founding_dir.mkdir(parents=True, exist_ok=True)

    # ── Pre-assign runes deterministically ───────────────────────────────────
    rune_assignment = build_rune_assignment(supply, runes)

    # ── Legion of Honour ─────────────────────────────────────────────────────
    tracker      = DistributionTracker()
    saved_legion = 0

    files_to_write = example_count if not write_all else supply

    print(f"\nGenerating {supply:,} Legion of Honour metadata entries...")
    print(f"Writing first {files_to_write} Legion JSONs to: {OUTPUT_DIR}\n")

    for token_id in range(1, supply + 1):
        rune       = rune_assignment[token_id - 1]
        generation = resolve_generation(token_id)

        tracker.record(rune, generation)

        if token_id <= files_to_write:
            metadata = build_legion_metadata(token_id, rune, generation)
            out_path = OUTPUT_DIR / f"{token_id:05d}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            saved_legion += 1
            print(f"  [{token_id:05d}] {metadata['name']}")
            print(f"         Rune: {rune['symbol']} {rune['name']}  |  {generation['name']} ({generation['color']} {generation['hex']})")
            print()

        if token_id % 5000 == 0:
            print(f"  ... processed {token_id:,} / {supply:,} ({token_id / supply * 100:.0f}%)")

    print(f"\nLegion examples written to disk: {saved_legion}")

    # ── Founding Warriors ─────────────────────────────────────────────────────
    print("\n" + "─" * 65)
    print("Generating 22 Founding Warrior template metadata entries...\n")

    fw_metas = []
    for sword_combo in sword_combos:
        slot     = sword_combo["warrior_slot"]
        metadata = build_founding_metadata(slot, sword_combo)
        out_path = founding_dir / f"FW{slot:02d}_template.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        fw_metas.append(metadata)
        print(f"  [FW{slot:02d}] {metadata['name']}")
        print(f"         Sword: {' · '.join(sword_combo['rune_names'])}")
        print(f"         Meaning: {sword_combo['meaning']}")
        print()

    print(f"Founding Warrior templates written: {len(fw_metas)}")

    # ── Distribution report ───────────────────────────────────────────────────
    tracker.print_report()

    # ── Manifest ─────────────────────────────────────────────────────────────
    manifest = {
        "collection":                     "REBORNFENIX",
        "symbol":                         "RBFX",
        "schema_version":                 "2.0.0",
        "legion_supply":                  supply,
        "legion_example_files_generated": saved_legion,
        "founding_warrior_count":         len(fw_metas),
        "total_collection_size":          supply + len(fw_metas),
        "generation_ranges": [
            {
                "id":          gen["id"],
                "name":        gen["name"],
                "color":       gen["color"],
                "hex":         gen["hex"],
                "token_start": start,
                "token_end":   end,
            }
            for (end, gen), start in zip(
                _GENERATION_RANGES,
                [1] + [e + 1 for e, _ in _GENERATION_RANGES[:-1]],
            )
        ],
        "output_dirs": {
            "legion":            str(OUTPUT_DIR),
            "founding_warriors": str(founding_dir),
        },
        "note": (
            "Legion examples only. Run generate(write_all=True) or pass --full flag "
            "to write all 22,222 JSON files. All 22 Founding Warrior templates always written."
        ),
    }
    manifest_path = OUTPUT_DIR / "_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Manifest written: {manifest_path}\n")


# ────────────────────────────────────────────────
# ENTRY POINT
# ────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="REBORNFENIX NFT Metadata Generator v2 — Metaplex v3"
    )
    parser.add_argument(
        "--supply", type=int, default=LEGION_SUPPLY,
        help=f"Total Legion NFTs to generate (default: {LEGION_SUPPLY})"
    )
    parser.add_argument(
        "--examples", type=int, default=EXAMPLE_COUNT,
        help=f"Number of Legion JSON files to write to disk (default: {EXAMPLE_COUNT})"
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Optional random seed for reproducible rune assignment"
    )
    parser.add_argument(
        "--full", action="store_true",
        help="Write ALL Legion metadata files to disk (22,222 files — slow!)"
    )

    args = parser.parse_args()
    generate(
        supply=args.supply,
        example_count=args.examples,
        seed=args.seed,
        write_all=args.full,
    )
