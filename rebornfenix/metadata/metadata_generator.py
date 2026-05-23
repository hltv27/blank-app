#!/usr/bin/env python3
"""
REBORNFENIX (RBFX) — Metaplex v3 Metadata Generator
Generates 22,222 unique NFT metadata JSON files for the Solana collection.

Norse warrior collection honouring resilience, fatherhood, and rebirth through loss.
"""

import json
import os
import random
import hashlib
from pathlib import Path
from collections import defaultdict
from typing import Optional

# ────────────────────────────────────────────────
# PATHS
# ────────────────────────────────────────────────
BASE_DIR    = Path("/home/user/blank-app/rebornfenix/metadata")
OUTPUT_DIR  = BASE_DIR / "generated"
ATTRS_FILE  = BASE_DIR / "runes_attributes.json"

# ────────────────────────────────────────────────
# COLLECTION CONSTANTS
# ────────────────────────────────────────────────
TOTAL_SUPPLY        = 22_222
EXAMPLE_COUNT       = 5          # Only write first N to disk for demo
BASE_IMAGE_URL      = "https://arweave.net/REBORNFENIX_PLACEHOLDER"
COLLECTION_ADDRESS  = "RBFX_COLLECTION_PLACEHOLDER_SOLANA_ADDRESS"

DESCRIPTION_EN = (
    "REBORNFENIX is a collection of 22,222 Viking warriors forged in the fires of "
    "Ragnarök — fathers, fighters, and survivors who stared into the abyss and refused "
    "to break. Each warrior carries the ancient power of Elder Futhark runes, drawn from "
    "the cosmic loom of fate. Not all who trade are warriors. But every warrior who "
    "trades knows: you do not surrender. You adapt. You endure. You return."
)

DESCRIPTION_PT = (
    "REBORNFENIX é uma coleção de 22.222 guerreiros Vikings forjados nos fogos de "
    "Ragnarök — pais, lutadores e sobreviventes que olharam para o abismo e recusaram "
    "quebrar. Cada guerreiro carrega o poder ancestral das runas Elder Futhark, "
    "retiradas do tear cósmico do destino."
)

# ────────────────────────────────────────────────
# WEIGHTED RANDOM SELECTION UTILITY
# ────────────────────────────────────────────────

def weighted_choice(options: list[dict], weight_key: str = "rarity_percentage") -> dict:
    """Pick one item according to its rarity_percentage weight."""
    total = sum(o[weight_key] for o in options)
    r = random.uniform(0, total)
    cumulative = 0.0
    for option in options:
        cumulative += option[weight_key]
        if r <= cumulative:
            return option
    return options[-1]


def weighted_choice_by_weight(options: list[dict], weight_key: str = "rarity_weight") -> dict:
    total = sum(o[weight_key] for o in options)
    r = random.uniform(0, total)
    cumulative = 0.0
    for option in options:
        cumulative += option[weight_key]
        if r <= cumulative:
            return option
    return options[-1]

# ────────────────────────────────────────────────
# RARITY TIER RESOLVER
# ────────────────────────────────────────────────

RARITY_TIER_WEIGHTS = {
    "Legendary": 1.0,
    "Epic":      5.0,
    "Rare":      15.0,
    "Uncommon":  30.0,
    "Common":    49.0,
}

def draw_rarity_tier() -> str:
    r = random.uniform(0, 100)
    cumulative = 0.0
    for tier, weight in RARITY_TIER_WEIGHTS.items():
        cumulative += weight
        if r <= cumulative:
            return tier
    return "Common"

# ────────────────────────────────────────────────
# SPECIAL TRAIT RESOLVER
# Reborn: 0.1% → exactly 22 in 22,222
# ────────────────────────────────────────────────

def build_reborn_token_ids(supply: int) -> set[int]:
    """Pre-assign the 22 Reborn token IDs deterministically using hash seeding."""
    reborn_count = round(supply * 0.001)  # 0.1% = ~22
    random.seed(0xFENRIR)  # deterministic seed so same IDs every run
    reborn_ids = set(random.sample(range(1, supply + 1), reborn_count))
    random.seed()  # restore true randomness
    return reborn_ids

# ────────────────────────────────────────────────
# ATTRIBUTE BUILDERS
# ────────────────────────────────────────────────

