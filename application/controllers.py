from flask import request, render_template, redirect, flash, session, jsonify, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from application.database import db
from application.models import Application, User, Company, Student, Drive
from app import app
from datetime import datetime
import os

# HOME PAGE
@app.route("/home")
def home():
    return render_template("base.html")


#REGISTER SELECT PAGE
@app.route("/register")
def register():
    return render_template("register.html")


# REGISTER STUDENT PAGE
@app.route("/register-student", methods=["GET","POST"])
def student_register():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        roll = request.form.get("rollNumber")
        dept = request.form.get("department")
        gpa = request.form.get("gpa")
        year = request.form.get("yearOfStudy")

        # ---- REQUIRED FIELD VALIDATION ----
        if not all([name,email,username,password,roll,dept,gpa,year]):
            flash("All fields are required", "danger")
            return redirect("/register-student")

        # ---- GPA VALIDATION ----
        try:
            gpa = float(gpa)
            if gpa < 0 or gpa > 10:
                flash("GPA must be between 0 and 10", "danger")
                return redirect("/register-student")
        except:
            flash("Invalid GPA format", "danger")
            return redirect("/register-student")

        # ---- USERNAME UNIQUE CHECK ----
        if User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
            return redirect("/register-student")

        # ---- EMAIL UNIQUE CHECK ----
        if User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect("/register-student")

        user = User(
            name=name,
            email=email,
            username=username,
            password=password,
            type="student"
        )

        db.session.add(user)
        db.session.commit()

        # resume upload handling
        resume_file = request.files.get("resume")
        filename = None

        if resume_file and resume_file.filename != "":

            allowed = ["pdf","doc","docx"]
            ext = resume_file.filename.split(".")[-1].lower()

            if ext not in allowed:
                flash("Resume must be PDF or DOC/DOCX", "danger")
                return redirect("/register-student")

            filename = f"{user.id}_{resume_file.filename}"

            path = os.path.join("application/static/resumes", filename)
            resume_file.save(path)

        student = Student(
            userId=user.id,
            rollNumber=roll,
            department=dept,
            gpa=gpa,
            yearOfStudy=year,
            resume=filename
        )

        db.session.add(student)
        db.session.commit()

        flash("Registration successful", "success")

        return redirect("/login")

    return render_template("studentreg.html")


@app.route("/resume/<filename>")
def view_resume(filename):

    return send_from_directory(
        "application/static/resumes",
        filename
    )

