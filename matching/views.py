"""
Matching views.

Computes a normalized matching score (0–1) for each job vacancy
relative to a given candidate, and provides skill-level explainability.
"""
import json

from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from matching.service import db


def _require_login(request):
    if not request.session.get("user"):
        return redirect("login")
    return None


def _is_admin(request):
    return bool(request.session.get("is_admin"))


def recommendations(request, name):
    """Show ranked job recommendations for a candidate."""
    login_redirect = _require_login(request)
    if login_redirect:
        return login_redirect
    if not _is_admin(request) and name != request.session.get("user"):
        return HttpResponseForbidden("No tienes permisos para ver estas recomendaciones.")

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
    """Render an in-app graph visualization of candidates, jobs and skills."""
    login_redirect = _require_login(request)
    if login_redirect:
        return login_redirect

    error = None
    nodes = []
    edges = []

    try:
        rows = db.query(
            """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN n, r, m
            LIMIT 400
            """
        )

        node_map = {}
        edge_keys = set()

        def add_node(node):
            if node is None:
                return None

            node_id = str(getattr(node, "element_id", "")) or str(node)
            if node_id in node_map:
                return node_id

            labels = list(getattr(node, "labels", []))
            props = dict(getattr(node, "_properties", {}))
            title = props.get("name") or props.get("title") or node_id

            node_map[node_id] = True
            nodes.append(
                {
                    "id": node_id,
                    "label": title,
                    "group": labels[0] if labels else "Node",
                    "title": f"{', '.join(labels) if labels else 'Node'} | {props}",
                }
            )
            return node_id

        for row in rows:
            source = row.get("n")
            rel = row.get("r")
            target = row.get("m")

            source_id = add_node(source)
            target_id = add_node(target)

            if rel is None or source_id is None or target_id is None:
                continue

            rel_type = str(getattr(rel, "type", "REL"))
            edge_key = (source_id, target_id, rel_type)
            if edge_key in edge_keys:
                continue

            edge_keys.add(edge_key)
            edges.append(
                {
                    "from": source_id,
                    "to": target_id,
                    "label": rel_type,
                    "arrows": "to",
                }
            )

    except RuntimeError as exc:
        error = str(exc)

    return render(
        request,
        "graph_view.html",
        {
            "error": error,
            "has_error": bool(error),
            "nodes_json": json.dumps(nodes),
            "edges_json": json.dumps(edges),
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
    )
