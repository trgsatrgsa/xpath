# Maintaining Crystal Data

## Add or fix an upgrade path

**1. Find the crystal IDs**
```bash
python3 -c "import sqlite3; [print(r) for r in sqlite3.connect('items.db').execute(\"SELECT id,name,type FROM items WHERE lower(name) LIKE '%name here%'\")]"
```

**2. Edit `links_fix.json`**

Add upgrade path:
```json
{
  "source_id": 1234,
  "source_name": "Crystal A",
  "target_id": 5678,
  "target_name": "Crystal B",
  "note": "confirmed in-game"
}
```

Fix wrong type (e.g. Coryn Club misclassified it):
```json
{
  "source_id": null,
  "target_id": 5678,
  "target_name": "Crystal B",
  "type_override": "Weapon Crysta",
  "note": "base Weapon Crysta, Coryn Club says Enhancer"
}
```

Not confirmed yet — mark as TODO (will be skipped):
```json
{
  "_todo": true,
  "source_id": null,
  "source_name": "unknown",
  "target_id": 5678,
  "target_name": "Crystal B",
  "note": "TODO: check in-game"
}
```

**3. Regenerate**
```bash
python3 export_crysta.py
```

---

---

## Add a crystal not in Coryn Club / missing from DB

No Python or DB needed. Add a `new_node` entry directly in `links_fix.json`.
Use IDs starting from **9001** (manual range, won't conflict with scrape).

```json
{
  "new_node": true,
  "id": 9003,
  "name": "Zega XI",
  "crysta_type": "Enhancer Crysta (Red)",
  "stats": [
    { "stat": "MaxHP",               "amount": "1400" },
    { "stat": "Magic Resistance %",  "amount": "12"   },
    { "stat": "Water resistance %",  "amount": "11"   },
    { "stat": "Attack MP Recovery",  "amount": "13"   }
  ],
  "note": "manually added"
}
```

Then add its upgrade edge as normal, and regenerate.

## Override stats of an existing crystal

Add `stats` to any edge entry — it replaces the DB stats for that `target_id`:

```json
{
  "source_id": 6779,
  "source_name": "Zega VII",
  "target_id": 9001,
  "target_name": "Zega VIII",
  "stats": [
    { "stat": "MaxHP", "amount": "1100" }
  ],
  "note": "corrected stats"
}
```

---

## Valid `crysta_type` values
- `Weapon Crysta` / `Enhancer Crysta (Red)`
- `Armor Crysta` / `Enhancer Crysta (Green)`
- `Additional Crysta` / `Enhancer Crysta (Yellow)`
- `Special Crysta` / `Enhancer Crysta (Purple)`
- `Normal Crysta` / `Enhancer Crysta (Blue)`
