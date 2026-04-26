#!/usr/bin/env python3
"""
query_entity.py — Search the Knowledge Graph using keyword + semantic search.

Queries follow the OpenClaw Core Ontology v0.3.0 — each entity type uses its
canonical name/description property as defined in the ontology (or the FOAF
vocabulary for foaf:Person).
"""
import argparse
import sys
from pathlib import Path

try:
    from rdflib import ConjunctiveGraph, Namespace, RDF, URIRef
except ImportError:
    print("ERROR: Missing dependency. Install with: pip install rdflib", file=sys.stderr)
    sys.exit(2)

# Full namespace URIs
NS_OPENCLAW = "urn:openclaw:ontology#"
NS_FOAF     = "http://xmlns.com/foaf/0.1/"
NS_RDF      = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
NS_VCARD    = "http://www.w3.org/2006/vcard/ns#"

# Canonical name properties per ontology type
NAME_PROPS = {
    "openclaw:Skill":     "openclaw:hasName",
    "openclaw:Agent":      "openclaw:hasName",
    "openclaw:Workspace":  "openclaw:hasName",
    "openclaw:Tool":       "openclaw:hasName",
    "openclaw:Channel":    "openclaw:hasName",
    "openclaw:Provider":   "openclaw:hasName",
    "openclaw:Concept":    "openclaw:hasName",
    "openclaw:Location":   "openclaw:hasName",
    "openclaw:Plugin":     "openclaw:hasName",
    "openclaw:Gateway":    "openclaw:hasName",
    "foaf:Person":        "foaf:name",
}

# Canonical description properties per ontology type
DESC_PROPS = {
    "openclaw:Skill":     "openclaw:hasDescription",
    "openclaw:Agent":      "openclaw:hasDescription",
    "openclaw:Workspace":  "openclaw:hasDescription",
    "openclaw:Tool":       "openclaw:hasDescription",
    "openclaw:Channel":    "openclaw:hasDescription",
    "openclaw:Concept":    "openclaw:hasDescription",
    "openclaw:Location":   "openclaw:hasDescription",
    "openclaw:Plugin":     "openclaw:hasDescription",
    "openclaw:Gateway":    "openclaw:hasDescription",
    "foaf:Person":        "openclaw:note",
    "openclaw:Provider":   "openclaw:providerName",
}

# Property URIRefs (built once)
P_openclaw_hasName        = URIRef(NS_OPENCLAW + "hasName")
P_openclaw_hasDescription = URIRef(NS_OPENCLAW + "hasDescription")
P_openclaw_note           = URIRef(NS_OPENCLAW + "note")
P_openclaw_providerName   = URIRef(NS_OPENCLAW + "providerName")
P_foaf_name               = URIRef(NS_FOAF + "name")
RDF_type                  = URIRef(NS_RDF + "type")
FOAF_Person               = URIRef(NS_FOAF + "Person")

# Namespace objects for SPARQL-style triple queries
_NS = Namespace(NS_OPENCLAW)


def _ns_prop(local):
    """openclaw:<local> as URIRef."""
    return URIRef(NS_OPENCLAW + local)


def _short_type(uri_ref_str):
    """Convert a full type URI to a 'prefix:local' short form using known namespaces."""
    for prefix, ns in [("openclaw", NS_OPENCLAW), ("foaf", NS_FOAF), ("rdf", NS_RDF)]:
        if ns in uri_ref_str:
            return f"{prefix}:{uri_ref_str.replace(ns, '')}"
    return uri_ref_str


def _get_types(g, subject):
    """Get all RDF types for a subject as short strings."""
    types = []
    for t in g.objects(subject, RDF_type):
        types.append(_short_type(str(t)))
    return types


def _get_name(g, subject, types):
    """Get canonical name following ontology type hierarchy."""
    for t in types:
        if t in NAME_PROPS:
            ns_pref, local = NAME_PROPS[t].split(":")
            if ns_pref == "openclaw":
                prop = _ns_prop(local)
            elif ns_pref == "foaf":
                prop = URIRef(NS_FOAF + local)
            else:
                continue
            name = g.value(subject, prop)
            if name:
                return str(name)
    # Fallback
    name = g.value(subject, P_openclaw_hasName)
    return str(name) if name else None


