"""
Ingest the contemplative-neuroscience-graph ontology into FalkorDB.

Matches the JSON schema produced in contemplative_neuroscience_ontology.json:
  - nodes: list of {id, type, ...properties}
  - edges: list of {from, to, type, ...properties}, where properties may include
    evidence_strength, confidence, description, and list-valued fields like
    evidenced_by / caveated_by (lists of Citation / Finding node ids).

Usage:
    python ingest_contemplative_graph.py --file contemplative_neuroscience_ontology.json --dry-run
    python ingest_contemplative_graph.py --file contemplative_neuroscience_ontology.json --host localhost --port 6379

Requires: pip install falkordb --break-system-packages
"""

import argparse
import json
import sys


def load_ontology(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def node_label(node_type):
    # FalkorDB/Cypher labels can't contain punctuation; ontology types are already clean.
    return node_type


def build_node_query(node):
    """MERGE on id so re-running ingestion is idempotent (safe to run twice)."""
    label = node_label(node["type"])
    props = {k: v for k, v in node.items() if k not in ("id", "type")}
    query = f"MERGE (n:{label} {{id: $id}}) SET n += $props"
    params = {"id": node["id"], "props": props}
    return query, params


def build_edge_query(edge, all_node_ids):
    """
    MERGE the relationship between two existing nodes, matched by id regardless
    of label, since an edge's from/to types are already implied by the schema.
    List-valued properties (evidenced_by, caveated_by) are stored as-is; FalkorDB
    supports array properties natively, so no flattening is needed.
    """
    from_id, to_id, rel_type = edge["from"], edge["to"], edge["type"]

    missing = [i for i in (from_id, to_id) if i not in all_node_ids]
    if missing:
        return None, None, f"Skipped edge {from_id} -[{rel_type}]-> {to_id}: missing node id(s) {missing}"

    props = {k: v for k, v in edge.items() if k not in ("from", "to", "type")}
    query = (
        f"MATCH (a {{id: $from_id}}), (b {{id: $to_id}}) "
        f"MERGE (a)-[r:{rel_type}]->(b) "
        f"SET r += $props"
    )
    params = {"from_id": from_id, "to_id": to_id, "props": props}
    return query, params, None


def ingest(ontology, host, port, graph_name, dry_run=False):
    node_ids = {n["id"] for n in ontology["nodes"]}
    node_queries = [build_node_query(n) for n in ontology["nodes"]]
    edge_results = [build_edge_query(e, node_ids) for e in ontology["edges"]]

    edge_queries = [(q, p) for q, p, warn in edge_results if q is not None]
    warnings = [warn for _, _, warn in edge_results if warn is not None]

    if dry_run:
        print(f"-- DRY RUN: {len(node_queries)} node upserts, {len(edge_queries)} edge upserts --\n")
        for q, p in node_queries:
            print(q)
            print("  params:", json.dumps(p, ensure_ascii=False))
        print()
        for q, p in edge_queries:
            print(q)
            print("  params:", json.dumps(p, ensure_ascii=False))
        if warnings:
            print("\n-- WARNINGS --")
            for w in warnings:
                print(w)
        return

    from falkordb import FalkorDB

    db = FalkorDB(host=host, port=port)
    graph = db.select_graph(graph_name)

    for q, p in node_queries:
        graph.query(q, p)
    for q, p in edge_queries:
        graph.query(q, p)

    print(f"Ingested {len(node_queries)} nodes and {len(edge_queries)} edges into graph '{graph_name}'.")
    if warnings:
        print(f"{len(warnings)} edge(s) skipped:")
        for w in warnings:
            print(" ", w)


# ---------------------------------------------------------------------------
# Example queries against this ontology once ingested. Run these directly in
# FalkorDB (redis-cli GRAPH.QUERY, or graph.query(...) in Python) to sanity
# check the load and to explore the graph the way the ontology was designed for.
# ---------------------------------------------------------------------------
EXAMPLE_QUERIES = {
    "practices_employing_predictive_suppression": """
        MATCH (p:Practice)-[:EMPLOYS]->(op:CognitiveOperation {id: 'cogop:predictive_model_suppression'})
        RETURN p.name
    """,
    "low_evidence_correlates": """
        MATCH (a)-[r:CORRELATES_WITH]->(b:NeuralSignature)
        WHERE r.evidence_strength IN ['low', 'theoretical_only']
        RETURN a.name, type(r), b.name, r.evidence_strength
    """,
    "orthogonality_claims_with_caveats": """
        MATCH (p1:Practice)-[r:ORTHOGONAL_TO]->(p2:Practice)
        RETURN p1.name, p2.name, r.caveated_by
    """,
    "hwadu_neighbors_and_confidence": """
        MATCH (p:Practice {id: 'prac:hwadu_investigation'})-[r:ANALOGOUS_TO]->(neighbor:Practice)
        RETURN neighbor.name, r.confidence, r.description
    """,
    "citations_by_sample_size": """
        MATCH (c:Citation)
        RETURN c.authors, c.year, c.sample_size, c.study_design
        ORDER BY c.year DESC
    """,
}


def main():
    parser = argparse.ArgumentParser(description="Ingest the contemplative-neuroscience-graph ontology into FalkorDB.")
    parser.add_argument("--file", default="contemplative_neuroscience_ontology.json", help="Path to the ontology JSON file.")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=6379)
    parser.add_argument("--graph", default="contemplative-neuroscience-graph", help="FalkorDB graph name to write into.")
    parser.add_argument("--dry-run", action="store_true", help="Print Cypher instead of executing it.")
    parser.add_argument("--print-example-queries", action="store_true", help="Print example queries to explore the graph after ingestion, then exit.")
    args = parser.parse_args()

    if args.print_example_queries:
        for name, q in EXAMPLE_QUERIES.items():
            print(f"-- {name} --")
            print(q.strip())
            print()
        return

    try:
        ontology = load_ontology(args.file)
    except FileNotFoundError:
        print(f"Could not find {args.file}. Pass --file with the correct path.", file=sys.stderr)
        sys.exit(1)

    ingest(ontology, args.host, args.port, args.graph, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