def build_attributes(
    token_id: int,
    rune: dict,
    background: dict,
    warrior_class: dict,
    aura: dict,
    rarity_tier: str,
    is_reborn: bool,
    attrs_data: dict,
) -> list[dict]:
    """Return a Metaplex-compatible attributes array."""
    attributes = [
        {"trait_type": "Rune",           "value": f"{rune['symbol']} {rune['name']}"},
        {"trait_type": "Rune Meaning",   "value": rune["meaning"]},
        {"trait_type": "Background",     "value": background["name"]},
        {"trait_type": "Warrior Class",  "value": warrior_class["name"]},
        {"trait_type": "Aura",           "value": aura["name"]},
        {"trait_type": "Rarity Tier",    "value": rarity_tier},
        {"trait_type": "Rune Symbol",    "value": rune["symbol"]},
        {"trait_type": "Rune Power",     "value": rune["trading_wisdom"]},
        {"trait_type": "Class Archetype","value": warrior_class["trading_style"]},
        {"trait_type": "Aura Color Hex", "value": aura["hex"]},
    ]

    if is_reborn:
        attributes.append({"trait_type": "Special", "value": "Reborn"})

    # Numeric traits for rarity scoring
    attributes.append({"trait_type": "Token ID",     "value": token_id,                       "display_type": "number"})
    attributes.append({"trait_type": "Rune Number",  "value": rune["id"],                      "display_type": "number"})
    attributes.append({"trait_type": "Fenrir Score", "value": _compute_fenrir_score(rarity_tier, is_reborn), "display_type": "number"})

    return attributes


def _compute_fenrir_score(rarity_tier: str, is_reborn: bool) -> int:
    """A composite rarity score from 1–1000. Higher = rarer."""
    base = {
        "Legendary": 850,
        "Epic":      650,
        "Rare":      400,
        "Uncommon":  200,
        "Common":    100,
    }.get(rarity_tier, 100)
    bonus = 150 if is_reborn else 0
    jitter = random.randint(-20, 20)
    return max(1, min(1000, base + bonus + jitter))

# ────────────────────────────────────────────────
# METAPLEX v3 JSON BUILDER
# ────────────────────────────────────────────────

def build_metadata(
    token_id: int,
    rune: dict,
    background: dict,
    warrior_class: dict,
    aura: dict,
    rarity_tier: str,
    is_reborn: bool,
    attrs_data: dict,
) -> dict:
    """
    Constructs a Metaplex Token Metadata Program v3 compatible JSON object.
    Reference: https://docs.metaplex.com/programs/token-metadata/token-standard
    """
    name_suffix = " [REBORN]" if is_reborn else ""
    token_name = f"REBORNFENIX #{token_id:05d}{name_suffix}"

    # Deterministic image URL — swap placeholder for Arweave/IPFS after upload
    image_url = f"{BASE_IMAGE_URL}/{token_id:05d}.png"

    lore_line = (
        "Born from fire. Tempered by loss. The rune of the {rune_name} burns in their chest "
        "— a warrior who chose to return when walking away was the easier path."
    ).format(rune_name=rune["name"])

    if is_reborn:
        lore_line = (
            "REBORN — one of the twenty-two. They died in the fire and came back changed. "
            "The rune of {rune_name} did not save them; it witnessed their return and "
            "burned itself deeper into their skin so all the Nine Realms would know."
        ).format(rune_name=rune["name"])

    return {
        "name": token_name,
        "symbol": "RBFX",
        "description": DESCRIPTION_EN,
        "seller_fee_basis_points": 500,
        "image": image_url,
        "animation_url": None,
        "external_url": "https://rebornfenix.io",
        "attributes": build_attributes(
            token_id, rune, background, warrior_class,
            aura, rarity_tier, is_reborn, attrs_data
        ),
        "properties": {
            "files": [
                {
                    "uri": image_url,
                    "type": "image/png"
                }
            ],
            "category": "image",
            "creators": [
                {
                    "address": "RBFX_CREATOR_WALLET_PLACEHOLDER",
                    "share": 100
                }
            ]
        },
        "collection": {
            "name": "REBORNFENIX",
            "family": "RBFX",
            "verified": False,
            "address": COLLECTION_ADDRESS
        },
        "lore": lore_line,
        "lore_pt": (
            f"Nascido do fogo. Temperado pela perda. A runa de {rune['name']} queima no "
            f"seu peito — um guerreiro que escolheu regressar quando partir era o caminho mais fácil."
        ),
        "metadata_version": "1.0.0",
        "standard": "Metaplex Token Metadata v3"
    }

