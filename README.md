# Coryn Club Item Scraper

## Files

| File | Purpose |
|------|---------|
| `download_toram.sh` | Download HTML pages (p=0 to p=43) into `html_pages/` |
| `parse_items.py` | Parse all HTML pages into `items.db` (SQLite) |
| `export_crysta.py` | Export crystal upgrade graph as JSON for xyflow |

## Usage

```bash
# 1. Download pages
bash download_toram.sh

# 2. Parse into DB
pip install beautifulsoup4
python parse_items.py

# 3. Export crystal graph
python export_crysta.py
# -> crysta_graph.json
```

## DB Schema

```
items         (id, name, type, item_url, image_url, sell_amount, sell_unit, process_amount, process_type)
item_stats    (item_id, stat_name, amount)
drop_sources  (item_id, monster_name, monster_level, monster_id, map_name, map_id, dye)
used_for      (item_id, category, target_name, target_id, note)
parse_errors  (page, item_id, item_name, section, error)
```

## Example Queries

```sql
-- All crystal types available
SELECT DISTINCT type FROM items WHERE type LIKE '%Crysta%';

-- All weapon crystas with ATK% buff
SELECT i.name, s.stat_name, s.amount
FROM items i JOIN item_stats s ON i.id = s.item_id
WHERE i.type = 'Weapon Crysta' AND s.stat_name LIKE 'ATK%'
ORDER BY CAST(s.amount AS REAL) DESC;

-- Upgrade path for a specific crystal
SELECT i.name AS "from", uf.target_name AS "upgrades into", uf.category
FROM items i JOIN used_for uf ON i.id = uf.item_id
WHERE i.type LIKE '%Crysta%' AND uf.category = 'Upgrade Into';

-- Where to farm a specific item
SELECT monster_name, monster_level, map_name
FROM drop_sources WHERE item_id = 4352;

-- Items that can be farmed from a specific map
SELECT DISTINCT i.name, i.type
FROM items i JOIN drop_sources d ON i.id = d.item_id
WHERE d.map_name LIKE '%Aulada%';

-- Most versatile crystas (used in most upgrade paths)
SELECT i.name, i.type, COUNT(*) AS upgrade_count
FROM items i JOIN used_for uf ON i.id = uf.item_id
WHERE i.type LIKE '%Crysta%' AND uf.category = 'Upgrade Into'
GROUP BY i.id ORDER BY upgrade_count DESC LIMIT 20;

-- Crystas with negative stats (trade-off builds)
SELECT i.name, s.stat_name, s.amount
FROM items i JOIN item_stats s ON i.id = s.item_id
WHERE i.type LIKE '%Crysta%' AND CAST(s.amount AS REAL) < 0;

-- Check parse errors
SELECT page, item_id, item_name, section, error FROM parse_errors;
```
