"""
Jobs views.

Renders the list of all vacancies with their required skills,
and handles the mock "Apply" action.
"""
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from matching.service import db


def _require_login(request):
    """Redirect to login if no session user exists."""
    if not request.session.get("user"):
        return redirect("login")
    return None


def _is_admin(request):
    return bool(request.session.get("is_admin"))


def job_list(request):
    """Display all job vacancies with required skills."""
    login_redirect = _require_login(request)
    if login_redirect:
        return login_redirect

    error = None
    jobs = []
    applied_jobs = set()
    current_user = request.session.get("user", "")

    try:
        results = db.query(
            """
            MATCH (v:Vacante)
            OPTIONAL MATCH (v)-[:REQUIERE]->(s:Skill)
            RETURN v.name AS name, collect(s.name) AS required_skills
            ORDER BY v.name
            """
        )
        jobs = results

        applied_result = db.query(
            """
            MATCH (u:Postulante {username: $username})-[:POSTULO_A]->(v:Vacante)
            RETURN collect(v.name) AS applied_jobs
            """,
            {"username": current_user},
        )
        if applied_result:
            applied_jobs = set(applied_result[0].get("applied_jobs") or [])
    except RuntimeError as exc:
        error = str(exc)

    return render(
        request,
        "job_list.html",
        {
            "jobs": jobs,
            "error": error,
            "is_admin": _is_admin(request),
            "current_user": current_user,
            "applied_jobs": applied_jobs,
        },
    )


def apply(request, job_name):
    """
    Mock apply action.

    POST → show a confirmation page (no persistence required).
    GET  → redirect back to job list.
    """
    login_redirect = _require_login(request)
    if login_redirect:
        return login_redirect

    candidate_name = request.session.get("user", "").strip()
    error = None

    if request.method == "POST":
        try:
            db.query(
                """
                MATCH (u:Postulante {username: $username})
                MATCH (v:Vacante {name: $job_name})
                MERGE (u)-[p:POSTULO_A]->(v)
                SET p.updated_at = datetime()
                """,
                {"username": candidate_name, "job_name": job_name},
            )
        except RuntimeError as exc:
            error = str(exc)

    return render(
        request,
        "apply_confirmation.html",
        {"job_name": job_name, "candidate_name": candidate_name, "error": error},
    )


def create_job(request):
    """Create a new job vacancy."""
    login_redirect = _require_login(request)
    if login_redirect:
        return login_redirect
    if not _is_admin(request):
        return HttpResponseForbidden("Solo el administrador puede crear vacantes.")

    error = None

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        skills_raw = request.POST.get("skills", "").strip()
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()]

        if not name:
            error = "El nombre de la vacante es requerido."
        elif not skills:
            error = "Al menos una habilidad es requerida."
        else:
            try:
                existing = db.query(
                    "MATCH (v:Vacante {name: $name}) RETURN v",
                    {"name": name},
                )
                if existing:
                    error = "Esta vacante ya existe."
                else:
                    db.query("CREATE (v:Vacante {name: $name})", {"name": name})
                    for skill in skills:
                        db.query(
                            """
                            MERGE (s:Skill {name: $skill})
                            WITH s
                            MATCH (v:Vacante {name: $job_name})
                            MERGE (v)-[:REQUIERE]->(s)
                            """,
                            {"skill": skill, "job_name": name},
                        )
                    return redirect("jobs")
            except RuntimeError as exc:
                error = str(exc)

    return render(request, "create_job.html", {"error": error})


def edit_job(request, name):
    """Edit an existing job vacancy."""
    login_redirect = _require_login(request)
    if login_redirect:
        return login_redirect
    if not _is_admin(request):
        return HttpResponseForbidden("Solo el administrador puede editar vacantes.")

    error = None
    job = None

    try:
        result = db.query(
            """
            MATCH (v:Vacante {name: $name})
            OPTIONAL MATCH (v)-[:REQUIERE]->(s:Skill)
            RETURN v.name AS name, collect(s.name) AS required_skills
            """,
            {"name": name},
        )
        if result:
            job = result[0]
    except RuntimeError as exc:
        error = str(exc)

    if request.method == "POST":
        skills_raw = request.POST.get("skills", "").strip()
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()]

        if not skills:
            error = "Al menos una habilidad es requerida."
        else:
            try:
                db.query(
                    """
                    MATCH (v:Vacante {name: $name})-[r:REQUIERE]->()
                    DELETE r
                    """,
                    {"name": name},
                )
                for skill in skills:
                    db.query(
                        """
                        MERGE (s:Skill {name: $skill})
                        WITH s
                        MATCH (v:Vacante {name: $name})
                        MERGE (v)-[:REQUIERE]->(s)
                        """,
                        {"skill": skill, "name": name},
                    )
                return redirect("jobs")
            except RuntimeError as exc:
                error = str(exc)

    return render(request, "edit_job.html", {"job": job, "error": error})


def delete_job(request, name):
    """Delete a job vacancy."""
    login_redirect = _require_login(request)
    if login_redirect:
        return login_redirect
    if not _is_admin(request):
        return HttpResponseForbidden("Solo el administrador puede eliminar vacantes.")

    try:
        db.query(
            """
            MATCH (v:Vacante {name: $name})
            DETACH DELETE v
            """,
            {"name": name},
        )
    except RuntimeError:
        pass
    return redirect("jobs")