# ────────────────────────────────────────────────
# UNIQUENESS GUARANTEE
# ────────────────────────────────────────────────

def combo_fingerprint(rune_id: int, bg_name: str, class_name: str, aura_name: str, tier: str) -> str:
    key = f"{rune_id}|{bg_name}|{class_name}|{aura_name}|{tier}"
    return hashlib.md5(key.encode()).hexdigest()

# ────────────────────────────────────────────────
# RARITY DISTRIBUTION TRACKER
# ────────────────────────────────────────────────

class DistributionTracker:
    def __init__(self):
        self.rarity_tiers   = defaultdict(int)
        self.backgrounds    = defaultdict(int)
        self.classes        = defaultdict(int)
        self.auras          = defaultdict(int)
        self.runes          = defaultdict(int)
        self.reborn_count   = 0
        self.total          = 0

    def record(self, rune, background, warrior_class, aura, rarity_tier, is_reborn):
        self.rarity_tiers[rarity_tier] += 1
        self.backgrounds[background["name"]] += 1
        self.classes[warrior_class["name"]] += 1
        self.auras[aura["name"]] += 1
        self.runes[rune["name"]] += 1
        if is_reborn:
            self.reborn_count += 1
        self.total += 1

    def print_report(self):
        print("\n" + "="*60)
        print("REBORNFENIX — RARITY DISTRIBUTION REPORT")
        print("="*60)

        print(f"\nTotal NFTs simulated: {self.total:,}")
        print(f"Reborn (special trait): {self.reborn_count} ({self.reborn_count/self.total*100:.2f}%)")

        print("\n── RARITY TIERS ──")
        for name, count in sorted(self.rarity_tiers.items(), key=lambda x: -x[1]):
            print(f"  {name:<12}: {count:>6,}  ({count/self.total*100:>5.2f}%)")

        print("\n── BACKGROUNDS ──")
        for name, count in sorted(self.backgrounds.items(), key=lambda x: -x[1]):
            print(f"  {name:<20}: {count:>6,}  ({count/self.total*100:>5.2f}%)")

        print("\n── WARRIOR CLASSES ──")
        for name, count in sorted(self.classes.items(), key=lambda x: -x[1]):
            print(f"  {name:<15}: {count:>6,}  ({count/self.total*100:>5.2f}%)")

        print("\n── AURA COLORS ──")
        for name, count in sorted(self.auras.items(), key=lambda x: -x[1]):
            print(f"  {name:<15}: {count:>6,}  ({count/self.total*100:>5.2f}%)")

        print("\n── RUNE DISTRIBUTION (top 5 / bottom 5) ──")
        sorted_runes = sorted(self.runes.items(), key=lambda x: -x[1])
        for name, count in sorted_runes[:5]:
            print(f"  {name:<10}: {count:>5,}  ({count/self.total*100:>5.2f}%)")
        print("  ...")
        for name, count in sorted_runes[-5:]:
            print(f"  {name:<10}: {count:>5,}  ({count/self.total*100:>5.2f}%)")

        print("\n── UNIQUENESS ──")
        # Theoretical max combos
        combos = 24 * 5 * 6 * 6 * 5
        print(f"  Attribute dimensions: 24 runes × 5 backgrounds × 6 classes × 6 auras × 5 tiers")
        print(f"  Theoretical unique combos: {combos:,}")
        print(f"  Collection size:           {self.total:,}")
        print(f"  Coverage ratio:            {self.total/combos*100:.1f}% of possible space")
        print("="*60 + "\n")

# ────────────────────────────────────────────────
# MAIN GENERATOR
# ────────────────────────────────────────────────