#REGISTER COMPANY PAGE
@app.route("/register-company", methods=["GET", "POST"])
def company_register():
    if request.method == "POST":
        new_company = Company(
            name=request.form.get("name"),
            username=request.form.get("username"),
            email=request.form.get("email"),
            password=request.form.get("password"),
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
        if not request.form.get("name") or not request.form.get("email"):
                        flash("Company name and email required", "danger")
                        return redirect("/register-company")
                    
        if Company.query.filter_by(username=request.form.get("username")).first():
                        flash("Username already exists", "danger")
                        return redirect("/register-company")
        try:
            db.session.add(new_company)
            db.session.commit()
            flash("Company registered successfully! Please login.", "success")
            return redirect("/login")
        except Exception as e:
            db.session.rollback()
            flash("Error: Username or Email already exists.", "danger")

    return render_template("companyreg.html")


#LOGIN PAGE
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        pwd = request.form["password"]

        if not username or not pwd:
            flash("Username and password required", "danger")
            return redirect("/login")

        this_user = User.query.filter_by(username=username).first()
        this_company = Company.query.filter_by(username=username).first()
         
        # COMPANY LOGIN
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

        #USER LOGIN
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


#MANAGER DASHBOARD

@app.route("/manager")
@login_required
def manager_dashboard():

    # Dashboard counts
    students = Student.query.count()
    companies = Company.query.count()
    drives = Drive.query.count()

    query = request.args.get("query")

    student_results = []
    company_results = []

    if query:
        
        student_results = Student.query.join(User).filter(
            User.name.ilike(f"%{query}%")
        ).all()

        company_results = Company.query.filter(
            Company.name.ilike(f"%{query}%")
        ).all()

    #Upcoming and past drives
    today = datetime.now()

    upcoming_drives = Drive.query.filter(
        Drive.applicationDeadline >= today
    ).all()

    past_drives = Drive.query.filter(
        Drive.applicationDeadline < today
    ).all()

    #DEPT Distribution
    dept_data = db.session.query(
        Student.department,
        func.count(Student.id)
    ).group_by(Student.department).all()

    dept_labels = [d[0] for d in dept_data]
    dept_values = [d[1] for d in dept_data]

    #Company Distribution
    company_data = db.session.query(
        Company.scale,
        func.count(Company.id)
    ).group_by(Company.scale).all()

    company_labels = [c[0] for c in company_data]
    company_values = [c[1] for c in company_data]

    
    # Daily Applications
    application_data = db.session.query(
        func.date(Application.applicationDate),
        func.count(Application.id)
    ).group_by(func.date(Application.applicationDate)).all()

    application_dates = [str(a[0]) for a in application_data]
    application_counts = [a[1] for a in application_data]

    placement_data = db.session.query(Application.status,func.count(Application.id)).filter(Application.status.in_(["Selected","Rejected"])).group_by(Application.status).all()
    placement_labels = [p[0] for p in placement_data]
    placement_values = [p[1] for p in placement_data]

    return render_template(
        "manager.html",
        students=students,
        companies=companies,
        drives=drives,
        student_results=student_results,
        company_results=company_results,
        upcoming_drives=upcoming_drives,
        past_drives=past_drives,

        dept_labels=json.dumps(dept_labels),
        dept_values=json.dumps(dept_values),

        company_labels=json.dumps(company_labels),
        company_values=json.dumps(company_values),

        application_dates=json.dumps(application_dates),
        application_counts=json.dumps(application_counts),
        placement_labels=json.dumps(placement_labels),
        placement_values=json.dumps(placement_values)
    )

#MANAGER DASHBOARD - COMPANY DETAILS
@app.route("/manager/companies")
@login_required
def manager_companies():

    if current_user.type != "manager":
        return redirect("/login")

    companies = Company.query.all()

    return render_template("companies.html", companies=companies)


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

#MANAGER DASHBOARD - STUDENT DETAILS

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
        "studentprofiles.html",
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

# MANAGER DASHBOARD - Drives
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

    drive = Drive.query.get_or_404(id)

    drive.adminStatus = "Approved"

    db.session.commit()

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


@app.route("/manager/drive/pending/<int:id>")
@login_required
def revert_drive_pending(id):

    drive = Drive.query.get_or_404(id)

    drive.adminStatus = "Pending"

    db.session.commit()

    return redirect("/manager/drives")




# STUDENT DASHBOARD
@app.route("/student")
@login_required
def student_dashboard():

    student = Student.query.filter_by(userId=current_user.id).first()

    drives = Drive.query.filter_by(
        adminStatus="Approved",
        hiringStatus="Hiring"
    ).count()

    applications = Application.query.filter_by(
        studentId=student.id
    ).count()

    shortlisted = Application.query.filter_by(
        studentId=student.id,
        status="Shortlisted"
    ).count()

    # -------- Placement History --------
    placements = Application.query.join(Drive).filter(
        Application.studentId == student.id,
        Application.status == "Selected"
    ).all()

    notifications = Application.query.filter(
        Application.studentId == student.id,
        Application.status != "Applied"
    ).all()

    return render_template(
        "student.html",
        drives=drives,
        applications=applications,
        shortlisted=shortlisted,
        placements=placements,
        notifications=notifications
    )
@app.route("/student/drives")
@login_required
def student_drives():

    search = request.args.get("search")

    if search:
        drives = Drive.query.join(Company).filter(
            (Company.name.ilike(f"%{search}%")) |
            (Drive.title.ilike(f"%{search}%")) |
            (Drive.skillsRequired.ilike(f"%{search}%"))
        ).all()
    else:
        drives = Drive.query.all()

    applications = Application.query.filter_by(
        studentId=current_user.student.id
    ).all()

    applied = {}

    for app in applications:
        applied[app.driveId] = app.status

    return render_template(
        "applydrives.html",
        drives=drives,
        applied=applied
    )


@app.route("/student/applications")
@login_required
def student_applications():

    student = Student.query.filter_by(userId=current_user.id).first()

    applications = Application.query.filter_by(
        studentId=student.id
    ).all()

    return render_template(
        "studentapplication.html",
        applications=applications
    )

@app.route("/student/apply/<int:drive_id>")
@login_required
def apply_drive(drive_id):

    student = Student.query.filter_by(userId=current_user.id).first()

    if not student:
        flash("Student profile not found", "danger")
        return redirect("/student")

    drive = Drive.query.get_or_404(drive_id)

    if drive.eligibilityCriteria:

        try:
            dept_list, min_gpa, min_year = drive.eligibilityCriteria.split(";")

            allowed_departments = dept_list.split(",")

            if student.department not in allowed_departments:
                flash("You are not eligible (department mismatch)", "danger")
                return redirect("/student/drives")

            if float(student.gpa) < float(min_gpa):
                flash("You are not eligible (CGPA too low)", "danger")
                return redirect("/student/drives")

            if int(student.yearOfStudy) < int(min_year):
                flash("You are not eligible (year requirement not met)", "danger")
                return redirect("/student/drives")

        except:
            pass

    existing = Application.query.filter_by(
        studentId=student.id,
        driveId=drive_id
    ).first()

    if existing:
        flash("You already applied for this drive", "warning")
        return redirect("/student/drives")

    application = Application(
        studentId=student.id,
        driveId=drive_id,
        applicationDate=datetime.utcnow(),
        gpa=student.gpa,
        department=student.department,
        status="Applied"
    )

    db.session.add(application)
    db.session.commit()

    flash("Application submitted successfully", "success")

    return redirect("/student/drives")


@app.route("/student/revert/<int:drive_id>")
@login_required
def student_revert_application(drive_id):

    student = Student.query.filter_by(userId=current_user.id).first()

    if not student:
        flash("Student profile not found", "danger")
        return redirect("/student")

    application = Application.query.filter_by(
        studentId=student.id,
        driveId=drive_id
    ).first()

    if application:

        if application.status == "Selected":
            flash("Cannot withdraw after selection", "danger")
            return redirect("/student/drives")

        db.session.delete(application)
        db.session.commit()

        flash("Application withdrawn successfully", "info")

    else:
        flash("Application not found", "warning")

    return redirect("/student/drives")

@app.route("/student/profile", methods=["GET", "POST"])
@login_required
def view_student_profile():

    student = Student.query.filter_by(userId=current_user.id).first()

    if request.method == "POST":

        student.department = request.form.get("department")
        student.gpa = request.form.get("gpa")
        student.skills = request.form.get("skills")
        student.yearOfStudy = request.form.get("yearOfStudy")

        resume = request.files.get("resume")

        if resume and resume.filename != "":
            path = os.path.join("application/static/resumes", resume.filename)
            resume.save(path)
            student.resume = resume.filename
        if not student.department or not student.gpa or not student.yearOfStudy:
            flash("All fields are required", "danger")
            return redirect("/student/profile")
        try:
            gpa = float(gpa)
            if gpa < 0 or gpa > 10:
                flash("GPA must be between 0 and 10", "danger")
                return redirect("/student/profile")
        except:
            flash("Invalid GPA format", "danger")
            return redirect("/student/profile")

        db.session.commit()

        flash("Profile updated successfully", "success")

        return redirect("/student/profile")

    return render_template("studentprofile.html", student=student)



#COMPANY DASHBOARD
@app.route("/company")
@login_required
def company_dashboard():

    company = Company.query.get(current_user.id)

    if company.status != "Approved":
        flash("Account not approved by admin", "danger")
        return redirect("/login")

    drives = Drive.query.filter_by(companyId=company.id).count()

    
    applications = Application.query.join(Drive).filter(
        Drive.companyId == company.id
    ).distinct(Application.id).count()


    shortlisted = Application.query.join(Drive).filter(
        Drive.companyId == company.id,
        Application.status == "Shortlisted"
    ).count()

    return render_template(
        "company.html",
        drives=drives,
        applications=applications,
        shortlisted=shortlisted
    )

@app.route("/company/profile")
@login_required
def company_profile():

    company = Company.query.get(current_user.id)

    return render_template(
        "companyprofile.html",
        company=company
    )

@app.route("/company/profile/update", methods=["POST"])
@login_required
def update_company_profile():

    company = Company.query.get(current_user.id)

    company.name = request.form["name"]
    company.category = request.form["category"]
    company.scale = request.form["scale"]
    company.website = request.form["website"]
    company.description = request.form["description"]

    db.session.commit()

    flash("Profile updated successfully", "success")

    return redirect("/company/profile")


@app.route("/company/drives")
@login_required
def company_drives():

    drives = Drive.query.filter_by(
        companyId=current_user.id
    ).all()

    return render_template(
        "companydrives.html",
        drives=drives
    )

@app.route("/company/drive/create", methods=["GET", "POST"])
@login_required
def create_drive():

    if request.method == "POST":

        drive = Drive(
            companyId=current_user.id,
            title=request.form["title"],
            description=request.form["description"],
            eligibilityCriteria=request.form["eligibilityCriteria"],
            salary=request.form["salary"],
            skillsRequired=request.form["skillsRequired"],
            experienceRequired=request.form["experienceRequired"],
            vacancy=request.form["vacancy"],
            location=request.form["location"],
            applicationDeadline=datetime.strptime(
                request.form["applicationDeadline"], "%Y-%m-%d"
            ),
            hiringStatus="Hiring",
            adminStatus="Pending",
            interviewrounds=request.form["interviewrounds"]
        )
        if not drive.title or not drive.salary or not drive.vacancy or not drive.applicationDeadline:
             flash("All fields are required", "danger")
             return redirect("/company/drive/create")
        try:
            vacancy = int(drive.vacancy)
            if vacancy <= 0:
                flash("Vacancy must be positive", "danger")
                return redirect("/company/drive/create")
        except ValueError:
            flash("Invalid vacancy number", "danger")
            return redirect("/company/drive/create")

        db.session.add(drive)
        db.session.commit()

        flash("Placement drive created successfully", "success")

        return redirect("/company/drives")

    return render_template("createdrive.html")

@app.route("/company/drive/<int:id>/close")
@login_required
def close_drive(id):

    drive = Drive.query.get_or_404(id)

    if drive.companyId != current_user.id:
        return redirect("/company/drives")

    drive.hiringStatus = "Closed"

    db.session.commit()

    flash("Drive closed successfully", "warning")

    return redirect("/company/drives")

@app.route("/company/drive/<int:id>/reopen")
@login_required
def reopen_drive(id):

    drive = Drive.query.get_or_404(id)

    if drive.companyId != current_user.id:
        return redirect("/company/drives")

    drive.hiringStatus = "Hiring"

    db.session.commit()

    flash("Drive reopened successfully", "success")

    return redirect("/company/drives")


@app.route("/company/applications")
@login_required
def company_applications():

    applications = Application.query.join(Drive).filter(
        Drive.companyId == current_user.id
    ).all()

    return render_template(
        "applications.html",
        applications=applications
    )

@app.route("/company/application/<int:id>")
@login_required
def view_application(id):

    application = Application.query.get_or_404(id)

    return render_template(
        "applicationreview.html",
        application=application
    )

@app.route("/company/application/<int:id>/shortlist")
@login_required
def shortlist_application(id):

    app_obj = Application.query.get_or_404(id)

    app_obj.status = "Shortlisted"

    db.session.commit()

    return redirect("/company/applications")

@app.route("/company/application/<int:id>/select")
@login_required
def select_application(id):

    app_obj = Application.query.get_or_404(id)

    app_obj.status = "Selected"

    db.session.commit()

    return redirect("/company/applications")

@app.route("/company/application/<int:id>/reject")
@login_required
def reject_application(id):

    app_obj = Application.query.get_or_404(id)

    app_obj.status = "Rejected"

    db.session.commit()

    return redirect("/company/applications")

@app.route("/company/application/<int:id>/applied")
@login_required
def revert_application(id):

    application = Application.query.get_or_404(id)

    application.status = "Applied"

    db.session.commit()

    return redirect("/company/applications")

# LOGOUT PAGE
@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully", "success")

    return redirect("/login")




#API CODE HERE

@app.route("/api/companies", methods=["POST"])
def api_companies():

    username = request.json.get("username")
    password = request.json.get("password")

    manager = User.query.filter_by(
        username=username,
        type="manager"
    ).first()

    # Validate manager credentials
    if not manager or manager.password != password:
        return jsonify({
            "status": "error",
            "message": "Invalid manager credentials"
        }), 401

    companies = Company.query.all()

    company_list = []

    for company in companies:
        company_list.append({
            "id": company.id,
            "name": company.name,
            "email": company.email,
            "category": company.category,
            "scale": company.scale,
            "status": company.status,
            "website": company.website
        })

    return jsonify({
        "status": "success",
        "total_companies": len(company_list),
        "companies": company_list
    })

# API endpoint to get all students (for manager)

@app.route("/api/students", methods=["POST"])
def api_students():

    username = request.json.get("username")
    password = request.json.get("password")

    manager = User.query.filter_by(
        username=username,
        type="manager"
    ).first()

    if not manager or manager.password != password:
        return jsonify({
            "status": "error",
            "message": "Invalid manager credentials"
        }), 401
    
    students = Student.query.join(User).all()

    student_list = []

    for student in students:

        student_list.append({
            "id": student.id,
            "name": student.user.name,
            "email": student.user.email,
            "rollNumber": student.rollNumber,
            "department": student.department,
            "gpa": student.gpa,
            "yearOfStudy": student.yearOfStudy
        })

    return jsonify({
        "status": "success",
        "total_students": len(student_list),
        "students": student_list
    })

# API endpoint to get all drives (for manager)
@app.route("/api/drives", methods=["POST"])
def api_drives():

    username = request.json.get("username")
    password = request.json.get("password")

    manager = User.query.filter_by(
        username=username,
        type="manager"
    ).first()

    if not manager or manager.password != password:
        return jsonify({
            "status": "error",
            "message": "Invalid manager credentials"
        }), 401

    drives = Drive.query.join(Company).all()

    drive_list = []

    for drive in drives:

        drive_list.append({
            "id": drive.id,
            "company": drive.company.name,
            "title": drive.title,
            "salary": drive.salary,
            "skillsRequired": drive.skillsRequired,
            "vacancy": drive.vacancy,
            "location": drive.location,
            "applicationDeadline": drive.applicationDeadline,
            "status": drive.adminStatus,
            "hiringStatus": drive.hiringStatus
        })

    return jsonify({
        "status": "success",
        "total_drives": len(drive_list),
        "drives": drive_list
    })

# API endpoint to get all drives (for manager)
@app.route("/api/applications", methods=["POST"])
def api_applications():

    username = request.json.get("username")
    password = request.json.get("password")

    manager = User.query.filter_by(
        username=username,
        type="manager"
    ).first()

    if not manager or manager.password != password:
        return jsonify({
            "status": "error",
            "message": "Invalid manager credentials"
        }), 401

    applications = Application.query.join(Student).join(User).join(Drive).join(Company).all()

    application_list = []

    for app in applications:

        application_list.append({
            "application_id": app.id,
            "student_name": app.student.user.name,
            "student_email": app.student.user.email,
            "rollNumber": app.student.rollNumber,
            "company": app.drive.company.name,
            "drive_title": app.drive.title,
            "department": app.department,
            "gpa": app.gpa,
            "application_date": app.applicationDate,
            "status": app.status
        })

    return jsonify({
        "status": "success",
        "total_applications": len(application_list),
        "applications": application_list
    })

@app.route("/api/student/applications", methods=["POST"])
def api_student_applications():

    username = request.json.get("username")
    password = request.json.get("password")

    # Find user
    user = User.query.filter_by(username=username, type="student").first()

    if not user or user.password != password:
        return jsonify({
            "status": "error",
            "message": "Invalid credentials"
        }), 401

    # Get student record
    student = Student.query.filter_by(userId=user.id).first()

    if not student:
        return jsonify({
            "status": "error",
            "message": "Student profile not found"
        })

    # Get applications
    applications = Application.query.filter_by(studentId=student.id).all()

    application_list = []

    for app in applications:

        application_list.append({
            "application_id": app.id,
            "company": app.drive.company.name,
            "drive_title": app.drive.title,
            "salary": app.drive.salary,
            "location": app.drive.location,
            "application_date": app.applicationDate,
            "status": app.status
        })

    return jsonify({
        "status": "success",
        "student": user.name,
        "total_applications": len(application_list),
        "applications": application_list
    })
