"""Authentication views."""
from django.shortcuts import render, redirect
from matching.service import db


def login(request):
    """Login view."""
    error = None
    
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        
        if not username or not password:
            error = "Usuario y contraseña son requeridos."
        else:
            try:
                result = db.query(
                    """
                    MATCH (u:Postulante {username: $username, password: $password})
                    RETURN u.username AS username
                    """,
                    {"username": username, "password": password},
                )
                if result:
                    request.session["user"] = username
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
                        "CREATE (u:Postulante {username: $username, password: $password})",
                        {"username": username, "password": password},
                    )
                    success = True
                    request.session["user"] = username
                    return redirect("candidate_list")
            except RuntimeError as exc:
                error = str(exc)
    
    return render(request, "register.html", {"error": error, "success": success})


def logout(request):
    """Logout view."""
    if "user" in request.session:
        del request.session["user"]
    return redirect("create_candidate")


def profile(request):
    """User profile view."""
    user = request.session.get("user")
    if not user:
        return redirect("login")
    
    return render(request, "profile.html", {"username": user})
