"""
Candidates views.

Handles candidate creation (with one or more skills) and candidate listing.
"""
from django.shortcuts import render, redirect
from matching.service import db


def create_candidate(request):
    """
    GET  → show the create-candidate form.
    POST → create/update the candidate node and their skills in Neo4j,
           then redirect to the job list.
    """
    error = None

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        # Accept a comma-separated list of skills
        skills_raw = request.POST.get("skills", "").strip()
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()]

        if not name:
            error = "Candidate name is required."
        elif not skills:
            error = "At least one skill is required."
        else:
            try:
                for skill in skills:
                    db.query(
                        """
                        MERGE (c:Candidato {name: $name})
                        MERGE (s:Skill {name: $skill})
                        MERGE (c)-[:TIENE_SKILL]->(s)
                        """,
                        {"name": name, "skill": skill},
                    )
                return redirect("recommendations", name=name)
            except RuntimeError as exc:
                error = str(exc)

    return render(request, "create_candidate.html", {"error": error})


def candidate_list(request):
    """List all candidates stored in Neo4j."""
    error = None
    candidates = []

    try:
        results = db.query(
            """
            MATCH (c:Candidato)
            OPTIONAL MATCH (c)-[:TIENE_SKILL]->(s:Skill)
            RETURN c.name AS name, collect(s.name) AS skills
            ORDER BY c.name
            """
        )
        candidates = results
    except RuntimeError as exc:
        error = str(exc)

    return render(request, "candidate_list.html", {"candidates": candidates, "error": error})
