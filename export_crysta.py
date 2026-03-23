#!/usr/bin/env python3
"""
Export crystal upgrade graph from items.db -> crysta_graph.json

Run: python export_crysta.py [options]
  --type            filter to a specific crysta type (default: all crysta types)
  --db              path to sqlite db (default: items.db)
  --out             output json path (default: crysta_graph.json)
  --links-fix       path to manual edge override file (default: links_fix.json)
  --check-orphans   print enhancer crystals with no incoming edge and exit
"""

import json
import sqlite3
import argparse
from pathlib import Path

DB_PATH        = Path("items.db")
OUT_PATH       = Path("crysta_graph.json")
LINKS_FIX_PATH = Path("links_fix.json")

ENHANCER_TYPES = {
    "Enhancer Crysta (Red)",
    "Enhancer Crysta (Green)",
    "Enhancer Crysta (Yellow)",
    "Enhancer Crysta (Purple)",
    "Enhancer Crysta (Blue)",
}


def fetch_crystas(conn, type_filter=None):
    if type_filter:
        return conn.execute(
            "SELECT id, name, type, item_url, image_url, sell_amount, sell_unit, process_amount, process_type "
            "FROM items WHERE type = ?", (type_filter,)
        ).fetchall()
    return conn.execute(
        "SELECT id, name, type, item_url, image_url, sell_amount, sell_unit, process_amount, process_type "
        "FROM items WHERE type LIKE '%Crysta%'"
    ).fetchall()


def fetch_stats(conn, item_ids):
    ph = ",".join("?" * len(item_ids))
    rows = conn.execute(f"SELECT item_id, stat_name, amount FROM item_stats WHERE item_id IN ({ph})", item_ids).fetchall()
    result = {}
    for item_id, stat_name, amount in rows:
        result.setdefault(item_id, []).append({"stat": stat_name, "amount": amount})
    return result


def fetch_drops(conn, item_ids):
    ph = ",".join("?" * len(item_ids))
    rows = conn.execute(
        f"SELECT item_id, monster_name, monster_level, monster_id, map_name, map_id, dye "
        f"FROM drop_sources WHERE item_id IN ({ph})", item_ids
    ).fetchall()
    result = {}
    for item_id, monster_name, monster_level, monster_id, map_name, map_id, dye in rows:
        result.setdefault(item_id, []).append({
            "monster": monster_name, "level": monster_level,
            "monster_id": monster_id, "map": map_name, "map_id": map_id, "dye": dye,
        })
    return result


def fetch_upgrade_edges(conn, item_ids):
    ph = ",".join("?" * len(item_ids))
    return conn.execute(
        f"SELECT item_id, target_id, target_name FROM used_for "
        f"WHERE item_id IN ({ph}) AND category = 'Upgrade Into'", item_ids
    ).fetchall()


def load_links_fix(path: Path):
    """Load manual overrides. Returns (edges, type_overrides, stats_overrides, new_nodes)."""
    if not path.exists():
        return [], {}, {}, []
    entries = json.loads(path.read_text())
    edges, type_overrides, stats_overrides, new_nodes = [], {}, {}, []
    for e in entries:
        skip = e.get("_todo") or e.get("_skip")
        sid  = e.get("source_id")
        tid  = e.get("target_id")
        if e.get("new_node"):
            new_nodes.append(e)
            continue
        if not skip and sid and tid:
            edges.append((int(sid), int(tid), e.get("note", "")))
        if tid and e.get("type_override"):
            type_overrides[int(tid)] = e["type_override"]
        if tid and e.get("stats"):
            stats_overrides[int(tid)] = e["stats"]
    return edges, type_overrides, stats_overrides, new_nodes


def check_orphan_enhancers(conn):
    """Print enhancer crystals that have no base crystal pointing to them."""
    enhancers = conn.execute(
        "SELECT id, name, type FROM items WHERE type LIKE 'Enhancer Crysta%'"
    ).fetchall()

    # find which enhancer ids appear as targets in used_for
    has_parent = set(
        row[0] for row in conn.execute(
            "SELECT target_id FROM used_for WHERE category = 'Upgrade Into'"
        ).fetchall()
    )

    orphans = [(eid, name, etype) for eid, name, etype in enhancers if eid not in has_parent]

    if not orphans:
        print("No orphan enhancers found — all have a base crystal pointing to them.")
        return

    print(f"Found {len(orphans)} enhancer(s) with no incoming upgrade link:\n")
    print(f"{'ID':<8} {'Type':<30} Name")
    print("-" * 70)
    for eid, name, etype in orphans:
        print(f"{eid:<8} {etype:<30} {name}")
    print(f"\nAdd entries to links_fix.json to fix these:")
    print(json.dumps([{
        "source_id": None, "source_name": "base crystal name here",
        "target_id": eid, "target_name": name, "note": "manual fix"
    } for eid, name, _ in orphans[:3]], indent=2))
    print("  ...")


