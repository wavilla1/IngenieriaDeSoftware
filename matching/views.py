"""
Matching views.

Computes a normalized matching score (0–1) for each job vacancy
relative to a given candidate, and provides skill-level explainability.
"""
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
