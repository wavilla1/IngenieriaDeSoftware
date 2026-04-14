"""Authentication views."""
from django.shortcuts import render, redirect
from matching.service import db


VALID_ROLES = {"admin", "user"}


def _normalize_role(raw_role):
    role = (raw_role or "user").strip().lower()
    return role if role in VALID_ROLES else "user"


def login(request):
    """Login view."""
    error = None
    
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        selected_role = _normalize_role(request.POST.get("role"))
        
        if not username or not password:
            error = "Usuario y contraseña son requeridos."
        else:
            try:
                result = db.query(
                    """
                    MATCH (u:Postulante {username: $username, password: $password})
                    RETURN u.username AS username, coalesce(u.role, 'user') AS role
                    """,
                    {"username": username, "password": password},
                )
                if result:
                    stored_role = _normalize_role(result[0].get("role"))
                    if stored_role != selected_role:
                        error = "El rol seleccionado no coincide con este usuario."
                        return render(request, "login.html", {"error": error})

                    request.session["user"] = username
                    request.session["role"] = stored_role
                    request.session["is_admin"] = stored_role == "admin"
                    request.session.set_expiry(None)
                    return redirect("candidate_list")
                error = "Usuario o contraseña incorrectos."
            except RuntimeError as exc:
                error = str(exc)
    
    return render(request, "login.html", {"error": error})


def register(request):
    """Register view."""
    error = None
    success = False
    
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()
        role = _normalize_role(request.POST.get("role"))
        
        if not username or not password:
            error = "Usuario y contraseña son requeridos."
        elif len(password) < 4:
            error = "La contraseña debe tener al menos 4 caracteres."
        elif password != confirm_password:
            error = "Las contraseñas no coinciden."
        else:
            try:
                exists = db.query(
                    "MATCH (u:Postulante {username: $username}) RETURN u",
                    {"username": username},
                )
                if exists:
                    error = "Este usuario ya existe."
                else:
                    db.query(
                        """
                        CREATE (u:Postulante {
                          username: $username,
                          password: $password,
                          role: $role
                        })
                        """,
                        {"username": username, "password": password, "role": role},
                    )
                    success = True
                    request.session["user"] = username
                    request.session["role"] = role
                    request.session["is_admin"] = role == "admin"
                    request.session.set_expiry(None)
                    return redirect("candidate_list")
            except RuntimeError as exc:
                error = str(exc)
    
    return render(request, "register.html", {"error": error, "success": success})


def logout(request):
    """Logout view."""
    request.session.flush()
    return redirect("login")


def profile(request):
    """User profile view."""
    user = request.session.get("user")
    if not user:
        return redirect("login")

    role = request.session.get("role", "user")
    applications = []
    error = None

    try:
        applications = db.query(
            """
            MATCH (u:Postulante {username: $username})-[p:POSTULO_A]->(v:Vacante)
            RETURN v.name AS job_name
            ORDER BY job_name
            """,
            {"username": user},
        )
    except RuntimeError as exc:
        error = str(exc)
    
    return render(
        request,
        "profile.html",
        {"username": user, "role": role, "applications": applications, "error": error},
    )