def build_graph(conn, type_filter=None, fix_edges=None, type_overrides=None, stats_overrides=None, new_nodes=None):
    crystas = fetch_crystas(conn, type_filter)
    if not crystas:
        print("No crystas found. Run parse_items.py first.")
        return {"nodes": [], "edges": []}

    item_ids = [r[0] for r in crystas]
    stats_map = fetch_stats(conn, item_ids)
    drops_map = fetch_drops(conn, item_ids)
    upgrade_rows = fetch_upgrade_edges(conn, item_ids)

    # inject manual fix edges as if they came from the DB
    fix_edges = fix_edges or []
    injected = 0
    for src, tgt, note in fix_edges:
        upgrade_rows.append((src, tgt, f"[fix] {note}"))
        injected += 1
    if injected:
        print(f"  Injected {injected} edge(s) from links_fix.json")

    type_overrides  = type_overrides  or {}
    stats_overrides = stats_overrides or {}
    new_nodes       = new_nodes       or []

    # inject new_node entries from links_fix into the working sets (skip if already in DB)
    existing_ids = set(item_ids)
    for n in new_nodes:
        nid = int(n["id"])
        if nid in existing_ids:
            # node already in DB — still apply stats/type overrides from new_node
            if n.get("stats"):       stats_overrides[nid] = n["stats"]
            if n.get("crysta_type"): type_overrides[nid]  = n["crysta_type"]
            continue
        item_ids.append(nid)
        crystas.append((nid, n["name"], n.get("crysta_type",""), None, None, None, None, None, None))
        if n.get("stats"):
            stats_overrides[nid] = n["stats"]
        if n.get("drop_sources"):
            drops_map[nid] = n["drop_sources"]
        if n.get("crysta_type"):
            pass  # handled via crystas tuple above
    if new_nodes:
        print(f"  Injected {len(new_nodes)} new node(s) from links_fix.json")

    id_set = set(item_ids)
    nodes = []
    for item_id, name, item_type, item_url, image_url, sell_amount, sell_unit, process_amount, process_type in crystas:
        item_type = type_overrides.get(item_id, item_type)
        node_stats = stats_overrides[item_id] if item_id in stats_overrides else stats_map.get(item_id, [])
        nodes.append({
            "id": str(item_id),
            "type": "crystaNode",
            "position": {"x": 0, "y": 0},
            "data": {
                "name": name, "crysta_type": item_type,
                "item_url": item_url, "image_url": image_url,
                "sell_amount": sell_amount, "sell_unit": sell_unit,
                "process_amount": process_amount, "process_type": process_type,
                "stats": node_stats,
                "drop_sources": drops_map.get(item_id, []),
            },
        })

    edges = []
    seen = set()
    for source_id, target_id, target_name in upgrade_rows:
        if target_id is None:
            continue
        edge_id = f"e{source_id}-{target_id}"
        if edge_id in seen:
            continue
        seen.add(edge_id)

        if target_id not in id_set:
            id_set.add(target_id)
            stub = conn.execute(
                "SELECT id, name, type, item_url, image_url FROM items WHERE id = ?", (target_id,)
            ).fetchone()
            if stub:
                nodes.append({
                    "id": str(stub[0]), "type": "crystaNode", "position": {"x": 0, "y": 0},
                    "data": {
                        "name": stub[1], "crysta_type": stub[2],
                        "item_url": stub[3], "image_url": stub[4],
                        "stats": stats_map.get(stub[0], []),
                        "drop_sources": drops_map.get(stub[0], []),
                    },
                })
            else:
                nodes.append({
                    "id": str(target_id), "type": "crystaNode", "position": {"x": 0, "y": 0},
                    "data": {"name": str(target_name), "crysta_type": None},
                })

        edges.append({"id": edge_id, "source": str(source_id), "target": str(target_id), "label": "Upgrade Into", "animated": True})

    return {"nodes": nodes, "edges": edges}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type",          default=None,              help="Filter crysta type e.g. 'Weapon Crysta'")
    parser.add_argument("--db",            default=str(DB_PATH))
    parser.add_argument("--out",           default=str(OUT_PATH))
    parser.add_argument("--links-fix",     default=str(LINKS_FIX_PATH))
    parser.add_argument("--check-orphans", action="store_true",       help="Print enhancers with no base crystal and exit")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)

    if args.check_orphans:
        check_orphan_enhancers(conn)
        conn.close()
        return

    fix_edges, type_overrides, stats_overrides, new_nodes = load_links_fix(Path(args.links_fix))
    graph = build_graph(conn, args.type, fix_edges, type_overrides, stats_overrides, new_nodes)
    conn.close()

    out = Path(args.out)
    out.write_text(json.dumps(graph, indent=2, ensure_ascii=False))
    print(f"Exported {len(graph['nodes'])} nodes, {len(graph['edges'])} edges -> {out}")
    if args.type:
        print(f"  Filtered to: {args.type}")


if __name__ == "__main__":
    main()
