# Toram Online — Crysta Upgrade Path Viewer

A browser-based tool to explore crystal upgrade paths from [Coryn Club](https://coryn.club).

Alternatively, you can check at [RaffyDB](https://raffydb.com/)

View page at https://trgsatrgsa.github.io/xpath/

---

## Viewer (`index.html`)

Open with a local server — `fetch()` requires HTTP, not `file://`:

```bash
python3 -m http.server 8080
# then open http://localhost:8080
```

### Navigation

- **Tabs** — filter by crystal slot: Weapon, Armor, Additional, Special, Normal
- **Search box** — filter crystals by name
- **Stat chips** — click one or more stats to show only crystals that have those stats; click again to deselect
- **⊡ Reset View** — return to the initial view for the current tab

### Reading the graph

- Each box is one crystal. Arrows point from a crystal to what it upgrades into.
- **Solid filled** node = base crystal. **Dark with dashed border** = enhancer crystal (same slot, different tier).
- **Faded dotted** node = upgrade target from a different slot type (shown so the arrow doesn't dangle).
- Longest upgrade chains appear first in the layout.
- Node shows: crystal name / abbreviated stats / map where it drops.

### Interacting

- **Hover** a node — tooltip shows full stats, drop sources, and maps.
- **Click** a node — side panel shows full detail: all stats, every drop source, sell/process values, and a link to Coryn Club.
- **Scroll** — pan up/down. **Drag** — pan freely.
- **− / slider / +** (top-right of graph) — zoom out/in.
- **Minimap** (bottom-left) — overview of the full graph. Click anywhere on it to jump to that area.
- Nodes are fixed in place (not draggable) to keep the layout clean.

---

## Planned

- **Event crystal separation** — event-obtained crystals flagged and filterable separately
- **Enhancer path fix** — broken upgrade links between base and enhancer crystals resolved

---

## Developer

### DB schema

```
items         (id, name, type, item_url, image_url, sell_amount, sell_unit, process_amount, process_type)
item_stats    (item_id, stat_name, amount)
drop_sources  (item_id, monster_name, monster_level, monster_id, map_name, map_id, dye)
used_for      (item_id, category, target_name, target_id, note)
parse_errors  (page, item_id, item_name, section, error)
```

### Useful queries

```sql
-- All crystal types in DB
SELECT DISTINCT type FROM items WHERE type LIKE '%Crysta%';

-- Weapon crystas with ATK% buff, sorted highest first
SELECT i.name, s.stat_name, s.amount
FROM items i JOIN item_stats s ON i.id = s.item_id
WHERE i.type = 'Weapon Crysta' AND s.stat_name LIKE 'ATK%'
ORDER BY CAST(s.amount AS REAL) DESC;

-- Full upgrade chain
SELECT i.name AS "from", uf.target_name AS "upgrades into"
FROM items i JOIN used_for uf ON i.id = uf.item_id
WHERE i.type LIKE '%Crysta%' AND uf.category = 'Upgrade Into';

-- Where to farm a specific item (use item id)
SELECT monster_name, monster_level, map_name
FROM drop_sources WHERE item_id = 4352;

-- All crystas with a negative stat (trade-off builds)
SELECT i.name, s.stat_name, s.amount
FROM items i JOIN item_stats s ON i.id = s.item_id
WHERE i.type LIKE '%Crysta%' AND CAST(s.amount AS REAL) < 0;

-- Check parse errors
SELECT page, item_id, item_name, section, error FROM parse_errors;
```
