import os
import re
from pathlib import Path

def parse_frontmatter(content):
    match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}
    
    yaml_text = match.group(1)
    data = {}
    
    # Very basic parsing
    name_match = re.search(r'^name:\s*(.+)$', yaml_text, re.MULTILINE)
    if name_match:
        data['name'] = name_match.group(1).strip()
    
    desc_match = re.search(r'^description:\s*(?:>|\|)?\n((?:\s+.*\n?)*)', yaml_text, re.MULTILINE)
    if desc_match:
        data['desc'] = re.sub(r'\s+', ' ', desc_match.group(1).strip())
    else:
        # try one liner
        desc_match_single = re.search(r'^description:\s*(.+)$', yaml_text, re.MULTILINE)
        if desc_match_single:
            data['desc'] = desc_match_single.group(1).strip()
            
    return data

def main():
    base_dir = Path(r"\\wsl.localhost\Ubuntu\home\shiyao\.openclaw\workspace\skills")
    
    skills_ttl = []
    
    for skill_name in os.listdir(base_dir):
        skill_dir = base_dir / skill_name
        if not skill_dir.is_dir():
            continue
        skill_md_path = skill_dir / "SKILL.md"
        if skill_md_path.exists():
            content = skill_md_path.read_text(encoding="utf-8")
            meta = parse_frontmatter(content)
            name = meta.get('name', skill_name).strip()
            desc = meta.get('desc', f"The {skill_name} skill.").strip()
            # replace backslashes and double quotes in desc
            desc = desc.replace('"', '\\"').replace('\n', ' ')
            
            slug = name.lower().replace(' ', '-')
            skills_ttl.append(f"""    kg:skill/{slug}
        a openclaw:Skill ;
        openclaw:hasName          "{name}" ;
        openclaw:hasDescription   "{desc}" ;
        openclaw:createdAt        "2026-04-01T00:00:00Z"^^xsd:dateTime .
""")

    trig_content = f"""@prefix owl:       <http://www.w3.org/2002/07/owl#> .
@prefix rdf:       <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:      <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:       <http://www.w3.org/2001/XMLSchema#> .
@prefix openclaw:  <urn:openclaw:ontology#> .
@prefix kg:        <urn:openclaw:kg:> .

# ── Graph: Meta ───────────────────────────────────────────────────────────────
GRAPH <urn:openclaw:graph:meta> {{
    <urn:openclaw:graph:meta>
        openclaw:createdAt  "2026-04-01T00:00:00Z"^^xsd:dateTime ;
        openclaw:updatedAt  "2026-04-01T00:00:00Z"^^xsd:dateTime ;
        owl:versionInfo     "0.1.0" .
}}

# ── Graph: Skills ─────────────────────────────────────────────────────────────
GRAPH <urn:openclaw:graph:skills> {{
{"".join(skills_ttl)}
}}

# ── Graph: Agents ─────────────────────────────────────────────────────────────
GRAPH <urn:openclaw:graph:agents> {{
    kg:agent/claw
        a openclaw:Agent ;
        openclaw:hasName          "Claw" ;
        openclaw:hasDescription   "The primary initialized Agent named Claw." ;
        openclaw:agentId          "claw" ;
        openclaw:isDefaultAgent   true ;
        openclaw:createdAt        "2026-04-01T00:00:00Z"^^xsd:dateTime .
}}

# ── Graph: Tools ──────────────────────────────────────────────────────────────
GRAPH <urn:openclaw:graph:tools> {{
}}

# ── Graph: Memories ───────────────────────────────────────────────────────────
GRAPH <urn:openclaw:graph:memories> {{
}}

# ── Graph: Concepts ───────────────────────────────────────────────────────────
GRAPH <urn:openclaw:graph:concepts> {{
}}
"""
    
    kg_dir = base_dir / "knowledge-graph" / "kg"
    kg_dir.mkdir(parents=True, exist_ok=True)
    snap_dir = kg_dir / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    
    graph_path = kg_dir / "graph.trig"
    graph_path.write_text(trig_content, encoding="utf-8")
    print(f"Created {{graph_path}}")

if __name__ == "__main__":
    main()
