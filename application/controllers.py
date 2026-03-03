from flask import request, render_template, redirect, flash, session
from application.database import db
from application.models import User, Company
from app import app


# -------------------- REGISTER --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        if not all([name, email, username, password, role]):
            flash("All fields are required!", "danger")
            return render_template("register.html")

        existing_username = User.query.filter(User.username.ilike(username)).first()
        existing_email = User.query.filter(User.email.ilike(email)).first()

        if existing_username:
            flash("Username already exists!", "danger")
            return render_template("register.html")

        if existing_email:
            flash("Email already exists!", "danger")
            return render_template("register.html")

        new_user = User(
            name=name,
            email=email,
            username=username,
            password=password,
            type=role
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration Successful! Please login.", "success")
        return redirect("/login")

    return render_template("register.html")


# -------------------- LOGIN --------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("All fields are required!", "danger")
            return render_template("login.html")

        user = User.query.filter(User.username.ilike(username)).first()
        company = Company.query.filter(Company.username.ilike(username)).first()

        # ---------- USER LOGIN ----------
        if user:

            if user.isBlacklisted:
                flash("Your account has been blacklisted.", "danger")
                return render_template("login.html")

            if user.password == password:

                session.clear()

                if user.type == "manager":
                    session["manager_id"] = user.id
                    flash("Manager login successful!", "success")
                    return redirect("/manager")
                
                elif user.type == "student":
                    session["student_id"] = user.id
                    flash("Student login successful!", "success")
                    return redirect("/student")
            else:
                flash("Incorrect password!", "danger")
                return render_template("login.html")

        # ---------- COMPANY LOGIN ----------
        elif company:

            if company.isBlacklisted:
                flash("Your account has been blacklisted.", "danger")
                return render_template("login.html")

            if company.password == password:

                session.clear()
                session["company_id"] = company.id

                flash("Company login successful!", "success")
                return redirect("/company")

            else:
                flash("Incorrect password!", "danger")
                return render_template("login.html")

        else:
            flash("Username not found! Please register first.", "danger")
            return redirect("/login")

    return render_template("login.html")


# -------------------- DASHBOARDS --------------------
@app.route("/student")
def student():
    if "student_id" not in session:
        return redirect("/login")
    return "Welcome to the student dashboard!"


@app.route("/manager")
def manager():
    if "manager_id" not in session:
        return redirect("/login")
    return "Welcome to the manager dashboard!"


@app.route("/company")
def company():
    if "company_id" not in session:
        return redirect("/login")
    return "Welcome to the company dashboard!"