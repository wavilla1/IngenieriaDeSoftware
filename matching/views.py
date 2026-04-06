"""
Matching views.

Computes a normalized matching score (0–1) for each job vacancy
relative to a given candidate, and provides skill-level explainability.
"""
import json
from django.shortcuts import render
from matching.service import db


def recommendations(request, name):
    """Show ranked job recommendations for a candidate."""
    error = None
    recs = []

    try:
        # Fetch all vacancies with their required skills
        vacancies = db.query(
            """
            MATCH (v:Vacante)-[:REQUIERE]->(s:Skill)
            RETURN v.name AS vacante, collect(s.name) AS required_skills
            """
        )

        # Fetch the candidate's skills
        candidate_skills_result = db.query(
            """
            MATCH (c:Candidato {name: $name})-[:TIENE_SKILL]->(s:Skill)
            RETURN collect(s.name) AS skills
            """,
            {"name": name},
        )
        candidate_skills = set(
            candidate_skills_result[0]["skills"] if candidate_skills_result else []
        )

        # Build recommendations with score and explanation
        for v in vacancies:
            required = set(v["required_skills"])
            matched = candidate_skills & required
            missing = required - candidate_skills
            score = round(len(matched) / len(required), 2) if required else 0.0
            # Pre-compute percentage for the CSS width property (0–100)
            score_pct = int(score * 100)

            if matched:
                explanation = (
                    "Recommended because you match: "
                    + ", ".join(sorted(matched))
                )
            else:
                explanation = "No matching skills yet"

            recs.append(
                {
                    "vacante": v["vacante"],
                    "score": score,
                    "score_pct": score_pct,
                    "matched_skills": sorted(matched),
                    "missing_skills": sorted(missing),
                    "explanation": explanation,
                }
            )

        # Sort by score descending
        recs.sort(key=lambda r: r["score"], reverse=True)

    except RuntimeError as exc:
        error = str(exc)

    return render(
        request,
        "recommendations.html",
        {"recs": recs, "candidate_name": name, "error": error},
    )


def graph_view(request):
    """Render an interactive vis.js graph of all candidates, skills and vacancies."""
    error = None
    nodes_json = "[]"
    edges_json = "[]"

    try:
        # Fetch all relationships in the graph
        rows = db.query(
            """
            MATCH (a)-[r]->(b)
            RETURN
                id(a)       AS src_id,
                labels(a)   AS src_labels,
                a.name      AS src_name,
                type(r)     AS rel_type,
                id(b)       AS tgt_id,
                labels(b)   AS tgt_labels,
                b.name      AS tgt_name
            """
        )

        node_map = {}
        edges = []

        _group = {
            "Candidato": "candidate",
            "Vacante":   "vacancy",
            "Skill":     "skill",
        }

        for row in rows:
            for nid, labels, name in [
                (row["src_id"], row["src_labels"], row["src_name"]),
                (row["tgt_id"], row["tgt_labels"], row["tgt_name"]),
            ]:
                if nid not in node_map:
                    label = labels[0] if labels else "Node"
                    node_map[nid] = {
                        "id":    nid,
                        "label": name or str(nid),
                        "group": _group.get(label, "other"),
                        "title": label,
                    }

            edges.append({
                "from":  row["src_id"],
                "to":    row["tgt_id"],
                "label": row["rel_type"],
            })

        nodes_json = json.dumps(list(node_map.values()))
        edges_json = json.dumps(edges)

    except RuntimeError as exc:
        error = str(exc)

    return render(
        request,
        "graph.html",
        {"nodes_json": nodes_json, "edges_json": edges_json, "error": error},
    )
