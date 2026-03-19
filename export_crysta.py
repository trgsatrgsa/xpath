#!/usr/bin/env python3
"""
Export crystal upgrade graph from items.db -> crysta_graph.json

Output format is ready for xyflow (React Flow):
  nodes[] - one per crystal, carries all stats + drop sources in data{}
  edges[] - one per "Upgrade Into" relationship

Run: python export_crysta.py [--type "Weapon Crysta"]
  --type  filter to a specific crysta type (default: all crysta types)
  --db    path to sqlite db (default: items.db)
  --out   output json path (default: crysta_graph.json)
"""

import json
import sqlite3
import argparse
from pathlib import Path

DB_PATH = Path("items.db")
OUT_PATH = Path("crysta_graph.json")


def fetch_crystas(conn, type_filter=None):
    if type_filter:
        rows = conn.execute(
            "SELECT id, name, type, item_url, image_url, sell_amount, sell_unit, process_amount, process_type "
            "FROM items WHERE type = ?",
            (type_filter,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, name, type, item_url, image_url, sell_amount, sell_unit, process_amount, process_type "
            "FROM items WHERE type LIKE '%Crysta%'"
        ).fetchall()
    return rows


def fetch_stats(conn, item_ids):
    placeholders = ",".join("?" * len(item_ids))
    rows = conn.execute(
        f"SELECT item_id, stat_name, amount FROM item_stats WHERE item_id IN ({placeholders})",
        item_ids
    ).fetchall()
    result = {}
    for item_id, stat_name, amount in rows:
        result.setdefault(item_id, []).append({"stat": stat_name, "amount": amount})
    return result


def fetch_drops(conn, item_ids):
    placeholders = ",".join("?" * len(item_ids))
    rows = conn.execute(
        f"SELECT item_id, monster_name, monster_level, monster_id, map_name, map_id, dye "
        f"FROM drop_sources WHERE item_id IN ({placeholders})",
        item_ids
    ).fetchall()
    result = {}
    for item_id, monster_name, monster_level, monster_id, map_name, map_id, dye in rows:
        result.setdefault(item_id, []).append({
            "monster": monster_name,
            "level": monster_level,
            "monster_id": monster_id,
            "map": map_name,
            "map_id": map_id,
            "dye": dye,
        })
    return result


def fetch_upgrade_edges(conn, item_ids):
    """Returns edges where source crysta upgrades into target crysta."""
    placeholders = ",".join("?" * len(item_ids))
    rows = conn.execute(
        f"SELECT item_id, target_id, target_name FROM used_for "
        f"WHERE item_id IN ({placeholders}) AND category = 'Upgrade Into'",
        item_ids
    ).fetchall()
    return rows


def build_graph(conn, type_filter=None):
    crystas = fetch_crystas(conn, type_filter)
    if not crystas:
        print("No crystas found. Run parse_items.py first.")
        return {"nodes": [], "edges": []}

    item_ids = [r[0] for r in crystas]
    stats_map = fetch_stats(conn, item_ids)
    drops_map = fetch_drops(conn, item_ids)
    upgrade_rows = fetch_upgrade_edges(conn, item_ids)

    # Build node id set for edge filtering (only include edges within this set)
    id_set = set(item_ids)

    nodes = []
    for item_id, name, item_type, item_url, image_url, sell_amount, sell_unit, process_amount, process_type in crystas:
        nodes.append({
            "id": str(item_id),
            "type": "crystaNode",          # custom node type for xyflow
            "position": {"x": 0, "y": 0},  # layout handled by xyflow/dagre
            "data": {
                "name": name,
                "crysta_type": item_type,
                "item_url": item_url,
                "image_url": image_url,
                "sell_amount": sell_amount,
                "sell_unit": sell_unit,
                "process_amount": process_amount,
                "process_type": process_type,
                "stats": stats_map.get(item_id, []),
                "drop_sources": drops_map.get(item_id, []),
            },
        })

    edges = []
    seen = set()
    for source_id, target_id, target_name in upgrade_rows:
        if target_id is None:
            continue
        # target may not be a crysta in our set — still include it as a node stub
        edge_id = f"e{source_id}-{target_id}"
        if edge_id in seen:
            continue
        seen.add(edge_id)

        # if target not in our fetched set, add a stub node so graph is complete
        if target_id not in id_set:
            id_set.add(target_id)
            # fetch minimal info for the stub
            stub = conn.execute(
                "SELECT id, name, type, item_url, image_url FROM items WHERE id = ?", (target_id,)
            ).fetchone()
            if stub:
                nodes.append({
                    "id": str(stub[0]),
                    "type": "crystaNode",
                    "position": {"x": 0, "y": 0},
                    "data": {
                        "name": stub[1],
                        "crysta_type": stub[2],
                        "item_url": stub[3],
                        "image_url": stub[4],
                        "stats": stats_map.get(stub[0], []),
                        "drop_sources": drops_map.get(stub[0], []),
                    },
                })
            else:
                # unknown item, minimal stub
                nodes.append({
                    "id": str(target_id),
                    "type": "crystaNode",
                    "position": {"x": 0, "y": 0},
                    "data": {"name": target_name, "crysta_type": None},
                })

        edges.append({
            "id": edge_id,
            "source": str(source_id),
            "target": str(target_id),
            "label": "Upgrade Into",
            "animated": True,
        })

    return {"nodes": nodes, "edges": edges}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", default=None, help="Filter crysta type e.g. 'Weapon Crysta'")
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--out", default=str(OUT_PATH))
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    graph = build_graph(conn, args.type)
    conn.close()

    out = Path(args.out)
    out.write_text(json.dumps(graph, indent=2, ensure_ascii=False))

    print(f"Exported {len(graph['nodes'])} nodes, {len(graph['edges'])} edges -> {out}")
    if args.type:
        print(f"  Filtered to: {args.type}")


if __name__ == "__main__":
    main()
