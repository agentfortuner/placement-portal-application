from flask import request, render_template, redirect, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from application.database import db
from application.models import User, Company, Student, Drive
from app import app


# ---------------- HOME ----------------
@app.route("/home")
def home():
    return render_template("base.html")


# ---------------- REGISTER SELECT ----------------
@app.route("/register")
def register():
    return render_template("register.html")


# ---------------- STUDENT REGISTER ----------------
@app.route("/register-student", methods=["GET","POST"])
def student_register():

    if request.method == "POST":

        name = request.form.get("name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        rollNumber = request.form.get("rollNumber")
        department = request.form.get("department")
        year = request.form.get("yearOfStudy")

        # create user
        user = User(
            name=name,
            username=username,
            email=email,
            password=password,
            type="student"
        )

        db.session.add(user)
        db.session.commit()

        # create student profile
        student = Student(
            userId=user.id,
            rollNumber=rollNumber,
            department=department,
            yearOfStudy=year
        )

        db.session.add(student)
        db.session.commit()

        flash("Student registered successfully", "success")

        return redirect("/login")

    return render_template("studentreg.html")

@app.route("/register-company", methods=["GET", "POST"])
def company_register():
    if request.method == "POST":
        # 1. Collect all data from the form
        new_company = Company(
            name=request.form.get("name"),
            username=request.form.get("username"),
            email=request.form.get("email"),
            password=request.form.get("password"), # Note: Use generate_password_hash in production!
            contactName=request.form.get("contactName"),
            contactEmail=request.form.get("contactEmail"),
            category=request.form.get("category"),
            scale=request.form.get("scale"),
            description=request.form.get("description"),
            placementHistory=request.form.get("placementHistory"),
            website=request.form.get("website"),
            address=request.form.get("address"),
            locations=request.form.get("locations")
        )

        try:
            # 2. Add to database
            db.session.add(new_company)
            db.session.commit()
            flash("Company registered successfully! Please login.", "success")
            return redirect("/login")
        except Exception as e:
            db.session.rollback()
            flash("Error: Username or Email already exists.", "danger")

    return render_template("companyreg.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        pwd = request.form["password"]

        this_user = User.query.filter_by(username=username).first()
        this_company = Company.query.filter_by(username=username).first()

        # ---------- COMPANY LOGIN ----------
        if this_company:

            login_user(this_company)

            if this_company.isBlacklisted == False:

                if this_company.password == pwd:

                    session["company_username"] = this_company.username
                    session["company_id"] = this_company.id

                    flash("Login Successful!", "success")

                    return redirect("/company")

                else:
                    flash("Incorrect Password, Try again!", "danger")

            else:
                flash("Company Blacklisted! Contact Admin.", "danger")

        # ---------- USER LOGIN ----------
        elif this_user:

            login_user(this_user)

            if this_user.isBlacklisted == False:

                if this_user.password == pwd:

                    if this_user.type == "manager":

                        session["manager_username"] = this_user.username
                        session["manager_id"] = this_user.id

                        flash("Login Successful!", "success")

                        return redirect("/manager")

                    else:

                        session["student_username"] = this_user.username
                        session["student_id"] = this_user.id

                        flash("Login Successful!", "success")

                        return redirect("/student")

                else:
                    flash("Incorrect Password, Try again!", "danger")

            else:
                flash("Account Blacklisted! Contact Admin.", "danger")

        else:

            flash("No user found! Please register first.", "danger")

    return render_template("login.html")


# ---------------- MANAGER DASHBOARD ----------------
@app.route("/manager")
@login_required
def manager():

    if current_user.type != "manager":
        return redirect("/login")

    query = request.args.get("query")

    student_results = []
    company_results = []

    if query:

        student_results = User.query.filter(
            (User.name.ilike(f"%{query}%")) |
            (User.username.ilike(f"%{query}%")) |
            (User.email.ilike(f"%{query}%"))
        ).all()

        company_results = Company.query.filter(
            (Company.name.ilike(f"%{query}%")) |
            (Company.scale.ilike(f"%{query}%"))
        ).all()

    students = User.query.filter_by(type="student").count()
    pending = Company.query.filter_by(status="Pending").count()
    drives = Drive.query.count()

    return render_template(
        "manager.html",
        students=students,
        pending=pending,
        drives=drives,
        student_results=student_results,
        company_results=company_results
    )
# ---------------- COMPANY APPROVALS ----------------
@app.route("/manager/companies")
@login_required
def manager_companies():

    if current_user.type != "manager":
        return redirect("/login")

    companies = Company.query.all()

    return render_template("companies.html", companies=companies)


# ---------------- COMPANY DETAILS ----------------
@app.route("/manager/company/<int:id>")
@login_required
def company_details(id):

    company = Company.query.get_or_404(id)

    drives = Drive.query.filter_by(companyId=id).all()

    return render_template(
        "companydetails.html",
        company=company,
        drives=drives
    )

@app.route("/manager/company/approve/<int:id>")
@login_required
def approve_company(id):
    if current_user.type != "manager":
        return redirect("/login")
    company = Company.query.get_or_404(id)
    company.status = "Approved"
    db.session.commit()
    flash("Company approved", "success")
    return redirect("/manager/companies")


@app.route("/manager/company/reject/<int:id>")
@login_required
def reject_company(id):
    if current_user.type != "manager":
        return redirect("/login")
    company = Company.query.get_or_404(id)
    company.status = "Rejected"
    db.session.commit()
    flash("Company rejected", "danger")
    return redirect("/manager/companies")

@app.route("/manager/company/blacklist/<int:id>")
@login_required
def blacklist_company(id):

    if current_user.type != "manager":
        return redirect("/login")

    company = Company.query.get_or_404(id)

    company.isBlacklisted = True

    db.session.commit()

    flash("Company blacklisted", "danger")

    return redirect("/manager/companies")

@app.route("/manager/company/whitelist/<int:id>")
@login_required
def whitelist_company(id):

    if current_user.type != "manager":
        return redirect("/login")

    company = Company.query.get_or_404(id)

    company.isBlacklisted = False

    db.session.commit()

    flash("Company whitelisted", "success")

    return redirect("/manager/companies")

# ---------------- STUDENT LIST ----------------
@app.route("/manager/students")
@login_required
def manager_students():

    students = User.query.filter_by(type="student").all()

    return render_template("students.html", students=students)

@app.route("/manager/student/<int:id>")
@login_required
def student_profile(id):

    if current_user.type != "manager":
        return redirect("/login")

    student = Student.query.filter_by(userId=id).first()
    user = User.query.get(id)

    return render_template(
        "studentprofile.html",
        user=user,
        student=student
    )

@app.route("/manager/student/blacklist/<int:id>")
@login_required
def blacklist_student(id):

    if current_user.type != "manager":
        return redirect("/login")

    student = User.query.get_or_404(id)

    student.isBlacklisted = True
    db.session.commit()

    flash("Student blacklisted", "danger")

    return redirect("/manager/students")

@app.route("/manager/student/whitelist/<int:id>")
@login_required
def whitelist_student(id):

    if current_user.type != "manager":
        return redirect("/login")

    student = User.query.get_or_404(id)

    student.isBlacklisted = False
    db.session.commit()

    flash("Student whitelisted", "success")

    return redirect("/manager/students")

# Drives
@app.route("/manager/drives")
@login_required
def manager_drives():

    if current_user.type != "manager":
        return redirect("/login")

    drives = Drive.query.all()

    return render_template("drives.html", drives=drives)

@app.route("/manager/drive/<int:id>")
@login_required
def view_drive(id):

    if current_user.type != "manager":
        return redirect("/login")

    drive = Drive.query.get_or_404(id)

    return render_template("drivedetails.html", drive=drive)

@app.route("/manager/drive/approve/<int:id>")
@login_required
def approve_drive(id):

    if current_user.type != "manager":
        return redirect("/login")

    drive = Drive.query.get_or_404(id)

    drive.adminStatus = "Approved"

    db.session.commit()

    flash("Drive approved", "success")

    return redirect("/manager/drives")

@app.route("/manager/drive/reject/<int:id>")
@login_required
def reject_drive(id):

    if current_user.type != "manager":
        return redirect("/login")

    drive = Drive.query.get_or_404(id)

    drive.adminStatus = "Rejected"

    db.session.commit()

    flash("Drive rejected", "danger")

    return redirect("/manager/drives")


# ---------------- STUDENT DASHBOARD ----------------
@app.route("/student")
@login_required
def student():

    if current_user.__class__.__name__ != "User":
        return redirect("/login")

    return "Student Dashboard"



# ---------------- COMPANY DASHBOARD ----------------
@app.route("/company")
@login_required
def company():
    return render_template("company.html")

@app.route("/company/createdrives")
@login_required
def createdrives():

    if current_user.__class__.__name__ != "Company":
        return redirect("/login")

    drive = Drive.query.filter_by(adminStatus="Approved").all()

    return render_template("createdrives.html", drive = drive )

# ---------------- LOGOUT ----------------
@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully", "success")

    return redirect("/login")