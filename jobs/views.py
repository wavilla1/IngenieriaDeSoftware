"""
Jobs views.

Renders the list of all vacancies with their required skills,
and handles the mock "Apply" action.
"""
from django.shortcuts import render
from matching.service import db


def job_list(request):
    """Display all job vacancies with required skills."""
    error = None
    jobs = []

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
    except RuntimeError as exc:
        error = str(exc)

    return render(request, "job_list.html", {"jobs": jobs, "error": error})


def apply(request, job_name):
    """
    Mock apply action.

    POST → show a confirmation page (no persistence required).
    GET  → redirect back to job list.
    """
    candidate_name = request.POST.get("candidate_name", "").strip()
    return render(
        request,
        "apply_confirmation.html",
        {"job_name": job_name, "candidate_name": candidate_name},
    )
