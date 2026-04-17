# Profile Manager — Django + Neo4j MVP

MVP that demonstrates **graph-based job recommendation** using
Django as the web framework and Neo4j as the backend graph database.

---

## Features

| Feature | Description |
|---------|-------------|
| **Candidate creation** | Register candidates with multiple comma-separated skills |
| **Job vacancies** | Browse vacancies with required skills listed |
| **Graph matching** | Normalized score (0–1) based on shared skills |
| **Explainability** | "Recommended because you match Python and SQL" |
| **Apply (mock)** | One-click apply shows a confirmation page |
| **Demo data** | Management command populates Neo4j in one step |
| **Error resilience** | Friendly message when Neo4j is unavailable |

---

## Tech Stack

- **Python 3.10+**
- **Django 4.2**
- **Neo4j 5.x** (graph database)
- **neo4j Python driver**

---

## Project Structure

```
profile_manager_project/
├── manage.py
├── requirements.txt
├── README.md
├── profile_manager/          # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── candidates/               # Candidate registration & listing
│   ├── views.py
│   ├── urls.py
│   └── management/commands/load_demo_data.py
├── jobs/                     # Job vacancies & apply action
│   ├── views.py
│   └── urls.py
├── matching/                 # Neo4j service + recommendation logic
│   ├── service.py            # Singleton Neo4j connection
│   ├── views.py              # Matching + explainability
│   └── urls.py
├── templates/                # HTML templates (extend base.html)
│   ├── base.html
│   ├── create_candidate.html
│   ├── candidate_list.html
│   ├── job_list.html
│   ├── recommendations.html
│   └── apply_confirmation.html
└── static/css/style.css      # Plain CSS styles
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/wavilla1/IngenieriaDeSoftware.git
cd IngenieriaDeSoftware
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running Neo4j

The easiest way is via Docker:

```bash
docker run \
  --name neo4j-demo \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5
```

Neo4j Browser will be available at <http://localhost:7474>.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j Bolt URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `password` | Neo4j password |
| `DJANGO_SECRET_KEY` | insecure demo key | Django secret key |
| `DJANGO_DEBUG` | `True` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost 127.0.0.1` | Allowed hosts (space-separated) |

You can set them in a `.env` file and export before running, or pass them
directly:

```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=password
```

---

## Running Django

```bash
python manage.py runserver
```

Open <http://127.0.0.1:8000/> in your browser.

---

## Loading Demo Data

Populate Neo4j with 2 candidates, 5 skills, and 3 vacancies:

```bash
python manage.py load_demo_data
```

The command is **idempotent** — it uses Cypher `MERGE` statements, so it is
safe to run multiple times without creating duplicates.

### Demo entities created

**Skills:** Python, SQL, JavaScript, Machine Learning, Docker

**Vacancies:**
- Backend Developer → requires Python, SQL, Docker
- Data Scientist → requires Python, SQL, Machine Learning
- Full Stack Developer → requires JavaScript, Python, Docker

**Candidates:**
- Alice → Python, SQL, Machine Learning
- Bob → JavaScript, Python, Docker

---

## Example Cypher Queries

Open Neo4j Browser at <http://localhost:7474> and run:

```cypher
// List all candidates and their skills
MATCH (c:Candidato)-[:TIENE_SKILL]->(s:Skill)
RETURN c.name AS candidate, collect(s.name) AS skills;

// List all vacancies and their required skills
MATCH (v:Vacante)-[:REQUIERE]->(s:Skill)
RETURN v.name AS vacancy, collect(s.name) AS required_skills;

// Find matching jobs for Alice (sorted by match count)
MATCH (c:Candidato {name: 'Alice'})-[:TIENE_SKILL]->(s:Skill)
MATCH (v:Vacante)-[:REQUIERE]->(s)
RETURN v.name AS vacancy, count(s) AS matched_skills
ORDER BY matched_skills DESC;

// Full matching with score and missing skills
MATCH (c:Candidato {name: 'Alice'})
MATCH (v:Vacante)-[:REQUIERE]->(rs:Skill)
OPTIONAL MATCH (c)-[:TIENE_SKILL]->(rs)
WITH v, rs, c,
     CASE WHEN (c)-[:TIENE_SKILL]->(rs) THEN rs.name END AS matched
WITH v,
     collect(rs.name) AS required,
     collect(matched) AS matchedSkills
RETURN v.name AS vacancy,
       required,
       [s IN matchedSkills WHERE s IS NOT NULL] AS matched,
       toFloat(size([s IN matchedSkills WHERE s IS NOT NULL])) / size(required) AS score
ORDER BY score DESC;
```

---

## URL Reference

| URL | View | Description |
|-----|------|-------------|
| `/` | `create_candidate` | Create a new candidate |
| `/candidates/` | `candidate_list` | List all candidates |
| `/jobs/` | `job_list` | Browse vacancies |
| `/jobs/apply/<job_name>/` | `apply` | Mock apply action |
| `/matching/recommendations/<name>/` | `recommendations` | Job recommendations |

---

## License

Academic project — no license.
