"""
Candidates views.

Handles candidate creation (with one or more skills) and candidate listing.
"""
from django.shortcuts import render, redirect
from matching.service import db


def _require_login(request):
    """Redirect to login if no session user exists."""
    if not request.session.get("user"):
        return redirect("login")
    return None


def create_candidate(request):
    """
    GET  → show the create-candidate form.
    POST → create/update the candidate node and their skills in Neo4j,
           then redirect to the job list.
    """
    login_redirect = _require_login(request)
    if login_redirect:
        return login_redirect

    error = None

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        # Accept a comma-separated list of skills
        skills_raw = request.POST.get("skills", "").strip()
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()]

        if not name:
            error = "El nombre del candidato es requerido."
        elif not skills:
            error = "Al menos una habilidad es requerida."
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
    login_redirect = _require_login(request)
    if login_redirect:
        return login_redirect

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

def edit_candidate(request, name):
    """Edit an existing candidate's skills."""
    login_redirect = _require_login(request)
    if login_redirect:
        return login_redirect

    error = None
    candidate = None

    try:
        result = db.query(
            """
            MATCH (c:Candidato {name: $name})
            OPTIONAL MATCH (c)-[:TIENE_SKILL]->(s:Skill)
            RETURN c.name AS name, collect(s.name) AS skills
            """,
            {"name": name}
        )
        if result:
            candidate = result[0]
    except RuntimeError as exc:
        error = str(exc)

    if request.method == "POST":
        skills_raw = request.POST.get("skills", "").strip()
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()]

        if not skills:
            error = "Al menos una habilidad es requerida."
        else:
            try:
                # Eliminar habilidades anteriores
                db.query(
                    """
                    MATCH (c:Candidato {name: $name})-[r:TIENE_SKILL]->()
                    DELETE r
                    """,
                    {"name": name}
                )
                # Agregar nuevas habilidades
                for skill in skills:
                    db.query(
                        """
                        MERGE (s:Skill {name: $skill})
                        WITH s
                        MATCH (c:Candidato {name: $name})
                        MERGE (c)-[:TIENE_SKILL]->(s)
                        """,
                        {"name": name, "skill": skill},
                    )
                return redirect("candidate_list")
            except RuntimeError as exc:
                error = str(exc)

    return render(request, "edit_candidate.html", 
                  {"candidate": candidate, "error": error})

def delete_candidate(request, name):
    """Delete a candidate."""
    login_redirect = _require_login(request)
    if login_redirect:
        return login_redirect

    try:
        db.query(
            """
            MATCH (c:Candidato {name: $name})
            DETACH DELETE c
            """,
            {"name": name}
        )
    except RuntimeError:
        pass
    return redirect("candidate_list")
