# contemplative-neuroscience-graph

A knowledge graph and companion paper mapping contemplative practices (Samatha
Jhana, Vipassana, Dzogchen Rigpa, Sufi Dhikr, Vajrayana Deity Yoga, Korean
Seon, and Jodo Shinshu) to their reported neural signatures, cognitive
mechanisms, and phenomenological states, with explicit evidence-strength
annotation on every claim.

This is a companion project to
[darshana-graph](https://github.com/joyboseroy/darshana-graph) and
[buddhist-philosophy-graph](https://huggingface.co/datasets/joyboseroy/buddhist-philosophy-graph),
sharing the same node-id conventions.

## Why this exists

Meditation neuroscience often groups very different mental training systems
under one label, "mindfulness" or "meditation," which produces conflicting or
irreproducible EEG/fMRI results across studies. This project takes the
opposite approach: every claim in the graph carries a citation, a sample
size, and an `evidence_strength` rating (`high`, `moderate`, `low`, or
`theoretical_only`), so well-supported findings (Samatha Jhana, Vipassana)
are never conflated with provisional, evidence-thin ones (Korean Seon hwadu
investigation, Jodo Shinshu nembutsu recitation).

It also encodes a direct empirical caution: a study that compared six
traditions head-to-head in a single experiment (Young et al., 2021, *Frontiers
in Human Neuroscience*) found no significant EEG power-spectra differences
between meditation styles. That null result is attached as a `Finding` node
via `CAVEATED_BY` edges directly onto the `ORTHOGONAL_TO` claims it
complicates, rather than either being silently dropped or quietly
undermining a real phenomenological distinction.

## Repository layout

```
data/
  contemplative_neuroscience_ontology.json   # the graph: 59 nodes, 42 edges
scripts/
  ingest_contemplative_graph.py               # loads the JSON into FalkorDB
paper/
  Meditation_Taxonomy_IEEE_plain.docx          # companion paper, IEEE-style
```

## Ontology schema

Node types: `Tradition`, `Practice`, `PhenomenologicalState`,
`NeuralSignature`, `NetworkNode`, `CognitiveMechanism`, `CognitiveOperation`,
`Citation`, `Finding`.

Edge types: `PRACTICED_WITHIN`, `PRODUCES`, `CORRELATES_WITH`, `MEDIATED_BY`,
`EXPLAINED_BY`, `EVIDENCED_BY`, `ORTHOGONAL_TO`, `ANALOGOUS_TO`, `EMPLOYS`,
`CAVEATED_BY`, `PART_OF`.

Full property definitions are in the `node_types` / `edge_types` blocks of
the JSON itself.

## Loading the graph

Requires a running [FalkorDB](https://falkordb.com) instance.

```bash
pip install falkordb --break-system-packages
python scripts/ingest_contemplative_graph.py \
  --file data/contemplative_neuroscience_ontology.json \
  --host localhost --port 6379 \
  --graph contemplative-neuroscience-graph
```

Dry-run first if you want to see the Cypher without writing anything:

```bash
python scripts/ingest_contemplative_graph.py --dry-run \
  --file data/contemplative_neuroscience_ontology.json
```

Example queries to explore the graph once loaded:

```bash
python scripts/ingest_contemplative_graph.py --print-example-queries
```

### Verified example

Run against the live graph (FalkorDB, via `redis-cli`):

```
redis-cli -p 6380 GRAPH.QUERY contemplative-neuroscience-graph \
  "MATCH (p:Practice {id: 'prac:hwadu_investigation'})-[r:ANALOGOUS_TO]->(n:Practice) \
   RETURN n.name, r.confidence, r.description"
```

Returns:

```
n.name       | r.confidence | r.description
Vipassana    | low          | provisional placement pending dedicated hwadu-phase
                              EEG study; shares external-tracking DAN engagement
                              but adds unmodeled conflict/doubt component
```

This is the graph doing exactly what it is for: making explicit that hwadu
investigation currently borrows Vipassana's evidence as a low-confidence
placeholder, rather than having its own dedicated findings, so nobody
mistakes the placement for an established result.

## Status and scope

All six traditions now have complete structural coverage: every Practice
node has a PRACTICED_WITHIN edge to its Tradition, a PRODUCES edge to its
PhenomenologicalState, and (except hwadu investigation, where none exists
yet) a CORRELATES_WITH edge to a NeuralSignature with an explicit evidence
strength. Earlier versions of this graph only had this full wiring for the
two most recently added traditions (Korean Seon, Jodo Shinshu); the four
original traditions have since been brought up to the same standard, with
citations added for each new edge.

A much larger scope (Nyingma sub-practices down to tsa-lung and ngondro,
Theravada's full progression, the four Zen styles, Shambhala, Mahamudra) is
documented but deliberately deferred, see `phase_2_deferred_scope` in the
JSON.

Korean Seon and Jodo Shinshu are explicitly marked `low` / `theoretical_only`
evidence strength throughout. Treat those two as hypotheses for future
studies to test, not settled findings.

## Citation

If you use this graph or the accompanying paper, please cite:

Bose, J. "A Taxonomy of Contemplative States: Matching Brain Signals to What
Practitioners Actually Experience." Independent researcher preprint, 2026.

## License

Code: MIT. Data and paper: CC-BY-4.0.