def _get_description(g, subject, types):
    """Get canonical description following ontology type hierarchy."""
    for t in types:
        if t in DESC_PROPS:
            ns_pref, local = DESC_PROPS[t].split(":")
            if ns_pref == "openclaw":
                prop = _ns_prop(local)
            elif ns_pref == "foaf":
                prop = URIRef(NS_FOAF + local)
            else:
                continue
            desc = g.value(subject, prop)
            if desc:
                return str(desc)
    # Fallback
    desc = g.value(subject, P_openclaw_hasDescription)
    return str(desc) if desc else ""


def get_all_entities(g):
    """
    Return all named entities from the graph.

    Follows the OpenClaw ontology: each type uses its canonical name property
    (openclaw:hasName for OpenClaw types, foaf:name for foaf:Person).
    Skips entity types without a canonical name property (Session, Binding,
    Memory) unless they happen to have an openclaw:hasName triple.
    """
    entities = []
    seen = set()

    # 1. Subjects that have openclaw:hasName
    for s in g.subjects(P_openclaw_hasName, None):
        if s in seen:
            continue
        seen.add(s)
        types = _get_types(g, s)
        name = _get_name(g, s, types)
        desc = _get_description(g, s, types)
        if not name:
            continue
        primary_type = types[0] if types else "unknown"
        entities.append({
            "uri": str(s),
            "type": primary_type,
            "types": types,
            "name": name,
            "description": desc or "",
            "text": f"{name} {desc or ''}".lower(),
        })

    # 2. foaf:Person entities (may not have openclaw:hasName)
    for s in g.subjects(RDF_type, FOAF_Person):
        if s in seen:
            continue
        seen.add(s)
        types = _get_types(g, s)
        name = _get_name(g, s, types)
        desc = _get_description(g, s, types)
        if not name:
            name = str(s).split(":")[-1]
        primary_type = types[0] if types else "foaf:Person"
        entities.append({
            "uri": str(s),
            "type": primary_type,
            "types": types,
            "name": name,
            "description": desc or "",
            "text": f"{name} {desc or ''}".lower(),
        })

    return entities


def keyword_score(query, entity_text):
    query_tokens = set(query.lower().split())
    entity_tokens = set(entity_text.split())
    overlap = len(query_tokens.intersection(entity_tokens))
    return overlap / max(len(query_tokens), 1)


def semantic_search(query, entities):
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        import logging
        logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

        model = SentenceTransformer('all-MiniLM-L6-v2')
        corpus = [e['text'] for e in entities]
        corpus_embeddings = model.encode(corpus)
        query_embedding = model.encode([query])

        scores = cosine_similarity(query_embedding, corpus_embeddings)[0]
        return scores
    except ImportError:
        import difflib
        scores = []
        for e in entities:
            seq = difflib.SequenceMatcher(None, query.lower(), e['text'])
            scores.append(seq.ratio())
        return scores


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path, required=True, help="Path to graph.trig")
    parser.add_argument("--query", type=str, required=True, help="Search query")
    parser.add_argument("--limit", type=int, default=5, help="Number of results")
    args = parser.parse_args()

    if not args.graph.exists():
        print(f"ERROR: Graph file not found: {args.graph}", file=sys.stderr)
        sys.exit(1)

    g = ConjunctiveGraph()
    g.parse(str(args.graph), format="trig")

    entities = get_all_entities(g)
    if not entities:
        print("Graph is empty or contains no named entities.")
        return

    semantic_scores = semantic_search(args.query, entities)

    for i, e in enumerate(entities):
        ks = keyword_score(args.query, e['text'])
        ss = semantic_scores[i]
        e['score'] = (0.4 * ks) + (0.6 * ss)

    entities.sort(key=lambda x: x['score'], reverse=True)

    print(f"Top {args.limit} results for '{args.query}':\n")
    for e in entities[:args.limit]:
        print(f"[{e['type']}] {e['name']} (Score: {e['score']:.3f})")
        print(f"URI:  {e['uri']}")
        print(f"Desc: {e['description']}")
        print("-" * 50)


if __name__ == "__main__":
    main()