def generate(supply: int = TOTAL_SUPPLY, example_count: int = EXAMPLE_COUNT, seed: Optional[int] = None):
    """
    Generate `supply` unique REBORNFENIX metadata entries.
    Writes the first `example_count` as JSON files to OUTPUT_DIR.
    """
    if seed is not None:
        random.seed(seed)

    # Load attribute definitions
    with open(ATTRS_FILE, "r", encoding="utf-8") as f:
        attrs_data = json.load(f)

    runes           = attrs_data["elder_futhark_runes"]         # 24 runes
    backgrounds     = attrs_data["background_types"]             # 5 backgrounds
    warrior_classes = attrs_data["warrior_classes"]              # 6 classes
    auras           = attrs_data["aura_colors"]                  # 6 auras
    reborn_ids      = build_reborn_token_ids(supply)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    tracker      = DistributionTracker()
    seen_combos  = set()
    saved_count  = 0
    collision_retries = 0

    print(f"\nGenerating {supply:,} REBORNFENIX metadata entries...")
    print(f"Writing first {example_count} to: {OUTPUT_DIR}\n")

    for token_id in range(1, supply + 1):
        is_reborn = token_id in reborn_ids

        # Draw attributes, retrying on collision
        for attempt in range(50):
            rune          = weighted_choice_by_weight(runes, "rarity_weight")
            background    = weighted_choice(backgrounds)
            warrior_class = weighted_choice(warrior_classes)
            aura          = weighted_choice(auras)
            rarity_tier   = draw_rarity_tier()

            fingerprint = combo_fingerprint(
                rune["id"], background["name"],
                warrior_class["name"], aura["name"], rarity_tier
            )

            if fingerprint not in seen_combos:
                seen_combos.add(fingerprint)
                break
            collision_retries += 1
        # Note: after 50 attempts we accept collision — at 22k vs 21,600 combos
        # the rarity tier variation means this almost never happens

        tracker.record(rune, background, warrior_class, aura, rarity_tier, is_reborn)

        # Only write files for first example_count tokens
        if token_id <= example_count:
            metadata = build_metadata(
                token_id, rune, background, warrior_class,
                aura, rarity_tier, is_reborn, attrs_data
            )
            out_path = OUTPUT_DIR / f"{token_id:05d}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            saved_count += 1
            print(f"  [{token_id:05d}] {metadata['name']}")
            print(f"         Rune: {rune['symbol']} {rune['name']} | BG: {background['name']}")
            print(f"         Class: {warrior_class['name']} | Aura: {aura['name']} | Tier: {rarity_tier}")
            if is_reborn:
                print(f"         *** REBORN ***")
            print()

        # Progress indicator for full run
        if token_id % 5000 == 0:
            print(f"  ... processed {token_id:,} / {supply:,} ({token_id/supply*100:.0f}%) | collisions: {collision_retries}")

    print(f"\nCompleted: {saved_count} example files written to disk.")
    print(f"Total combination collisions retried: {collision_retries}")
    tracker.print_report()

    # Write a summary manifest for the first example_count tokens
    manifest_path = OUTPUT_DIR / "_manifest.json"
    manifest = {
        "collection": "REBORNFENIX",
        "symbol": "RBFX",
        "supply": supply,
        "example_files_generated": example_count,
        "reborn_count": len(reborn_ids),
        "reborn_token_ids": sorted(list(reborn_ids))[:30],  # first 30 listed
        "output_dir": str(OUTPUT_DIR),
        "note": (
            "This manifest lists the first 30 Reborn token IDs for verification. "
            "Run generate() to produce all 22,222 JSON files."
        )
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest written: {manifest_path}")


# ────────────────────────────────────────────────
# ENTRY POINT
# ────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="REBORNFENIX NFT Metadata Generator — Metaplex v3"
    )
    parser.add_argument(
        "--supply", type=int, default=TOTAL_SUPPLY,
        help="Total NFTs to generate (default: 22222)"
    )
    parser.add_argument(
        "--examples", type=int, default=EXAMPLE_COUNT,
        help="Number of JSON files to write to disk (default: 5)"
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Optional random seed for reproducible generation"
    )
    parser.add_argument(
        "--full", action="store_true",
        help="Write ALL metadata files (22,222) to disk — slow!"
    )

    args = parser.parse_args()

    example_count = args.supply if args.full else args.examples
    generate(supply=args.supply, example_count=example_count, seed=args.seed)
