"""
Management command: load_demo_data

Populates Neo4j with demo candidates, skills, and vacancies.
Uses MERGE statements so the command is safe to run multiple times.

Usage:
    python manage.py load_demo_data
"""
from django.core.management.base import BaseCommand
from matching.service import db


DEMO_CYPHER = """
// ── Skills ──────────────────────────────────────────────────────────
MERGE (:Skill {name: 'Python'})
MERGE (:Skill {name: 'SQL'})
MERGE (:Skill {name: 'JavaScript'})
MERGE (:Skill {name: 'Machine Learning'})
MERGE (:Skill {name: 'Docker'})

// ── Vacancies ────────────────────────────────────────────────────────
MERGE (v1:Vacante {name: 'Backend Developer'})
MERGE (v2:Vacante {name: 'Data Scientist'})
MERGE (v3:Vacante {name: 'Full Stack Developer'})

// ── Vacancy → Skill (REQUIERE) ────────────────────────────────────────
MERGE (v1)-[:REQUIERE]->(:Skill {name: 'Python'})
MERGE (v1)-[:REQUIERE]->(:Skill {name: 'SQL'})
MERGE (v1)-[:REQUIERE]->(:Skill {name: 'Docker'})

MERGE (v2)-[:REQUIERE]->(:Skill {name: 'Python'})
MERGE (v2)-[:REQUIERE]->(:Skill {name: 'SQL'})
MERGE (v2)-[:REQUIERE]->(:Skill {name: 'Machine Learning'})

MERGE (v3)-[:REQUIERE]->(:Skill {name: 'JavaScript'})
MERGE (v3)-[:REQUIERE]->(:Skill {name: 'Python'})
MERGE (v3)-[:REQUIERE]->(:Skill {name: 'Docker'})

// ── Candidates ───────────────────────────────────────────────────────
MERGE (c1:Candidato {name: 'Alice'})
MERGE (c2:Candidato {name: 'Bob'})

// ── Candidate → Skill (TIENE_SKILL) ──────────────────────────────────
MERGE (c1)-[:TIENE_SKILL]->(:Skill {name: 'Python'})
MERGE (c1)-[:TIENE_SKILL]->(:Skill {name: 'SQL'})
MERGE (c1)-[:TIENE_SKILL]->(:Skill {name: 'Machine Learning'})

MERGE (c2)-[:TIENE_SKILL]->(:Skill {name: 'JavaScript'})
MERGE (c2)-[:TIENE_SKILL]->(:Skill {name: 'Python'})
MERGE (c2)-[:TIENE_SKILL]->(:Skill {name: 'Docker'})
"""


class Command(BaseCommand):
    help = "Populate Neo4j with demo data (idempotent — uses MERGE)."

    def handle(self, *args, **options):
        self.stdout.write("Loading demo data into Neo4j …")
        try:
            # Execute each non-empty statement individually for clarity
            statements = [
                s.strip()
                for s in DEMO_CYPHER.split("\n\n")
                if s.strip() and not s.strip().startswith("//")
            ]
            for stmt in statements:
                # Skip pure comment blocks
                lines = [l for l in stmt.splitlines() if not l.startswith("//")]
                cypher = "\n".join(lines).strip()
                if cypher:
                    db.query(cypher)

            self.stdout.write(self.style.SUCCESS("Demo data loaded successfully."))
        except RuntimeError as exc:
            self.stderr.write(self.style.ERROR(f"Failed to load demo data: {exc}"))
